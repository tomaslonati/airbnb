"""
Servicio de búsquedas que utiliza Cassandra y Redis para cacheo.
CU 8: Property search results caching with 5-minute TTL.
"""

import json
from typing import Dict, Any, Optional
from utils.logging import get_logger
from db.redisdb import get_key, set_key, add_to_set, delete_keys_in_set

logger = get_logger(__name__)

# City name to ID mapping
CITY_MAP = {
    "Buenos Aires": 1,
    "buenos aires": 1,
    "Madrid": 2,
    "madrid": 2,
    "Barcelona": 3,
    "barcelona": 3,
    "Córdoba": 4,
    "cordoba": 4,
    "Mendoza": 5,
    "mendoza": 5
}


class SearchService:
    """Servicio para gestionar búsquedas de propiedades con caching Redis."""

    def __init__(self):
        self.cache_ttl = 300  # 5 minutos (CU 8 requirement)

    def _generate_cache_key(self, ciudad: str, capacidad_minima: int = None,
                           precio_maximo: float = None) -> str:
        """
        Genera una clave de cache determinística basada en los parámetros de búsqueda.

        Args:
            ciudad: Nombre de la ciudad
            capacidad_minima: Capacidad mínima de huéspedes
            precio_maximo: Precio máximo por noche

        Returns:
            Cache key string (readable format)
        """
        # Normalizar ciudad: remover espacios, tildes, lowercase
        ciudad_clean = ciudad.lower().strip().replace(" ", "_").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")

        # Construir partes de la clave
        parts = [f"search:{ciudad_clean}"]

        if capacidad_minima:
            parts.append(f"cap_{capacidad_minima}")

        if precio_maximo:
            parts.append(f"price_{int(precio_maximo)}")

        # Unir con : para formar clave legible
        return ":".join(parts)

    def _get_ciudad_id(self, ciudad: str) -> Optional[int]:
        """
        Convierte nombre de ciudad a ciudad_id.

        Args:
            ciudad: Nombre de la ciudad

        Returns:
            ciudad_id o None si no se encuentra
        """
        return CITY_MAP.get(ciudad) or CITY_MAP.get(ciudad.lower())

    async def search_properties(self, ciudad: str, capacidad_minima: int = None,
                                precio_maximo: float = None) -> Dict[str, Any]:
        """
        CU 8: Busca propiedades por ciudad con filtros de capacidad y precio.
        Implementa caching en Redis con TTL de 5 minutos.

        Args:
            ciudad: Ciudad donde buscar (ej: "Buenos Aires")
            capacidad_minima: Capacidad mínima de huéspedes (opcional)
            precio_maximo: Precio máximo por noche (opcional)

        Returns:
            Dict con success, ciudad, properties, count, cached (bool)
        """
        try:
            # Generar cache key
            cache_key = self._generate_cache_key(ciudad, capacidad_minima, precio_maximo)

            # Intentar obtener del cache
            cached_data = await get_key(cache_key)

            if cached_data:
                logger.info(f"[CU8] Cache HIT para búsqueda en {ciudad}",
                           ciudad=ciudad, cache_key=cache_key)
                result = json.loads(cached_data)
                result['cached'] = True
                return result

            # Cache MISS - consultar Supabase
            logger.info(f"[CU8] Cache MISS para búsqueda en {ciudad}",
                       ciudad=ciudad, cache_key=cache_key)

            # Query Supabase (PostgreSQL)
            from db import postgres

            # Obtener ciudad_id primero
            ciudad_id = self._get_ciudad_id(ciudad)

            if not ciudad_id:
                return {
                    "success": False,
                    "error": f"Ciudad '{ciudad}' no encontrada",
                    "cached": False
                }

            pool = await postgres.get_client()

            # Query para obtener propiedades con WiFi
            query = """
                SELECT DISTINCT
                    p.id AS propiedad_id,
                    p.nombre AS propiedad_nombre,
                    p.capacidad AS capacidad_huespedes,
                    p.ciudad_id,
                    c.nombre AS ciudad_nombre,
                    COALESCE(
                        (SELECT AVG(price_per_night)
                         FROM propiedad_disponibilidad pd
                         WHERE pd.propiedad_id = p.id
                         AND pd.disponible = TRUE
                         AND pd.price_per_night IS NOT NULL),
                        0
                    ) AS precio_noche,
                    TRUE AS wifi
                FROM propiedad p
                INNER JOIN ciudad c ON p.ciudad_id = c.id
                INNER JOIN propiedad_servicio ps ON p.id = ps.propiedad_id
                INNER JOIN servicios s ON ps.servicio_id = s.id
                WHERE
                    p.ciudad_id = $1
                    AND p.capacidad >= $2
                    AND (LOWER(s.descripcion) LIKE '%wifi%' OR LOWER(s.descripcion) LIKE '%internet%')
            """

            params = [ciudad_id, capacidad_minima or 1]

            # Agregar filtro de precio si se especifica
            if precio_maximo:
                query += """
                    AND (
                        SELECT AVG(price_per_night)
                        FROM propiedad_disponibilidad pd
                        WHERE pd.propiedad_id = p.id
                        AND pd.disponible = TRUE
                        AND pd.price_per_night IS NOT NULL
                    ) <= $3
                """
                params.append(precio_maximo)

            # Ejecutar query
            rows = await pool.fetch(query, *params)

            # Convertir resultados a lista de diccionarios y convertir Decimals a float
            from decimal import Decimal
            propiedades = []
            for row in rows:
                prop_dict = dict(row)
                # Convertir Decimal a float para serialización JSON
                for key, value in prop_dict.items():
                    if isinstance(value, Decimal):
                        prop_dict[key] = float(value)
                propiedades.append(prop_dict)

            # Preparar resultado
            result = {
                "success": True,
                "ciudad": ciudad,
                "capacidad_minima": capacidad_minima,
                "precio_maximo": precio_maximo,
                "properties": propiedades,
                "count": len(propiedades),
                "cached": False
            }

            # Guardar en cache con TTL de 5 minutos
            await set_key(cache_key, json.dumps(result), expire=self.cache_ttl)

            # Trackear la clave para poder invalidarla después
            tracking_key = f"search_keys:ciudad:{ciudad_id}"
            await add_to_set(tracking_key, cache_key)

            logger.info(f"[CU8] Resultados guardados en cache para {ciudad}",
                       ciudad=ciudad, count=len(propiedades),
                       ttl=self.cache_ttl, cache_key=cache_key)

            return result

        except Exception as e:
            logger.error(f"[CU8] Error en búsqueda: {e}", ciudad=ciudad)
            return {
                "success": False,
                "error": f"Error en búsqueda: {str(e)}",
                "cached": False
            }

    async def clear_cache(self, ciudad: str = None):
        """
        Limpia el cache de búsquedas.

        Args:
            ciudad: Ciudad específica a limpiar, o None para todas
        """
        try:
            if ciudad:
                # Limpiar cache de una ciudad específica
                ciudad_id = self._get_ciudad_id(ciudad)

                if ciudad_id:
                    tracking_key = f"search_keys:ciudad:{ciudad_id}"
                    deleted_count = await delete_keys_in_set(tracking_key)
                    logger.info(f"[CU8] Cache limpiado para ciudad {ciudad}",
                               deleted_keys=deleted_count)
                else:
                    logger.warning(f"[CU8] Ciudad '{ciudad}' no encontrada para limpiar cache")
            else:
                # Limpiar cache de todas las ciudades
                total_deleted = 0
                for ciudad_id in CITY_MAP.values():
                    tracking_key = f"search_keys:ciudad:{ciudad_id}"
                    deleted_count = await delete_keys_in_set(tracking_key)
                    total_deleted += deleted_count

                logger.info("[CU8] Cache limpiado para todas las ciudades",
                           deleted_keys=total_deleted)

        except Exception as e:
            logger.error(f"[CU8] Error limpiando cache: {e}")


async def invalidate_search_cache_for_city(ciudad_id: int):
    """
    Helper function para invalidar cache cuando cambian reservas.
    Se llama desde create_reservation() y cancel_reservation().

    Args:
        ciudad_id: ID de la ciudad a invalidar
    """
    try:
        tracking_key = f"search_keys:ciudad:{ciudad_id}"
        deleted_count = await delete_keys_in_set(tracking_key)
        logger.info(f"[CU8] Cache invalidado para ciudad_id {ciudad_id}",
                   deleted_keys=deleted_count)
    except Exception as e:
        logger.error(f"[CU8] Error invalidando cache: {e}")
