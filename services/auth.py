"""
Servicio de autenticación para el sistema Airbnb.
Integra Supabase Auth con las tablas del modelo de negocio.
Sigue principios SOLID.
"""

import asyncio
import json
import os
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

from db.postgres import execute_query, execute_command
from services.neo4j_user import Neo4jUserService
from services.mongo_host import MongoHostService
from utils.logging import get_logger

logger = get_logger(__name__)

# Import SessionManager (will be defined after UserProfile)
# from services.session import session_manager


@dataclass
class UserProfile:
    """Modelo de perfil de usuario."""
    id: int
    email: str
    rol: str
    auth_user_id: Optional[str]
    creado_en: datetime
    huesped_id: Optional[int] = None
    anfitrion_id: Optional[int] = None
    nombre: Optional[str] = None


@dataclass
class AuthResult:
    """Resultado de operación de autenticación."""
    success: bool
    message: str
    user_profile: Optional[UserProfile] = None
    session_token: Optional[str] = None
    error: Optional[str] = None


class AuthService:
    """
    Servicio de autenticación siguiendo principios SOLID.

    Responsabilidades:
    - Autenticación de usuarios
    - Registro de nuevos usuarios
    - Gestión de sesiones
    - Integración con Supabase Auth
    """

    def __init__(self):
        self.current_user: Optional[UserProfile] = None
        self.current_session_token: Optional[str] = None
        self.neo4j_user_service = Neo4jUserService()
        self.mongo_host_service = MongoHostService()
        # Lazy import to avoid circular dependency
        self._session_manager = None
        logger.info("AuthService inicializado")

    @property
    def session_manager(self):
        """Lazy load session manager to avoid circular imports"""
        if self._session_manager is None:
            from services.session import session_manager
            self._session_manager = session_manager
        return self._session_manager

    async def register(
        self,
        email: str,
        password: str,
        rol: str,
        nombre: Optional[str] = None
    ) -> AuthResult:
        """
        Registra un nuevo usuario en el sistema.

        Args:
            email: Correo electrónico del usuario
            password: Contraseña del usuario
            rol: Rol del usuario (HUESPED, ANFITRION, AMBOS)
            nombre: Nombre del usuario (opcional)

        Returns:
            AuthResult con el resultado de la operación
        """
        try:
            logger.info(f"Iniciando registro para email: {email}, rol: {rol}")

            # Validar rol
            if rol not in ['HUESPED', 'ANFITRION', 'AMBOS']:
                return AuthResult(
                    success=False,
                    message="❌ Rol inválido. Debe ser HUESPED, ANFITRION o AMBOS",
                    error="Invalid role"
                )

            # Verificar si el usuario ya existe
            existing_user = await self._get_user_by_email(email)
            if existing_user:
                return AuthResult(
                    success=False,
                    message="❌ Ya existe un usuario con este email",
                    error="User already exists"
                )

            # Insertar solo en la tabla usuario, el trigger de Supabase manejará el resto
            user_profile = await self._create_user(
                email=email,
                rol=rol,
                nombre=nombre or email.split('@')[0]
            )

            if user_profile:
                self.current_user = user_profile
                logger.info(f"Usuario registrado exitosamente: {email}")

                return AuthResult(
                    success=True,
                    message=f"✅ Usuario registrado exitosamente como {rol}",
                    user_profile=user_profile
                )
            else:
                return AuthResult(
                    success=False,
                    message="❌ Error interno durante el registro",
                    error="Internal registration error"
                )

        except Exception as e:
            logger.error(f"Error durante registro: {str(e)}")
            return AuthResult(
                success=False,
                message=f"❌ Error durante el registro: {str(e)}",
                error=str(e)
            )

    async def login(self, email: str, password: str) -> AuthResult:
        """
        Autentica un usuario existente y crea una sesión en Redis.

        Args:
            email: Correo electrónico del usuario
            password: Contraseña del usuario

        Returns:
            AuthResult con el resultado de la operación y el token de sesión
        """
        try:
            logger.info(f"Iniciando login para email: {email}")

            # Obtener usuario de la base de datos
            user_data = await self._get_user_by_email(email)

            if not user_data:
                return AuthResult(
                    success=False,
                    message="❌ Usuario no encontrado",
                    error="User not found"
                )

            # Para esta implementación CLI, aceptamos cualquier password
            # En producción, se verificaría contra Supabase Auth
            user_profile = await self._build_user_profile(user_data)

            # Create session in Redis and get token
            session_token = await self.session_manager.create_session(user_profile)

            # Store in memory as well
            self.current_user = user_profile
            self.current_session_token = session_token

            logger.info(f"Login exitoso para: {email}, session token: {session_token[:8]}...")

            return AuthResult(
                success=True,
                message=f"✅ Bienvenido/a {user_profile.nombre or email}",
                user_profile=user_profile,
                session_token=session_token
            )

        except Exception as e:
            logger.error(f"Error durante login: {str(e)}")
            return AuthResult(
                success=False,
                message=f"❌ Error durante el login: {str(e)}",
                error=str(e)
            )

    async def logout(self) -> AuthResult:
        """
        Cierra la sesión del usuario actual e invalida el token en Redis.

        Returns:
            AuthResult con el resultado de la operación
        """
        try:
            if self.current_user:
                logger.info(f"Cerrando sesión para: {self.current_user.email}")

                # Invalidate session in Redis if we have a token
                if self.current_session_token:
                    await self.session_manager.invalidate_session(self.current_session_token)
                    self.current_session_token = None

                self.current_user = None

            return AuthResult(
                success=True,
                message="✅ Sesión cerrada exitosamente"
            )

        except Exception as e:
            logger.error(f"Error durante logout: {str(e)}")
            return AuthResult(
                success=False,
                message=f"❌ Error cerrando sesión: {str(e)}",
                error=str(e)
            )

    async def restore_session(self, token: str) -> AuthResult:
        """
        Restaura una sesión desde un token almacenado en Redis.

        Args:
            token: Token de sesión a restaurar

        Returns:
            AuthResult indicando si la sesión se restauró exitosamente
        """
        try:
            logger.info(f"Intentando restaurar sesión con token: {token[:8]}...")

            user_profile = await self.session_manager.get_session(token)

            if user_profile:
                self.current_user = user_profile
                self.current_session_token = token
                logger.info(f"Sesión restaurada para: {user_profile.email}")

                return AuthResult(
                    success=True,
                    message=f"✅ Sesión restaurada: {user_profile.nombre or user_profile.email}",
                    user_profile=user_profile,
                    session_token=token
                )
            else:
                return AuthResult(
                    success=False,
                    message="❌ Sesión expirada o inválida",
                    error="Session expired or invalid"
                )

        except Exception as e:
            logger.error(f"Error restaurando sesión: {str(e)}")
            return AuthResult(
                success=False,
                message=f"❌ Error restaurando sesión: {str(e)}",
                error=str(e)
            )

    async def check_session_validity(self) -> bool:
        """
        Verifica si la sesión actual es válida SIN refrescar el TTL.

        Use esto para validar antes de acciones sin extender la sesión.

        Returns:
            True si la sesión es válida, False si expiró
        """
        if not self.current_session_token:
            return False

        try:
            user_profile = await self.session_manager.peek_session(self.current_session_token)
            if user_profile:
                return True
            else:
                # Session expired, clear local state
                self.current_user = None
                self.current_session_token = None
                return False

        except Exception as e:
            logger.error(f"Error verificando sesión: {str(e)}")
            return False

    async def validate_session(self) -> bool:
        """
        Valida que la sesión actual siga siendo válida en Redis.
        Actualiza el TTL si es válida (sliding window).

        Returns:
            True si la sesión es válida, False si expiró
        """
        if not self.current_session_token:
            return False

        try:
            user_profile = await self.session_manager.get_session(self.current_session_token)
            if user_profile:
                # Session is still valid, update current_user
                self.current_user = user_profile
                return True
            else:
                # Session expired, clear local state
                self.current_user = None
                self.current_session_token = None
                return False

        except Exception as e:
            logger.error(f"Error validando sesión: {str(e)}")
            return False

    def get_current_user(self) -> Optional[UserProfile]:
        """
        Obtiene el usuario actualmente autenticado.

        Returns:
            UserProfile del usuario actual o None si no hay sesión
        """
        return self.current_user

    async def list_sessions(self) -> Optional[list]:
        """
        Lista todas las sesiones activas del usuario actual.

        Returns:
            Lista de sesiones activas o None si no hay usuario autenticado
        """
        if not self.current_user:
            return None

        try:
            sessions = await self.session_manager.list_user_sessions(self.current_user.id)
            return sessions
        except Exception as e:
            logger.error(f"Error listando sesiones: {str(e)}")
            return []

    def is_authenticated(self) -> bool:
        """
        Verifica si hay un usuario autenticado.

        Returns:
            True si hay un usuario autenticado, False en caso contrario
        """
        return self.current_user is not None

    def has_role(self, role: str) -> bool:
        """
        Verifica si el usuario actual tiene un rol específico.

        Args:
            role: Rol a verificar (HUESPED, ANFITRION)

        Returns:
            True si el usuario tiene el rol, False en caso contrario
        """
        if not self.current_user:
            return False

        if self.current_user.rol == 'AMBOS':
            return role in ['HUESPED', 'ANFITRION']

        return self.current_user.rol == role

    async def update_user_role(self, user_id: int, new_role: str) -> bool:
        """
        Actualiza el rol de un usuario en PostgreSQL y Neo4j.

        Args:
            user_id: ID del usuario
            new_role: Nuevo rol (HUESPED, ANFITRION, AMBOS)

        Returns:
            True si se actualizó exitosamente, False en caso contrario
        """
        try:
            logger.info(
                f"Actualizando rol de usuario: ID={user_id}, nuevo_rol={new_role}")

            # Validar nuevo rol
            if new_role not in ['HUESPED', 'ANFITRION', 'AMBOS']:
                logger.error(f"Rol inválido: {new_role}")
                return False

            # Actualizar en PostgreSQL
            result = await execute_query(
                "UPDATE usuario SET rol = $1 WHERE id = $2 RETURNING id",
                new_role, user_id
            )

            if not result:
                logger.error(
                    f"No se pudo actualizar el rol en PostgreSQL para usuario ID={user_id}")
                return False

            # Actualizar en Neo4j
            neo4j_updated = await self.neo4j_user_service.update_user_role(user_id, new_role)
            if not neo4j_updated:
                logger.warning(
                    f"No se pudo actualizar el rol en Neo4j para usuario ID={user_id}")
                # No fallar completamente, PostgreSQL ya fue actualizado

            # Si el nuevo rol incluye ANFITRION, asegurar documento MongoDB
            if new_role in ['ANFITRION', 'AMBOS']:
                # Obtener ID de anfitrión
                anfitrion_result = await execute_query(
                    "SELECT id FROM anfitrion WHERE usuario_id = $1",
                    user_id
                )
                if anfitrion_result:
                    anfitrion_id = anfitrion_result[0]['id']
                    mongo_result = await self.mongo_host_service.ensure_host_document_sync(anfitrion_id)
                    if mongo_result.get('success'):
                        action = mongo_result.get('action', 'unknown')
                        logger.info(
                            f"Documento MongoDB para anfitrión ID={anfitrion_id}: {action}")
                    else:
                        logger.warning(
                            f"No se pudo sincronizar documento MongoDB para anfitrión ID={anfitrion_id}: {mongo_result.get('error')}")

            # Si el usuario actual es el que se está actualizando, actualizar la sesión
            if self.current_user and self.current_user.id == user_id:
                self.current_user.rol = new_role
                logger.info(f"Rol actualizado en sesión actual: {new_role}")

            return True

        except Exception as e:
            logger.error(f"Error actualizando rol de usuario: {str(e)}")
            return False

    async def ensure_neo4j_sync(self, user_id: Optional[int] = None) -> bool:
        """
        Asegura que los nodos de Neo4j estén sincronizados con PostgreSQL.

        Args:
            user_id: ID específico de usuario a sincronizar. Si es None, sincroniza el usuario actual.

        Returns:
            True si se sincronizó exitosamente, False en caso contrario
        """
        try:
            if user_id is None and self.current_user:
                user_id = self.current_user.id
                rol = self.current_user.rol
            elif user_id is not None:
                # Obtener rol del usuario de la base de datos
                user_data = await execute_query(
                    "SELECT rol FROM usuario WHERE id = $1",
                    user_id
                )
                if not user_data:
                    logger.error(f"Usuario no encontrado para ID={user_id}")
                    return False
                rol = user_data[0]['rol']
            else:
                logger.error(
                    "No se especificó user_id y no hay usuario actual")
                return False

            return await self.neo4j_user_service.ensure_user_node_sync(user_id, rol)

        except Exception as e:
            logger.error(f"Error sincronizando con Neo4j: {str(e)}")
            return False

    # Métodos privados
    async def _get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Obtiene los datos de usuario por email."""
        try:
            result = await execute_query(
                "SELECT * FROM usuario WHERE email = $1",
                email
            )
            return result[0] if result else None

        except Exception as e:
            logger.error(f"Error obteniendo usuario por email: {str(e)}")
            return None

    async def _create_user(
        self,
        email: str,
        rol: str,
        nombre: str
    ) -> Optional[UserProfile]:
        """
        Simula Supabase Auth signUp con metadata.
        En producción sería: supabase.auth.signUp({email, password, options: {data: {rol, nombre}}})
        El trigger de Supabase se encarga automáticamente de crear los registros en las tablas correspondientes.
        """
        try:
            # Para desarrollo: insertar en usuario sin auth_user_id por ahora
            # En producción, Supabase Auth creará el user y el trigger poblará automáticamente
            user_result = await execute_query(
                """
                INSERT INTO usuario (email, rol)
                VALUES ($1, $2)
                RETURNING id, email, rol, auth_user_id, creado_en
                """,
                email, rol
            )

            if not user_result:
                return None

            user_data = user_result[0]

            # El trigger ya habrá creado automáticamente los registros en huesped/anfitrion
            # Ahora obtenemos los IDs generados por el trigger
            user_id = user_data['id']
            huesped_id = None
            anfitrion_id = None

            # Obtener ID de huésped si corresponde
            if rol in ['HUESPED', 'AMBOS']:
                huesped_result = await execute_query(
                    "SELECT id FROM huesped WHERE usuario_id = $1",
                    user_id
                )
                if huesped_result:
                    huesped_id = huesped_result[0]['id']

            # Obtener ID de anfitrión si corresponde
            if rol in ['ANFITRION', 'AMBOS']:
                anfitrion_result = await execute_query(
                    "SELECT id FROM anfitrion WHERE usuario_id = $1",
                    user_id
                )
                if anfitrion_result:
                    anfitrion_id = anfitrion_result[0]['id']

            # Crear nodo de usuario en Neo4j
            neo4j_created = await self.neo4j_user_service.create_user_node(user_id, rol)
            if not neo4j_created:
                logger.warning(
                    f"No se pudo crear el nodo de usuario en Neo4j para ID={user_id}")
                # Continuar sin fallar, ya que el registro en PostgreSQL fue exitoso

            # Crear documento en MongoDB para anfitriones
            if rol in ['ANFITRION', 'AMBOS'] and anfitrion_id:
                mongo_result = await self.mongo_host_service.create_host_document(anfitrion_id)
                if mongo_result.get('success'):
                    logger.info(
                        f"Documento MongoDB creado para anfitrión ID={anfitrion_id}")
                else:
                    logger.warning(
                        f"No se pudo crear documento MongoDB para anfitrión ID={anfitrion_id}: {mongo_result.get('error')}")
                    # Continuar sin fallar, ya que el registro principal fue exitoso

            return UserProfile(
                id=user_data['id'],
                email=user_data['email'],
                rol=user_data['rol'],
                auth_user_id=str(
                    user_data['auth_user_id']) if user_data['auth_user_id'] else None,
                creado_en=user_data['creado_en'],
                huesped_id=huesped_id,
                anfitrion_id=anfitrion_id,
                nombre=nombre
            )

        except Exception as e:
            logger.error(f"Error creando usuario: {str(e)}")
            return None

    async def _build_user_profile(self, user_data: Dict[str, Any]) -> UserProfile:
        """Construye el perfil completo del usuario."""
        try:
            user_id = user_data['id']

            # Obtener datos de huésped si existe
            huesped_data = None
            if user_data['rol'] in ['HUESPED', 'AMBOS']:
                huesped_result = await execute_query(
                    "SELECT id, nombre FROM huesped WHERE usuario_id = $1",
                    user_id
                )
                huesped_data = huesped_result[0] if huesped_result else None

            # Obtener datos de anfitrión si existe
            anfitrion_data = None
            if user_data['rol'] in ['ANFITRION', 'AMBOS']:
                anfitrion_result = await execute_query(
                    "SELECT id, nombre FROM anfitrion WHERE usuario_id = $1",
                    user_id
                )
                anfitrion_data = anfitrion_result[0] if anfitrion_result else None

            # Determinar nombre a mostrar
            nombre = user_data.get('nombre')
            if not nombre:
                if huesped_data and huesped_data.get('nombre'):
                    nombre = huesped_data['nombre']
                elif anfitrion_data and anfitrion_data.get('nombre'):
                    nombre = anfitrion_data['nombre']
                else:
                    nombre = user_data['email'].split('@')[0]

            return UserProfile(
                id=user_data['id'],
                email=user_data['email'],
                rol=user_data['rol'],
                auth_user_id=user_data.get('auth_user_id'),
                creado_en=user_data['creado_en'],
                huesped_id=huesped_data['id'] if huesped_data else None,
                anfitrion_id=anfitrion_data['id'] if anfitrion_data else None,
                nombre=nombre
            )

        except Exception as e:
            logger.error(f"Error construyendo perfil de usuario: {str(e)}")
            raise
