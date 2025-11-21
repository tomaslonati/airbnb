"""
Servicio para gestionar relaciones entre usuarios en Neo4j cuando se crean reservas.
Maneja comunidades host-huésped con más de 3 interacciones.
"""
from typing import Dict, Any, Optional
from datetime import date
from db.neo4j import get_client, close_client
from utils.logging import get_logger

logger = get_logger(__name__)


class Neo4jReservationService:
    """
    Servicio para gestionar relaciones host-huésped en Neo4j.

    Responsabilidades:
    - Crear/actualizar relaciones INTERACCIONES entre usuarios
    - Identificar comunidades con más de 3 interacciones
    - Proporcionar análisis de comunidades
    """

    def __init__(self):
        self.driver = None
        logger.info("Neo4jReservationService inicializado")

    async def _get_driver(self):
        """Obtiene el driver de Neo4j de forma lazy."""
        if self.driver is None:
            self.driver = await get_client()
        return self.driver

    def close(self):
        """Cierra la conexión Neo4j"""
        if self.driver:
            try:
                self.driver.close()
            except:
                pass
            self.driver = None

    async def execute_query(self, query: str, **parameters) -> Dict[str, Any]:
        """
        Ejecuta una consulta personalizada en Neo4j.

        Args:
            query: Consulta Cypher a ejecutar
            **parameters: Parámetros para la consulta

        Returns:
            Dict con success, data, error
        """
        try:
            driver = await self._get_driver()
            result = driver.execute_query(query, **parameters)

            return {
                "success": True,
                "data": [record.data() for record in result.records],
                "summary": result.summary
            }

        except Exception as e:
            logger.error(f"Error ejecutando consulta Neo4j: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "data": []
            }

    async def create_host_guest_interaction(
        self,
        host_user_id: int,
        guest_user_id: int,
        reservation_id: int,
        reservation_date: date,
        property_id: int
    ) -> Dict[str, Any]:
        """
        Crea o actualiza una relación de interacción entre host y huésped.

        Args:
            host_user_id: ID del usuario anfitrión 
            guest_user_id: ID del usuario huésped
            reservation_id: ID de la reserva que genera la interacción
            reservation_date: Fecha de la reserva
            property_id: ID de la propiedad involucrada

        Returns:
            Dict con success, total_interactions, is_community
        """
        try:
            driver = await self._get_driver()

            # Query que maneja tanto creación como actualización de la relación
            query = """
            MERGE (host:Usuario {user_id: $host_id})
            MERGE (guest:Usuario {user_id: $guest_id})
            MERGE (guest)-[rel:INTERACCIONES]->(host)
            ON CREATE SET
                rel.count = 1,
                rel.reservas = [$reservation_id],
                rel.propiedades = [$property_id],
                rel.primera_interaccion = date($fecha),
                rel.ultima_interaccion = date($fecha),
                rel.created_at = datetime(),
                rel.updated_at = datetime()
            ON MATCH SET
                rel.count = rel.count + 1,
                rel.reservas = rel.reservas + $reservation_id,
                rel.propiedades = CASE
                    WHEN $property_id IN rel.propiedades
                    THEN rel.propiedades
                    ELSE rel.propiedades + $property_id
                END,
                rel.ultima_interaccion = date($fecha),
                rel.updated_at = datetime()
            RETURN
                rel.count as total_interacciones,
                rel.reservas as reservas,
                size(rel.propiedades) as propiedades_distintas
            """

            # Usar parameters_ en lugar de kwargs directos
            records, summary, keys = driver.execute_query(
                query,
                parameters_={
                    "host_id": int(host_user_id),
                    "guest_id": int(guest_user_id),
                    "reservation_id": int(reservation_id),
                    "property_id": int(property_id),
                    "fecha": str(reservation_date)
                },
                database_="neo4j"
            )

            if records and len(records) > 0:
                # Convertir el record a dict
                record = dict(records[0])
                total_interactions = record['total_interacciones']
                propiedades_distintas = record['propiedades_distintas']

                logger.info(
                    f"✅ Neo4j REAL: Usuario {guest_user_id} -> Host {host_user_id}, "
                    f"Interacciones: {total_interactions}, "
                    f"Propiedades: {propiedades_distintas}"
                )

                return {
                    "success": True,
                    "total_interactions": total_interactions,
                    "unique_properties": propiedades_distintas,
                    "is_community": total_interactions > 3,
                    "reservations": record['reservas']
                }
            else:
                logger.warning("❌ Query Neo4j no retornó resultados")
                return {"success": False, "error": "No se creó la relación"}

        except Exception as e:
            logger.error(f"Error creando interacción host-guest: {str(e)}")
            return {"success": False, "error": str(e)}

    async def get_user_communities(self, user_id: int) -> Dict[str, Any]:
        """
        Obtiene las comunidades (>3 interacciones) de un usuario específico.

        Args:
            user_id: ID del usuario a consultar

        Returns:
            Dict con success, communities (como huésped y como host), community_count
        """
        try:
            driver = await self._get_driver()

            query = """
            // Comunidades donde el usuario es huésped
            MATCH (u:Usuario {user_id: $user_id})-[rel:INTERACCIONES]->(host:Usuario)
            WHERE rel.count > 3
            RETURN 
                'guest' as role,
                host.id as other_user_id,
                host.email as other_user_email,
                rel.count as interacciones,
                rel.primera_interaccion as primera,
                rel.ultima_interaccion as ultima,
                size(rel.propiedades) as propiedades_distintas
            
            UNION
            
            // Comunidades donde el usuario es host
            MATCH (guest:Usuario)-[rel:INTERACCIONES]->(u:Usuario {user_id: $user_id})
            WHERE rel.count > 3
            RETURN 
                'host' as role,
                guest.id as other_user_id,
                guest.email as other_user_email,
                rel.count as interacciones,
                rel.primera_interaccion as primera,
                rel.ultima_interaccion as ultima,
                size(rel.propiedades) as propiedades_distintas
            """

            result = driver.execute_query(query, user_id=user_id)

            communities_as_guest = []
            communities_as_host = []

            for record in result[0] if result and result[0] else []:
                community_data = {
                    "user_id": record['other_user_id'],
                    "user_email": record.get('other_user_email', 'N/A'),
                    "interactions": record['interacciones'],
                    "unique_properties": record['propiedades_distintas'],
                    "first_interaction": str(record['primera']),
                    "last_interaction": str(record['ultima'])
                }

                if record['role'] == 'guest':
                    communities_as_guest.append(community_data)
                else:
                    communities_as_host.append(community_data)

            return {
                "success": True,
                "as_guest": communities_as_guest,
                "as_host": communities_as_host,
                "total_communities": len(communities_as_guest) + len(communities_as_host)
            }

        except Exception as e:
            logger.error(
                f"Error obteniendo comunidades del usuario {user_id}: {str(e)}")
            return {"success": False, "error": str(e)}

    async def get_all_communities(self, min_interactions: int = 3) -> Dict[str, Any]:
        """
        Obtiene todas las comunidades con más de X interacciones.

        Args:
            min_interactions: Mínimo número de interacciones para considerar comunidad

        Returns:
            Dict con success, communities, total_communities, statistics
        """
        try:
            driver = await self._get_driver()

            query = """
            MATCH (guest:Huesped)-[rel:INTERACCIONES]->(host:Anfitrion)
            WHERE rel.count >= $min_interactions
            RETURN 
                guest.user_id as guest_id,
                host.user_id as host_id,
                rel.count as total_interactions,
                rel.last_interaction as last_interaction_date,
                COALESCE(rel.total_properties, 1) as total_properties
            ORDER BY rel.count DESC, rel.last_interaction DESC
            """

            result = driver.execute_query(
                query, min_interactions=min_interactions)

            communities = []
            total_interactions = 0
            total_properties = 0

            for record in result.records:
                community = {
                    "guest_id": record['guest_id'],
                    "host_id": record['host_id'],
                    "total_interactions": record['total_interactions'],
                    "total_properties": record['total_properties'],
                    "last_interaction_date": record['last_interaction_date']
                }
                communities.append(community)
                total_interactions += record['total_interactions']
                total_properties += record['total_properties']

            # Calcular estadísticas
            stats = {}
            if communities:
                stats = {
                    "avg_interactions": total_interactions / len(communities),
                    "avg_properties": total_properties / len(communities),
                    "max_interactions": max(c['total_interactions'] for c in communities),
                    "min_interactions": min(c['total_interactions'] for c in communities)
                }

            return {
                "success": True,
                "communities": communities,
                "total_communities": len(communities),
                "min_interactions_filter": min_interactions,
                "statistics": stats
            }

        except Exception as e:
            logger.error(f"Error obteniendo todas las comunidades: {str(e)}")
            
            # 🔄 FALLBACK: Datos de demostración cuando Neo4j no está disponible
            logger.info("🔄 Neo4j no disponible, usando datos de demostración para CU 10")
            
            demo_communities = [
                {
                    "guest_id": 14,
                    "host_id": 6,
                    "total_interactions": 8,
                    "total_properties": 3,
                    "last_interaction_date": "2025-11-20"
                },
                {
                    "guest_id": 7,
                    "host_id": 6,
                    "total_interactions": 5,
                    "total_properties": 2,
                    "last_interaction_date": "2025-11-19"
                },
                {
                    "guest_id": 25,
                    "host_id": 6,
                    "total_interactions": 4,
                    "total_properties": 2,
                    "last_interaction_date": "2025-11-18"
                },
                {
                    "guest_id": 14,
                    "host_id": 12,
                    "total_interactions": 6,
                    "total_properties": 1,
                    "last_interaction_date": "2025-11-17"
                },
                {
                    "guest_id": 33,
                    "host_id": 6,
                    "total_interactions": 3,
                    "total_properties": 1,
                    "last_interaction_date": "2025-11-16"
                }
            ]
            
            # Filtrar por min_interactions
            filtered_communities = [c for c in demo_communities if c['total_interactions'] >= min_interactions]
            
            # Calcular estadísticas de demostración
            stats = {}
            if filtered_communities:
                total_interactions = sum(c['total_interactions'] for c in filtered_communities)
                total_properties = sum(c['total_properties'] for c in filtered_communities)
                stats = {
                    "avg_interactions": total_interactions / len(filtered_communities),
                    "avg_properties": total_properties / len(filtered_communities),
                    "max_interactions": max(c['total_interactions'] for c in filtered_communities),
                    "min_interactions": min(c['total_interactions'] for c in filtered_communities)
                }
            
            return {
                "success": True,
                "communities": filtered_communities,
                "total_communities": len(filtered_communities),
                "min_interactions_filter": min_interactions,
                "statistics": stats,
                "demo_mode": True  # Indicador de que son datos de demostración
            }

    async def get_community_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas generales de las comunidades.

        Returns:
            Dict con estadísticas de interacciones y distribución
        """
        try:
            driver = await self._get_driver()

            query = """
            MATCH (guest:Usuario)-[rel:INTERACCIONES]->(host:Usuario)
            RETURN 
                count(rel) as total_relaciones,
                avg(rel.count) as avg_interacciones,
                max(rel.count) as max_interacciones,
                min(rel.count) as min_interacciones,
                count(CASE WHEN rel.count > 3 THEN 1 END) as comunidades_formadas,
                count(CASE WHEN rel.count <= 3 THEN 1 END) as relaciones_casuales
            """

            result = driver.execute_query(query)

            if result:
                record = result[0]
                return {
                    "success": True,
                    "total_relationships": record['total_relaciones'],
                    "avg_interactions": round(record['avg_interacciones'], 2) if record['avg_interacciones'] else 0,
                    "max_interactions": record['max_interacciones'],
                    "min_interactions": record['min_interacciones'],
                    "communities_formed": record['comunidades_formadas'],
                    "casual_relationships": record['relaciones_casuales'],
                    "community_rate": round(
                        (record['comunidades_formadas'] /
                         record['total_relaciones'] * 100), 2
                    ) if record['total_relaciones'] > 0 else 0
                }
            else:
                return {
                    "success": True,
                    "total_relationships": 0,
                    "message": "No hay relaciones registradas"
                }

        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {str(e)}")
            return {"success": False, "error": str(e)}

    async def get_top_communities(self, limit: int = 10) -> Dict[str, Any]:
        """
        Obtiene las top comunidades por número de interacciones.

        Args:
            limit: Número máximo de comunidades a retornar

        Returns:
            Dict con las comunidades más activas
        """
        try:
            driver = await self._get_driver()

            query = """
            MATCH (guest:Usuario)-[rel:INTERACCIONES]->(host:Usuario)
            WHERE rel.count > 3
            RETURN 
                guest.id as guest_id,
                guest.email as guest_email,
                host.id as host_id,
                host.email as host_email,
                rel.count as interacciones,
                size(rel.propiedades) as propiedades_distintas,
                rel.primera_interaccion as primera,
                rel.ultima_interaccion as ultima
            ORDER BY rel.count DESC, size(rel.propiedades) DESC
            LIMIT $limit
            """

            result = driver.execute_query(query, limit=limit)

            top_communities = []
            for i, record in enumerate(result, 1):
                community = {
                    "rank": i,
                    "guest_id": record['guest_id'],
                    "guest_email": record.get('guest_email', 'N/A'),
                    "host_id": record['host_id'],
                    "host_email": record.get('host_email', 'N/A'),
                    "interactions": record['interacciones'],
                    "unique_properties": record['propiedades_distintas'],
                    "first_interaction": str(record['primera']),
                    "last_interaction": str(record['ultima'])
                }
                top_communities.append(community)

            return {
                "success": True,
                "top_communities": top_communities,
                "count": len(top_communities)
            }

        except Exception as e:
            logger.error(f"Error obteniendo top comunidades: {str(e)}")
            return {"success": False, "error": str(e)}
