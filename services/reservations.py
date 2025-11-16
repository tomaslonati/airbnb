"""
Servicio de reservas que utiliza PostgreSQL (Supabase).
Cassandra logging será agregado en el futuro.
"""

from datetime import date
from typing import Dict, Any, Optional
from decimal import Decimal
from db.postgres import execute_query, execute_command, get_client
from utils.logging import get_logger

logger = get_logger(__name__)


class ReservationService:
    """
    Servicio para gestionar reservas de propiedades.
    
    Responsabilidades:
    - Gestionar reservas en PostgreSQL
    - Registrar eventos en Cassandra
    - Validar disponibilidad
    - Calcular precios
    """

    def __init__(self):
        logger.info("ReservationService inicializado")

    async def _log_event_to_cassandra(
        self,
        reserva_id: int,
        event_type: str,
        propiedad_id: int,
        huesped_id: int,
        check_in: date,
        check_out: date,
        metadata: Optional[Dict[str, str]] = None
    ):
        """
        Placeholder para logging de eventos en Cassandra (futuro).
        Por ahora solo registra en logs.
        
        Args:
            reserva_id: ID de la reserva
            event_type: Tipo de evento (CREATED, CANCELLED, CHECKED_IN, etc.)
            propiedad_id: ID de la propiedad
            huesped_id: ID del huésped
            check_in: Fecha de entrada
            check_out: Fecha de salida
            metadata: Información adicional del evento
        """
        logger.info(
            f"Evento {event_type} para reserva {reserva_id}",
            event_type=event_type,
            reserva_id=reserva_id,
            propiedad_id=propiedad_id,
            huesped_id=huesped_id
        )
        # TODO: Implementar logging en Cassandra cuando esté listo
        pass

    async def _check_availability(
        self,
        propiedad_id: int,
        check_in: date,
        check_out: date,
        exclude_reserva_id: Optional[int] = None
    ) -> bool:
        """
        Verifica si una propiedad está disponible en las fechas solicitadas.
        
        Args:
            propiedad_id: ID de la propiedad
            check_in: Fecha de entrada
            check_out: Fecha de salida
            exclude_reserva_id: ID de reserva a excluir (para actualizaciones)
            
        Returns:
            True si está disponible, False si no
        """
        try:
            # Verificar que no haya reservas que se solapen
            query = """
                SELECT COUNT(*) as count
                FROM reserva r
                JOIN estado_reserva er ON r.estado_reserva_id = er.id
                WHERE r.propiedad_id = $1
                AND er.nombre NOT IN ('Cancelada', 'Rechazada')
                AND (
                    (r.fecha_inicio <= $2 AND r.fecha_fin > $2)
                    OR (r.fecha_inicio < $3 AND r.fecha_fin >= $3)
                    OR (r.fecha_inicio >= $2 AND r.fecha_fin <= $3)
                )
            """
            
            params = [propiedad_id, check_in, check_out]
            
            if exclude_reserva_id:
                query += " AND r.id != $4"
                params.append(exclude_reserva_id)
            
            result = await execute_query(query, *params)
            
            if result and result[0]['count'] > 0:
                logger.warning(f"Propiedad {propiedad_id} no disponible entre {check_in} y {check_out}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error verificando disponibilidad: {str(e)}")
            return False

    async def _calculate_total_price(
        self,
        propiedad_id: int,
        check_in: date,
        check_out: date
    ) -> Decimal:
        """
        Calcula el precio total de una reserva basado en el calendario de disponibilidad.
        
        Args:
            propiedad_id: ID de la propiedad
            check_in: Fecha de entrada
            check_out: Fecha de salida
            
        Returns:
            Precio total de la reserva
        """
        try:
            # Sumar precios del calendario de disponibilidad
            query = """
                SELECT COALESCE(SUM(precio_noche), 0) as total
                FROM calendario_disponibilidad
                WHERE propiedad_id = $1
                AND fecha >= $2
                AND fecha < $3
                AND disponible = TRUE
            """
            
            result = await execute_query(query, propiedad_id, check_in, check_out)
            
            if result and result[0]['total']:
                return Decimal(str(result[0]['total']))
            else:
                # Si no hay calendario, usar precio base de la propiedad
                prop_query = "SELECT precio_base FROM propiedad WHERE id = $1"
                prop_result = await execute_query(prop_query, propiedad_id)
                
                if prop_result:
                    num_nights = (check_out - check_in).days
                    precio_base = Decimal(str(prop_result[0].get('precio_base', 100)))
                    return precio_base * num_nights
                
                return Decimal('0')
                
        except Exception as e:
            logger.error(f"Error calculando precio: {str(e)}")
            return Decimal('0')

    async def create_reservation(
        self,
        propiedad_id: int,
        huesped_id: int,
        check_in: date,
        check_out: date,
        num_huespedes: int = 1,
        metodo_pago_id: int = 1,
        comentarios: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Crea una nueva reserva.
        
        Proceso:
        1. Verificar disponibilidad en PostgreSQL
        2. Calcular precio total
        3. Crear la reserva en PostgreSQL
        4. Registrar evento en Cassandra
        
        Args:
            propiedad_id: ID de la propiedad
            huesped_id: ID del huésped
            check_in: Fecha de entrada
            check_out: Fecha de salida
            num_huespedes: Número de huéspedes
            metodo_pago_id: ID del método de pago
            comentarios: Comentarios especiales
            
        Returns:
            Diccionario con success, message, y datos de la reserva
        """
        try:
            # Validaciones básicas
            if check_in < date.today():
                return {
                    "success": False,
                    "error": "La fecha de entrada no puede ser en el pasado"
                }
            
            if check_out <= check_in:
                return {
                    "success": False,
                    "error": "La fecha de salida debe ser posterior a la fecha de entrada"
                }
            
            # Verificar que la propiedad existe
            prop_result = await execute_query(
                "SELECT id, nombre, capacidad FROM propiedad WHERE id = $1",
                propiedad_id
            )
            
            if not prop_result:
                return {
                    "success": False,
                    "error": f"Propiedad con ID {propiedad_id} no existe"
                }
            
            propiedad = prop_result[0]
            
            # Verificar capacidad
            if num_huespedes > propiedad['capacidad']:
                return {
                    "success": False,
                    "error": f"La propiedad tiene capacidad para {propiedad['capacidad']} huéspedes, solicitaste {num_huespedes}"
                }
            
            # Verificar disponibilidad
            is_available = await self._check_availability(propiedad_id, check_in, check_out)
            
            if not is_available:
                return {
                    "success": False,
                    "error": "La propiedad no está disponible en las fechas seleccionadas"
                }
            
            # Calcular precio total
            total_price = await self._calculate_total_price(propiedad_id, check_in, check_out)
            
            # Obtener estado "Confirmada"
            estado_result = await execute_query(
                "SELECT id FROM estado_reserva WHERE nombre = 'Confirmada'"
            )
            
            if not estado_result:
                return {
                    "success": False,
                    "error": "No se encontró el estado 'Confirmada' en la base de datos"
                }
            
            estado_id = estado_result[0]['id']
            
            # Crear la reserva
            pool = await get_client()
            async with pool.acquire() as conn:
                async with conn.transaction():
                    query = """
                        INSERT INTO reserva (
                            propiedad_id, huesped_id, fecha_inicio, fecha_fin,
                            num_huespedes, precio_total, metodo_pago_id,
                            estado_reserva_id, comentarios
                        )
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                        RETURNING id, fecha_creacion
                    """
                    
                    result = await conn.fetchrow(
                        query,
                        propiedad_id,
                        huesped_id,
                        check_in,
                        check_out,
                        num_huespedes,
                        total_price,
                        metodo_pago_id,
                        estado_id,
                        comentarios
                    )
                    
                    reserva_id = result['id']
                    fecha_creacion = result['fecha_creacion']
                    
                    logger.info(f"Reserva {reserva_id} creada exitosamente")
            
            # Registrar evento en Cassandra (async, no bloquear si falla)
            await self._log_event_to_cassandra(
                reserva_id=reserva_id,
                event_type="CREATED",
                propiedad_id=propiedad_id,
                huesped_id=huesped_id,
                check_in=check_in,
                check_out=check_out,
                metadata={
                    "num_huespedes": str(num_huespedes),
                    "precio_total": str(total_price)
                }
            )
            
            num_nights = (check_out - check_in).days
            
            return {
                "success": True,
                "message": "Reserva creada exitosamente",
                "reservation": {
                    "id": reserva_id,
                    "propiedad_id": propiedad_id,
                    "propiedad_nombre": propiedad['nombre'],
                    "huesped_id": huesped_id,
                    "check_in": check_in.isoformat(),
                    "check_out": check_out.isoformat(),
                    "num_nights": num_nights,
                    "num_huespedes": num_huespedes,
                    "precio_total": float(total_price),
                    "estado": "Confirmada",
                    "fecha_creacion": fecha_creacion.isoformat(),
                    "comentarios": comentarios
                }
            }
            
        except Exception as e:
            logger.error(f"Error creando reserva: {str(e)}")
            return {
                "success": False,
                "error": f"Error al crear la reserva: {str(e)}"
            }

    async def get_user_reservations(
        self,
        huesped_id: int,
        include_cancelled: bool = False
    ) -> Dict[str, Any]:
        """
        Obtiene las reservas de un huésped.
        
        Args:
            huesped_id: ID del huésped
            include_cancelled: Si incluir reservas canceladas
            
        Returns:
            Diccionario con success y lista de reservas
        """
        try:
            query = """
                SELECT 
                    r.id,
                    r.propiedad_id,
                    p.nombre as propiedad_nombre,
                    r.fecha_inicio,
                    r.fecha_fin,
                    r.num_huespedes,
                    r.precio_total,
                    r.fecha_creacion,
                    r.comentarios,
                    er.nombre as estado,
                    c.nombre as ciudad,
                    pa.nombre as pais
                FROM reserva r
                JOIN propiedad p ON r.propiedad_id = p.id
                JOIN estado_reserva er ON r.estado_reserva_id = er.id
                JOIN ciudad c ON p.ciudad_id = c.id
                JOIN pais pa ON c.pais_id = pa.id
                WHERE r.huesped_id = $1
            """
            
            if not include_cancelled:
                query += " AND er.nombre NOT IN ('Cancelada', 'Rechazada')"
            
            query += " ORDER BY r.fecha_inicio DESC"
            
            results = await execute_query(query, huesped_id)
            
            reservations = []
            for row in results:
                num_nights = (row['fecha_fin'] - row['fecha_inicio']).days
                reservations.append({
                    "id": row['id'],
                    "propiedad_id": row['propiedad_id'],
                    "propiedad_nombre": row['propiedad_nombre'],
                    "check_in": row['fecha_inicio'].isoformat(),
                    "check_out": row['fecha_fin'].isoformat(),
                    "num_nights": num_nights,
                    "num_huespedes": row['num_huespedes'],
                    "precio_total": float(row['precio_total']),
                    "estado": row['estado'],
                    "ciudad": row['ciudad'],
                    "pais": row['pais'],
                    "fecha_creacion": row['fecha_creacion'].isoformat(),
                    "comentarios": row['comentarios']
                })
            
            return {
                "success": True,
                "reservations": reservations,
                "total": len(reservations)
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo reservas: {str(e)}")
            return {
                "success": False,
                "error": f"Error al obtener reservas: {str(e)}",
                "reservations": [],
                "total": 0
            }

    async def get_reservation(self, reserva_id: int) -> Dict[str, Any]:
        """
        Obtiene los detalles de una reserva específica.
        
        Args:
            reserva_id: ID de la reserva
            
        Returns:
            Diccionario con success y datos de la reserva
        """
        try:
            query = """
                SELECT 
                    r.id,
                    r.propiedad_id,
                    p.nombre as propiedad_nombre,
                    p.descripcion as propiedad_descripcion,
                    r.huesped_id,
                    h.nombre as huesped_nombre,
                    h.email as huesped_email,
                    r.fecha_inicio,
                    r.fecha_fin,
                    r.num_huespedes,
                    r.precio_total,
                    r.fecha_creacion,
                    r.comentarios,
                    er.nombre as estado,
                    c.nombre as ciudad,
                    pa.nombre as pais,
                    mp.nombre as metodo_pago
                FROM reserva r
                JOIN propiedad p ON r.propiedad_id = p.id
                JOIN huesped h ON r.huesped_id = h.id
                JOIN estado_reserva er ON r.estado_reserva_id = er.id
                JOIN ciudad c ON p.ciudad_id = c.id
                JOIN pais pa ON c.pais_id = pa.id
                LEFT JOIN metodo_pago mp ON r.metodo_pago_id = mp.id
                WHERE r.id = $1
            """
            
            result = await execute_query(query, reserva_id)
            
            if not result:
                return {
                    "success": False,
                    "error": f"Reserva con ID {reserva_id} no encontrada"
                }
            
            row = result[0]
            num_nights = (row['fecha_fin'] - row['fecha_inicio']).days
            
            return {
                "success": True,
                "reservation": {
                    "id": row['id'],
                    "propiedad": {
                        "id": row['propiedad_id'],
                        "nombre": row['propiedad_nombre'],
                        "descripcion": row['propiedad_descripcion'],
                        "ciudad": row['ciudad'],
                        "pais": row['pais']
                    },
                    "huesped": {
                        "id": row['huesped_id'],
                        "nombre": row['huesped_nombre'],
                        "email": row['huesped_email']
                    },
                    "check_in": row['fecha_inicio'].isoformat(),
                    "check_out": row['fecha_fin'].isoformat(),
                    "num_nights": num_nights,
                    "num_huespedes": row['num_huespedes'],
                    "precio_total": float(row['precio_total']),
                    "estado": row['estado'],
                    "metodo_pago": row['metodo_pago'],
                    "fecha_creacion": row['fecha_creacion'].isoformat(),
                    "comentarios": row['comentarios']
                }
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo reserva: {str(e)}")
            return {
                "success": False,
                "error": f"Error al obtener reserva: {str(e)}"
            }

    async def cancel_reservation(
        self,
        reserva_id: int,
        huesped_id: int,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cancela una reserva.
        
        Args:
            reserva_id: ID de la reserva
            huesped_id: ID del huésped (para verificar ownership)
            reason: Razón de la cancelación
            
        Returns:
            Diccionario con success y message
        """
        try:
            # Verificar que la reserva existe y pertenece al huésped
            verify_query = """
                SELECT r.id, r.propiedad_id, r.fecha_inicio, r.fecha_fin, er.nombre as estado
                FROM reserva r
                JOIN estado_reserva er ON r.estado_reserva_id = er.id
                WHERE r.id = $1 AND r.huesped_id = $2
            """
            
            result = await execute_query(verify_query, reserva_id, huesped_id)
            
            if not result:
                return {
                    "success": False,
                    "error": "Reserva no encontrada o no te pertenece"
                }
            
            reserva = result[0]
            
            # Verificar que no esté ya cancelada
            if reserva['estado'] in ['Cancelada', 'Rechazada']:
                return {
                    "success": False,
                    "error": f"La reserva ya está {reserva['estado'].lower()}"
                }
            
            # Obtener ID del estado "Cancelada"
            estado_result = await execute_query(
                "SELECT id FROM estado_reserva WHERE nombre = 'Cancelada'"
            )
            
            if not estado_result:
                return {
                    "success": False,
                    "error": "No se encontró el estado 'Cancelada' en la base de datos"
                }
            
            estado_id = estado_result[0]['id']
            
            # Actualizar la reserva
            update_query = """
                UPDATE reserva
                SET estado_reserva_id = $1, comentarios = COALESCE(comentarios || ' | Cancelación: ' || $2, $2)
                WHERE id = $3
            """
            
            await execute_command(update_query, estado_id, reason or "Sin razón especificada", reserva_id)
            
            logger.info(f"Reserva {reserva_id} cancelada exitosamente")
            
            # Registrar evento en Cassandra
            await self._log_event_to_cassandra(
                reserva_id=reserva_id,
                event_type="CANCELLED",
                propiedad_id=reserva['propiedad_id'],
                huesped_id=huesped_id,
                check_in=reserva['fecha_inicio'],
                check_out=reserva['fecha_fin'],
                metadata={"reason": reason or "Sin razón especificada"}
            )
            
            return {
                "success": True,
                "message": "Reserva cancelada exitosamente"
            }
            
        except Exception as e:
            logger.error(f"Error cancelando reserva: {str(e)}")
            return {
                "success": False,
                "error": f"Error al cancelar reserva: {str(e)}"
            }

    async def get_property_availability(
        self,
        propiedad_id: int,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        Obtiene la disponibilidad de una propiedad en un rango de fechas.
        
        Args:
            propiedad_id: ID de la propiedad
            start_date: Fecha inicio del rango
            end_date: Fecha fin del rango
            
        Returns:
            Diccionario con fechas disponibles y no disponibles
        """
        try:
            query = """
                SELECT fecha, disponible, precio_noche
                FROM calendario_disponibilidad
                WHERE propiedad_id = $1
                AND fecha >= $2
                AND fecha <= $3
                ORDER BY fecha
            """
            
            results = await execute_query(query, propiedad_id, start_date, end_date)
            
            available_dates = []
            unavailable_dates = []
            
            for row in results:
                date_info = {
                    "fecha": row['fecha'].isoformat(),
                    "precio": float(row['precio_noche'])
                }
                
                if row['disponible']:
                    available_dates.append(date_info)
                else:
                    unavailable_dates.append(date_info)
            
            return {
                "success": True,
                "propiedad_id": propiedad_id,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "available_dates": available_dates,
                "unavailable_dates": unavailable_dates,
                "total_days": (end_date - start_date).days + 1
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo disponibilidad: {str(e)}")
            return {
                "success": False,
                "error": f"Error al obtener disponibilidad: {str(e)}"
            }
