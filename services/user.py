"""
Servicio de gestión de usuarios para el sistema Airbnb.
Maneja operaciones específicas por rol (HUESPED, ANFITRION, AMBOS).
Sigue principios SOLID.
"""

import asyncio
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

from db.postgres import execute_query, execute_command
from utils.logging import get_logger
from services.auth import UserProfile

logger = get_logger(__name__)


@dataclass
class HuespedProfile:
    """Perfil extendido de huésped."""
    id: int
    usuario_id: int
    nombre: str
    email: Optional[str]
    telefono: Optional[str]
    reservas_activas: int = 0
    total_reservas: int = 0


@dataclass
class AnfitrionProfile:
    """Perfil extendido de anfitrión."""
    id: int
    usuario_id: int
    nombre: str
    cant_rvas_completadas: int
    total_propiedades: int = 0
    propiedades_activas: int = 0


@dataclass
class UserStats:
    """Estadísticas del usuario según su rol."""
    rol: str
    huesped_stats: Optional[Dict[str, Any]] = None
    anfitrion_stats: Optional[Dict[str, Any]] = None


class UserService:
    """
    Servicio de gestión de usuarios siguiendo principios SOLID.

    Responsabilidades:
    - Obtener perfiles extendidos de usuarios
    - Gestionar datos específicos por rol
    - Proporcionar estadísticas de usuario
    - Operaciones CRUD sobre perfiles
    """

    def __init__(self):
        logger.info("UserService inicializado")

    async def get_huesped_profile(self, user_profile: UserProfile) -> Optional[HuespedProfile]:
        """
        Obtiene el perfil extendido de huésped.

        Args:
            user_profile: Perfil base del usuario

        Returns:
            HuespedProfile con datos extendidos o None
        """
        try:
            if not user_profile.huesped_id:
                logger.warning(
                    f"Usuario {user_profile.email} no tiene perfil de huésped")
                return None

            # Obtener datos básicos del huésped
            huesped_result = await execute_query(
                "SELECT * FROM huesped WHERE id = $1",
                user_profile.huesped_id
            )

            if not huesped_result:
                return None

            huesped_data = huesped_result[0]

            # Obtener estadísticas de reservas
            reservas_stats = await execute_query(
                """
                SELECT 
                    COUNT(*) as total_reservas,
                    COUNT(CASE WHEN er.nombre IN ('Confirmada', 'En curso') THEN 1 END) as reservas_activas
                FROM reserva r
                JOIN estado_reserva er ON r.estado_reserva_id = er.id
                WHERE r.huesped_id = $1
                """,
                user_profile.huesped_id
            )

            stats = reservas_stats[0] if reservas_stats else {
                'total_reservas': 0, 'reservas_activas': 0}

            return HuespedProfile(
                id=huesped_data['id'],
                usuario_id=huesped_data['usuario_id'],
                nombre=huesped_data['nombre'],
                email=huesped_data.get('email'),
                telefono=huesped_data.get('telefono'),
                reservas_activas=stats['reservas_activas'] or 0,
                total_reservas=stats['total_reservas'] or 0
            )

        except Exception as e:
            logger.error(f"Error obteniendo perfil de huésped: {str(e)}")
            return None

    async def get_anfitrion_profile(self, user_profile: UserProfile) -> Optional[AnfitrionProfile]:
        """
        Obtiene el perfil extendido de anfitrión.

        Args:
            user_profile: Perfil base del usuario

        Returns:
            AnfitrionProfile con datos extendidos o None
        """
        try:
            if not user_profile.anfitrion_id:
                logger.warning(
                    f"Usuario {user_profile.email} no tiene perfil de anfitrión")
                return None

            # Obtener datos básicos del anfitrión
            anfitrion_result = await execute_query(
                "SELECT * FROM anfitrion WHERE id = $1",
                user_profile.anfitrion_id
            )

            if not anfitrion_result:
                return None

            anfitrion_data = anfitrion_result[0]

            # Obtener estadísticas de propiedades
            propiedades_stats = await execute_query(
                """
                SELECT 
                    COUNT(*) as total_propiedades,
                    COUNT(*) as propiedades_activas
                FROM propiedad 
                WHERE anfitrion_id = $1
                """,
                user_profile.anfitrion_id
            )

            stats = propiedades_stats[0] if propiedades_stats else {
                'total_propiedades': 0, 'propiedades_activas': 0}

            return AnfitrionProfile(
                id=anfitrion_data['id'],
                usuario_id=anfitrion_data['usuario_id'],
                nombre=anfitrion_data['nombre'],
                cant_rvas_completadas=anfitrion_data['cant_rvas_completadas'] or 0,
                total_propiedades=stats['total_propiedades'] or 0,
                propiedades_activas=stats['propiedades_activas'] or 0
            )

        except Exception as e:
            logger.error(f"Error obteniendo perfil de anfitrión: {str(e)}")
            return None

    async def get_user_stats(self, user_profile: UserProfile) -> UserStats:
        """
        Obtiene estadísticas completas del usuario según su rol.

        Args:
            user_profile: Perfil base del usuario

        Returns:
            UserStats con estadísticas según el rol
        """
        try:
            stats = UserStats(rol=user_profile.rol)

            # Estadísticas de huésped
            if user_profile.rol in ['HUESPED', 'AMBOS'] and user_profile.huesped_id:
                huesped_stats = await execute_query(
                    """
                    SELECT 
                        COUNT(*) as total_reservas,
                        COUNT(CASE WHEN er.nombre = 'Completada' THEN 1 END) as reservas_completadas,
                        COUNT(CASE WHEN er.nombre IN ('Confirmada', 'En curso') THEN 1 END) as reservas_activas,
                        COUNT(CASE WHEN er.nombre = 'Cancelada' THEN 1 END) as reservas_canceladas,
                        COALESCE(SUM(CASE WHEN er.nombre = 'Completada' THEN r.monto_final END), 0) as gasto_total
                    FROM reserva r
                    JOIN estado_reserva er ON r.estado_reserva_id = er.id
                    WHERE r.huesped_id = $1
                    """,
                    user_profile.huesped_id
                )

                if huesped_stats:
                    stats.huesped_stats = dict(huesped_stats[0])

            # Estadísticas de anfitrión
            if user_profile.rol in ['ANFITRION', 'AMBOS'] and user_profile.anfitrion_id:
                anfitrion_stats = await execute_query(
                    """
                    SELECT 
                        COUNT(DISTINCT p.id) as total_propiedades,
                        COUNT(DISTINCT r.id) as total_reservas_recibidas,
                        a.cant_rvas_completadas,
                        COALESCE(SUM(CASE WHEN er.nombre = 'Completada' THEN r.monto_final END), 0) as ingresos_totales,
                        COALESCE(AVG(CASE WHEN res.puntaje IS NOT NULL THEN res.puntaje END), 0) as puntaje_promedio
                    FROM anfitrion a
                    LEFT JOIN propiedad p ON a.id = p.anfitrion_id
                    LEFT JOIN reserva r ON p.id = r.propiedad_id
                    LEFT JOIN estado_reserva er ON r.estado_reserva_id = er.id
                    LEFT JOIN resenia res ON r.id = res.reserva_id
                    WHERE a.id = $1
                    GROUP BY a.id, a.cant_rvas_completadas
                    """,
                    user_profile.anfitrion_id
                )

                if anfitrion_stats:
                    stats.anfitrion_stats = dict(anfitrion_stats[0])

            logger.info(
                f"Estadísticas obtenidas para usuario: {user_profile.email}")
            return stats

        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de usuario: {str(e)}")
            return UserStats(rol=user_profile.rol)

    async def update_huesped_profile(
        self,
        huesped_id: int,
        nombre: Optional[str] = None,
        email: Optional[str] = None,
        telefono: Optional[str] = None
    ) -> bool:
        """
        Actualiza el perfil de huésped.

        Args:
            huesped_id: ID del huésped
            nombre: Nuevo nombre (opcional)
            email: Nuevo email (opcional)
            telefono: Nuevo teléfono (opcional)

        Returns:
            True si se actualizó correctamente, False en caso contrario
        """
        try:
            updates = []
            params = []
            param_count = 1

            if nombre:
                updates.append(f"nombre = ${param_count}")
                params.append(nombre)
                param_count += 1

            if email:
                updates.append(f"email = ${param_count}")
                params.append(email)
                param_count += 1

            if telefono:
                updates.append(f"telefono = ${param_count}")
                params.append(telefono)
                param_count += 1

            if not updates:
                return True  # No hay nada que actualizar

            params.append(huesped_id)  # ID al final

            query = f"""
                UPDATE huesped 
                SET {', '.join(updates)}
                WHERE id = ${param_count}
            """

            result = await execute_command(query, *params)

            if result:
                logger.info(
                    f"Perfil de huésped {huesped_id} actualizado exitosamente")
                return True
            else:
                logger.warning(
                    f"No se pudo actualizar el perfil de huésped {huesped_id}")
                return False

        except Exception as e:
            logger.error(f"Error actualizando perfil de huésped: {str(e)}")
            return False

    async def update_anfitrion_profile(
        self,
        anfitrion_id: int,
        nombre: Optional[str] = None
    ) -> bool:
        """
        Actualiza el perfil de anfitrión.

        Args:
            anfitrion_id: ID del anfitrión
            nombre: Nuevo nombre (opcional)

        Returns:
            True si se actualizó correctamente, False en caso contrario
        """
        try:
            if not nombre:
                return True  # No hay nada que actualizar

            result = await execute_command(
                "UPDATE anfitrion SET nombre = $1 WHERE id = $2",
                nombre, anfitrion_id
            )

            if result:
                logger.info(
                    f"Perfil de anfitrión {anfitrion_id} actualizado exitosamente")
                return True
            else:
                logger.warning(
                    f"No se pudo actualizar el perfil de anfitrión {anfitrion_id}")
                return False

        except Exception as e:
            logger.error(f"Error actualizando perfil de anfitrión: {str(e)}")
            return False

    async def get_user_reservations(self, huesped_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtiene las reservas de un huésped.

        Args:
            huesped_id: ID del huésped
            limit: Límite de reservas a obtener

        Returns:
            Lista de reservas
        """
        try:
            reservas = await execute_query(
                """
                SELECT 
                    r.id,
                    r.fecha_check_in,
                    r.fecha_check_out,
                    r.monto_final,
                    p.nombre as propiedad_nombre,
                    c.nombre as ciudad,
                    pa.nombre as pais,
                    er.nombre as estado,
                    a.nombre as anfitrion_nombre
                FROM reserva r
                JOIN propiedad p ON r.propiedad_id = p.id
                JOIN ciudad c ON p.ciudad_id = c.id
                JOIN pais pa ON c.pais_id = pa.id
                JOIN estado_reserva er ON r.estado_reserva_id = er.id
                JOIN anfitrion a ON p.anfitrion_id = a.id
                WHERE r.huesped_id = $1
                ORDER BY r.fecha_check_in DESC
                LIMIT $2
                """,
                huesped_id, limit
            )

            return [dict(reserva) for reserva in reservas] if reservas else []

        except Exception as e:
            logger.error(f"Error obteniendo reservas de huésped: {str(e)}")
            return []

    async def get_anfitrion_properties(self, anfitrion_id: int) -> List[Dict[str, Any]]:
        """
        Obtiene las propiedades de un anfitrión.

        Args:
            anfitrion_id: ID del anfitrión

        Returns:
            Lista de propiedades
        """
        try:
            propiedades = await execute_query(
                """
                SELECT 
                    p.id,
                    p.nombre,
                    p.descripcion,
                    p.capacidad,
                    c.nombre as ciudad,
                    pa.nombre as pais,
                    tp.nombre as tipo_propiedad,
                    COUNT(r.id) as total_reservas
                FROM propiedad p
                JOIN ciudad c ON p.ciudad_id = c.id
                JOIN pais pa ON c.pais_id = pa.id
                JOIN tipo_propiedad tp ON p.tipo_propiedad_id = tp.id
                LEFT JOIN reserva r ON p.id = r.propiedad_id
                WHERE p.anfitrion_id = $1
                GROUP BY p.id, p.nombre, p.descripcion, p.capacidad, c.nombre, pa.nombre, tp.nombre
                ORDER BY p.nombre
                """,
                anfitrion_id
            )

            return [dict(propiedad) for propiedad in propiedades] if propiedades else []

        except Exception as e:
            logger.error(
                f"Error obteniendo propiedades de anfitrión: {str(e)}")
            return []
