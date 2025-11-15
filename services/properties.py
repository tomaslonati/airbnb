"""
Servicio para gestionar propiedades.
"""

import asyncio
from typing import Optional, List, Dict, Any
from db import postgres
from utils.logging import get_logger

logger = get_logger(__name__)


class PropertyService:
    """Servicio para crear, actualizar y gestionar propiedades."""

    async def create_property(
        self,
        nombre: str,
        descripcion: str,
        capacidad: int,
        ciudad_id: int,
        anfitrion_id: int,
        tipo_propiedad_id: int,
        imagenes: Optional[List[str]] = None,
        amenities: Optional[List[int]] = None,
        servicios: Optional[List[int]] = None,
        reglas: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """
        Crea una nueva propiedad.
        
        Args:
            nombre: Nombre de la propiedad
            descripcion: Descripción detallada
            capacidad: Cantidad de personas que puede albergar
            ciudad_id: ID de la ciudad
            anfitrion_id: ID del anfitrión
            tipo_propiedad_id: ID del tipo de propiedad
            imagenes: Lista de URLs de imágenes
            amenities: Lista de IDs de amenities
            servicios: Lista de IDs de servicios
            reglas: Lista de IDs de reglas
            
        Returns:
            Resultado de la creación
        """
        try:
            pool = await postgres.get_client()
            
            logger.info(f"Creando propiedad: {nombre}")
            
            # Crear la propiedad
            query = """
                INSERT INTO propiedad (
                    nombre, descripcion, capacidad, 
                    ciudad_id, anfitrion_id, tipo_propiedad_id, imagenes
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id, nombre, descripcion, capacidad, ciudad_id, anfitrion_id, tipo_propiedad_id
            """
            
            result = await pool.fetchrow(
                query,
                nombre,
                descripcion,
                capacidad,
                ciudad_id,
                anfitrion_id,
                tipo_propiedad_id,
                imagenes or []
            )
            
            propiedad_id = result['id']
            logger.info(f"Propiedad creada con ID: {propiedad_id}")
            
            # Agregar amenities
            if amenities:
                await self._add_amenities(pool, propiedad_id, amenities)
            
            # Agregar servicios
            if servicios:
                await self._add_servicios(pool, propiedad_id, servicios)
            
            # Agregar reglas
            if reglas:
                await self._add_reglas(pool, propiedad_id, reglas)
            
            return {
                "success": True,
                "message": f"Propiedad '{nombre}' creada exitosamente",
                "property_id": propiedad_id,
                "property": dict(result)
            }
            
        except Exception as e:
            logger.error(f"Error al crear propiedad: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _add_amenities(self, pool, propiedad_id: int, amenity_ids: List[int]):
        """Agrega amenities a una propiedad."""
        try:
            query = """
                INSERT INTO propiedad_amenity (propiedad_id, amenity_id)
                VALUES ($1, $2)
                ON CONFLICT DO NOTHING
            """
            
            for amenity_id in amenity_ids:
                await pool.execute(query, propiedad_id, amenity_id)
            
            logger.info(f"Agregados {len(amenity_ids)} amenities a propiedad {propiedad_id}")
        except Exception as e:
            logger.error(f"Error al agregar amenities: {e}")

    async def _add_servicios(self, pool, propiedad_id: int, servicio_ids: List[int]):
        """Agrega servicios a una propiedad."""
        try:
            query = """
                INSERT INTO propiedad_servicio (propiedad_id, servicio_id)
                VALUES ($1, $2)
                ON CONFLICT DO NOTHING
            """
            
            for servicio_id in servicio_ids:
                await pool.execute(query, propiedad_id, servicio_id)
            
            logger.info(f"Agregados {len(servicio_ids)} servicios a propiedad {propiedad_id}")
        except Exception as e:
            logger.error(f"Error al agregar servicios: {e}")

    async def _add_reglas(self, pool, propiedad_id: int, regla_ids: List[int]):
        """Agrega reglas a una propiedad."""
        try:
            query = """
                INSERT INTO propiedad_regla (propiedad_id, regla_id)
                VALUES ($1, $2)
                ON CONFLICT DO NOTHING
            """
            
            for regla_id in regla_ids:
                await pool.execute(query, propiedad_id, regla_id)
            
            logger.info(f"Agregadas {len(regla_ids)} reglas a propiedad {propiedad_id}")
        except Exception as e:
            logger.error(f"Error al agregar reglas: {e}")

    async def get_property(self, propiedad_id: int) -> Dict[str, Any]:
        """Obtiene los detalles de una propiedad."""
        try:
            pool = await postgres.get_client()
            
            query = """
                SELECT p.*, c.nombre as ciudad, t.nombre as tipo_propiedad
                FROM propiedad p
                JOIN ciudad c ON p.ciudad_id = c.id
                JOIN tipo_propiedad t ON p.tipo_propiedad_id = t.id
                WHERE p.id = $1
            """
            
            result = await pool.fetchrow(query, propiedad_id)
            
            if not result:
                return {"success": False, "error": "Propiedad no encontrada"}
            
            return {"success": True, "property": dict(result)}
            
        except Exception as e:
            logger.error(f"Error al obtener propiedad: {e}")
            return {"success": False, "error": str(e)}

    async def list_properties_by_city(self, ciudad_id: int) -> Dict[str, Any]:
        """Lista todas las propiedades de una ciudad."""
        try:
            pool = await postgres.get_client()
            
            query = """
                SELECT p.*, c.nombre as ciudad, t.nombre as tipo_propiedad
                FROM propiedad p
                JOIN ciudad c ON p.ciudad_id = c.id
                JOIN tipo_propiedad t ON p.tipo_propiedad_id = t.id
                WHERE p.ciudad_id = $1
                ORDER BY p.nombre
            """
            
            results = await pool.fetch(query, ciudad_id)
            
            return {
                "success": True,
                "total": len(results),
                "properties": [dict(r) for r in results]
            }
            
        except Exception as e:
            logger.error(f"Error al listar propiedades: {e}")
            return {"success": False, "error": str(e)}

    async def list_properties_by_host(self, anfitrion_id: int) -> Dict[str, Any]:
        """Lista todas las propiedades de un anfitrión."""
        try:
            pool = await postgres.get_client()
            
            query = """
                SELECT p.*, c.nombre as ciudad, t.nombre as tipo_propiedad
                FROM propiedad p
                JOIN ciudad c ON p.ciudad_id = c.id
                JOIN tipo_propiedad t ON p.tipo_propiedad_id = t.id
                WHERE p.anfitrion_id = $1
                ORDER BY p.nombre
            """
            
            results = await pool.fetch(query, anfitrion_id)
            
            return {
                "success": True,
                "total": len(results),
                "properties": [dict(r) for r in results]
            }
            
        except Exception as e:
            logger.error(f"Error al listar propiedades del anfitrión: {e}")
            return {"success": False, "error": str(e)}
