"""
Servicio para gestionar nodos de usuario en Neo4j.
Sigue principios SOLID y se integra con el sistema de autenticación.
"""

from typing import Optional, Dict
from db.neo4j import get_client
from utils.logging import get_logger

logger = get_logger(__name__)


class Neo4jUserService:
    """
    Servicio para gestionar nodos de usuario en Neo4j.

    Responsabilidades:
    - Crear nodos de usuario en Neo4j
    - Actualizar roles de usuario
    - Mantener sincronización con PostgreSQL
    """

    def __init__(self):
        logger.info("Neo4jUserService inicializado")

    async def create_user_node(self, user_id: int, rol: str) -> bool:
        """
        Crea un nodo de usuario en Neo4j.

        Args:
            user_id: ID del usuario en PostgreSQL
            rol: Rol del usuario (HUESPED, ANFITRION, AMBOS)

        Returns:
            True si se creó exitosamente, False en caso contrario
        """
        try:
            logger.info(
                f"Creando nodo de usuario en Neo4j: ID={user_id}, rol={rol}")

            client = await get_client()

            # Crear nodo Usuario con las propiedades especificadas
            query = """
            CREATE (u:Usuario {id: $user_id, rol: $rol})
            RETURN u
            """

            result = client.execute_query(
                query,
                user_id=user_id,
                rol=rol
            )

            if result and len(result.records) > 0:
                logger.info(
                    f"Nodo de usuario creado exitosamente en Neo4j: ID={user_id}")
                return True
            else:
                logger.warning(
                    f"No se pudo crear el nodo de usuario en Neo4j: ID={user_id}")
                return False

        except Exception as e:
            logger.error(f"Error creando nodo de usuario en Neo4j: {str(e)}")
            return False

    async def update_user_role(self, user_id: int, new_role: str) -> bool:
        """
        Actualiza el rol de un usuario existente en Neo4j.

        Args:
            user_id: ID del usuario en PostgreSQL
            new_role: Nuevo rol del usuario

        Returns:
            True si se actualizó exitosamente, False en caso contrario
        """
        try:
            logger.info(
                f"Actualizando rol de usuario en Neo4j: ID={user_id}, nuevo_rol={new_role}")

            client = await get_client()

            # Actualizar rol del usuario existente
            query = """
            MATCH (u:Usuario {id: $user_id})
            SET u.rol = $new_role
            RETURN u
            """

            result = client.execute_query(
                query,
                user_id=user_id,
                new_role=new_role
            )

            if result and len(result.records) > 0:
                logger.info(
                    f"Rol de usuario actualizado exitosamente en Neo4j: ID={user_id}")
                return True
            else:
                logger.warning(
                    f"No se encontró el usuario para actualizar en Neo4j: ID={user_id}")
                return False

        except Exception as e:
            logger.error(
                f"Error actualizando rol de usuario en Neo4j: {str(e)}")
            return False

    async def get_user_node(self, user_id: int) -> Optional[Dict]:
        """
        Obtiene un nodo de usuario de Neo4j.

        Args:
            user_id: ID del usuario en PostgreSQL

        Returns:
            Diccionario con los datos del nodo o None si no existe
        """
        try:
            client = await get_client()

            query = """
            MATCH (u:Usuario {id: $user_id})
            RETURN u.id as id, u.rol as rol
            """

            result = client.execute_query(query, user_id=user_id)

            if result and len(result.records) > 0:
                record = result.records[0]
                return {
                    "id": record["id"],
                    "rol": record["rol"]
                }

            return None

        except Exception as e:
            logger.error(
                f"Error obteniendo nodo de usuario de Neo4j: {str(e)}")
            return None

    async def user_node_exists(self, user_id: int) -> bool:
        """
        Verifica si existe un nodo de usuario en Neo4j.

        Args:
            user_id: ID del usuario en PostgreSQL

        Returns:
            True si existe, False en caso contrario
        """
        try:
            node = await self.get_user_node(user_id)
            return node is not None
        except Exception as e:
            logger.error(
                f"Error verificando existencia de nodo de usuario: {str(e)}")
            return False

    async def ensure_user_node_sync(self, user_id: int, rol: str) -> bool:
        """
        Asegura que el nodo de usuario esté sincronizado con PostgreSQL.
        Crea el nodo si no existe, o actualiza el rol si es diferente.

        Args:
            user_id: ID del usuario en PostgreSQL
            rol: Rol actual del usuario

        Returns:
            True si el nodo está sincronizado, False en caso contrario
        """
        try:
            existing_node = await self.get_user_node(user_id)

            if existing_node is None:
                # El nodo no existe, crearlo
                return await self.create_user_node(user_id, rol)
            elif existing_node["rol"] != rol:
                # El nodo existe pero el rol es diferente, actualizarlo
                return await self.update_user_role(user_id, rol)
            else:
                # El nodo existe y el rol es correcto
                logger.info(
                    f"Nodo de usuario ya está sincronizado: ID={user_id}")
                return True

        except Exception as e:
            logger.error(f"Error sincronizando nodo de usuario: {str(e)}")
            return False

    async def close(self):
        """
        Cierra las conexiones del servicio.
        Por ahora no necesitamos cerrar nada específico ya que 
        Neo4j se maneja a través del cliente global.
        """
        logger.info("Neo4jUserService cerrado")
        pass
