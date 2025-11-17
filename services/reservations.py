"""
Servicio de reservas que utiliza PostgreSQL (Supabase) con sincronización en Cassandra.
"""

from datetime import date, timedelta
from typing import Dict, Any, Optional
from decimal import Decimal
from db.postgres import execute_query, execute_command, get_client
from repositories.cassandra_reservation_repository import get_cassandra_reservation_repository
from utils.logging import get_logger
import asyncio

logger = get_logger(__name__)


class ReservationService:
    """
    Servicio para gestionar reservas de propiedades.

    Responsabilidades:
    - Gestionar reservas en PostgreSQL
    - Sincronizar con Cassandra para analytics
    - Validar disponibilidad
    - Calcular precios
    - Gestionar comunidades host-huésped en Neo4j
    """

    def __init__(self):
        # Inicialización lazy del servicio Neo4j para evitar dependencias circulares
        self._neo4j_service = None
        # Repositorio Cassandra para sincronización
        self._cassandra_repo = None
        logger.info("ReservationService inicializado")

    @property
    def neo4j_service(self):
        """Lazy loading del servicio Neo4j"""
        if self._neo4j_service is None:
            try:
                from services.neo4j_reservations import Neo4jReservationService
                self._neo4j_service = Neo4jReservationService()
            except ImportError as e:
                logger.warning(
                    f"No se pudo importar Neo4jReservationService: {e}")
                self._neo4j_service = None
        return self._neo4j_service

    @property
    async def cassandra_repo(self):
        """Lazy loading del repositorio Cassandra"""
        if self._cassandra_repo is None:
            try:
                self._cassandra_repo = await get_cassandra_reservation_repository()
            except Exception as e:
                logger.warning(f"No se pudo inicializar repositorio Cassandra: {e}")
                self._cassandra_repo = None
        return self._cassandra_repo

    def close(self):
        """Cierra las conexiones de servicios externos"""
        if self._neo4j_service:
            self._neo4j_service.close()
            self._neo4j_service = None
        
        if self._cassandra_repo:
            asyncio.create_task(self._cassandra_repo.close())
            self._cassandra_repo = None

    async def _sync_reservation_to_cassandra(
        self,
        reserva_id: str,
        event_type: str,
        propiedad_id: int,
        huesped_id: str,
        check_in: date,
        check_out: date,
        monto_total: Optional[Decimal] = None,
        host_id: Optional[str] = None,
        ciudad_id: Optional[int] = None
    ):
        """
        Sincroniza eventos de reservas con Cassandra usando el repositorio específico.

        Args:
            reserva_id: ID de la reserva
            event_type: Tipo de evento (CREATED, CANCELLED)
            propiedad_id: ID de la propiedad
            huesped_id: ID del huésped
            check_in: Fecha de entrada
            check_out: Fecha de salida
            monto_total: Monto total de la reserva (para creación)
            host_id: ID del anfitrión
            ciudad_id: ID de la ciudad
        """
        try:
            repo = await self.cassandra_repo
            if not repo:
                logger.warning("Repositorio Cassandra no disponible, saltando sincronización")
                return

            # Obtener datos adicionales si no se proporcionaron
            if not host_id or not ciudad_id:
                prop_query = """
                    SELECT p.anfitrion_id, c.id as ciudad_id
                    FROM propiedad p
                    JOIN ciudad c ON p.ciudad_id = c.id
                    WHERE p.id = $1
                """
                
                prop_result = await execute_query(prop_query, propiedad_id)
                if prop_result:
                    host_id = host_id or str(prop_result[0]['anfitrion_id'])
                    ciudad_id = ciudad_id or prop_result[0]['ciudad_id']

            # Sincronizar según el tipo de evento
            if event_type == "CREATED" and monto_total:
                await repo.sync_reservation_creation(
                    ciudad_id=ciudad_id,
                    host_id=host_id,
                    propiedad_id=str(propiedad_id),
                    huesped_id=huesped_id,
                    reserva_id=reserva_id,
                    fecha_check_in=check_in,
                    fecha_check_out=check_out,
                    monto_total=monto_total
                )
                logger.info(f"✅ Reserva {reserva_id} sincronizada con Cassandra (CREADA)")

            elif event_type == "CANCELLED":
                await repo.sync_reservation_cancellation(
                    ciudad_id=ciudad_id,
                    host_id=host_id,
                    propiedad_id=str(propiedad_id),
                    reserva_id=reserva_id,
                    fecha_check_in=check_in,
                    fecha_check_out=check_out
                )
                logger.info(f"✅ Reserva {reserva_id} sincronizada con Cassandra (CANCELADA)")

        except Exception as e:
            # No fallar el flujo principal si Cassandra falla
            logger.error(f"❌ Error sincronizando con Cassandra: {e}")
            # Registrar para potencial reintento futuro
            logger.info(
                f"📝 Evento {event_type} para reserva {reserva_id}",
                event_type=event_type,
                reserva_id=reserva_id,
                propiedad_id=propiedad_id,
                huesped_id=huesped_id
            )

    async def _mark_dates_unavailable(
        self,
        propiedad_id: int,
        check_in: date,
        check_out: date,
        reason: str = "Reserva confirmada"
    ):
        """
        Marca fechas como no disponibles en la tabla property_availability.

        Args:
            propiedad_id: ID de la propiedad
            check_in: Fecha de inicio
            check_out: Fecha de fin
            reason: Razón de la no disponibilidad
        """
        try:
            from db.cassandra import cassandra_mark_unavailable
            
            current_date = check_in
            fechas_para_cassandra = []

            while current_date < check_out:
                # Usar UPSERT para evitar conflictos de fechas duplicadas
                query = """
                    INSERT INTO propiedad_disponibilidad (propiedad_id, dia, disponible, price_per_night)
                    VALUES ($1, $2, FALSE, $3)
                    ON CONFLICT (propiedad_id, dia)
                    DO UPDATE SET 
                        disponible = FALSE,
                        updated_at = NOW()
                """

                await execute_command(query, propiedad_id, current_date, None)
                fechas_para_cassandra.append(current_date)
                current_date += timedelta(days=1)

            logger.info(
                f"Fechas {check_in} a {check_out} marcadas como no disponibles para propiedad {propiedad_id}")

            # Sincronizar con Cassandra
            try:
                if fechas_para_cassandra:
                    await cassandra_mark_unavailable(propiedad_id, fechas_para_cassandra)
                    logger.info(f"Sincronizado estado no disponible en Cassandra para propiedad {propiedad_id}")
            except Exception as cassandra_error:
                logger.error(f"Error al sincronizar con Cassandra para marcar no disponible: {cassandra_error}")
                # No fallar el proceso completo por errores de Cassandra
                pass

        except Exception as e:
            logger.error(
                f"Error marcando fechas como no disponibles: {str(e)}")
            raise

    async def _mark_dates_available(
        self,
        propiedad_id: int,
        check_in: date,
        check_out: date,
        price_per_night: Optional[Decimal] = None
    ):
        """
        Marca fechas como disponibles en la tabla property_availability.

        Args:
            propiedad_id: ID de la propiedad
            check_in: Fecha de inicio
            check_out: Fecha de fin
            price_per_night: Precio por noche (opcional)
        """
        try:
            from db.cassandra import cassandra_mark_available
            
            current_date = check_in
            fechas_para_cassandra = []

            # Si no se especifica precio, usar precio por defecto
            if price_per_night is None:
                # La tabla propiedad no tiene precio_base, usar precio estándar
                price_per_night = Decimal('100')  # $100 por noche por defecto

            while current_date < check_out:
                query = """
                    INSERT INTO propiedad_disponibilidad (propiedad_id, dia, disponible, price_per_night)
                    VALUES ($1, $2, TRUE, $3)
                    ON CONFLICT (propiedad_id, dia)
                    DO UPDATE SET 
                        disponible = TRUE,
                        price_per_night = EXCLUDED.price_per_night,
                        updated_at = NOW()
                """

                await execute_command(query, propiedad_id, current_date, price_per_night)
                fechas_para_cassandra.append(current_date)
                current_date += timedelta(days=1)

            logger.info(
                f"Fechas {check_in} a {check_out} marcadas como disponibles para propiedad {propiedad_id}")

            # Sincronizar con Cassandra
            try:
                if fechas_para_cassandra:
                    await cassandra_mark_available(propiedad_id, fechas_para_cassandra)
                    logger.info(f"Sincronizado estado disponible en Cassandra para propiedad {propiedad_id}")
            except Exception as cassandra_error:
                logger.error(f"Error al sincronizar con Cassandra para marcar disponible: {cassandra_error}")
                # No fallar el proceso completo por errores de Cassandra
                pass

        except Exception as e:
            logger.error(f"Error marcando fechas como disponibles: {str(e)}")
            raise

    async def _check_availability(
        self,
        propiedad_id: int,
        check_in: date,
        check_out: date,
        exclude_reserva_id: Optional[int] = None
    ) -> bool:
        """
        Verifica si una propiedad está disponible en las fechas solicitadas.
        Ahora usa la tabla property_availability como fuente principal.

        Args:
            propiedad_id: ID de la propiedad
            check_in: Fecha de entrada
            check_out: Fecha de salida
            exclude_reserva_id: ID de reserva a excluir (para actualizaciones)

        Returns:
            True si está disponible, False si no
        """
        try:
            # Primero verificar en la tabla de disponibilidad
            availability_query = """
                SELECT COUNT(*) as unavailable_days
                FROM propiedad_disponibilidad
                WHERE propiedad_id = $1
                AND dia >= $2
                AND dia < $3
                AND disponible = FALSE
            """

            availability_result = await execute_query(availability_query, propiedad_id, check_in, check_out)

            # Si hay días marcados como no disponibles, no se puede reservar
            if availability_result and availability_result[0]['unavailable_days'] > 0:
                logger.warning(
                    f"Propiedad {propiedad_id} tiene días no disponibles entre {check_in} y {check_out}")
                return False

            # Verificar que no haya reservas confirmadas que se solapen
            reservations_query = """
                SELECT COUNT(*) as count
                FROM reserva r
                JOIN estado_reserva er ON r.estado_reserva_id = er.id
                WHERE r.propiedad_id = $1
                AND er.nombre NOT IN ('Cancelada', 'Rechazada')
                AND (
                    (r.fecha_check_in <= $2 AND r.fecha_check_out > $2)
                    OR (r.fecha_check_in < $3 AND r.fecha_check_out >= $3)
                    OR (r.fecha_check_in >= $2 AND r.fecha_check_out <= $3)
                )
            """

            params = [propiedad_id, check_in, check_out]

            if exclude_reserva_id:
                reservations_query += " AND r.id != $4"
                params.append(exclude_reserva_id)

            reservations_result = await execute_query(reservations_query, *params)

            if reservations_result and reservations_result[0]['count'] > 0:
                logger.warning(
                    f"Propiedad {propiedad_id} tiene reservas confirmadas entre {check_in} y {check_out}")
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
        Calcula el precio total de una reserva basado en la tabla property_availability.

        Args:
            propiedad_id: ID de la propiedad
            check_in: Fecha de entrada
            check_out: Fecha de salida

        Returns:
            Precio total de la reserva
        """
        try:
            # Sumar precios de la tabla de disponibilidad
            query = """
                SELECT COALESCE(SUM(price_per_night), 0) as total
                FROM propiedad_disponibilidad
                WHERE propiedad_id = $1
                AND dia >= $2
                AND dia < $3
                AND disponible = TRUE
            """

            result = await execute_query(query, propiedad_id, check_in, check_out)

            if result and result[0]['total']:
                return Decimal(str(result[0]['total']))
            else:
                # Si no hay disponibilidad configurada, usar precio por defecto
                # La tabla propiedad no tiene precio_base, usar precio estándar
                num_nights = (check_out - check_in).days
                # $100 por noche por defecto
                precio_default = Decimal('100.00')
                return precio_default * num_nights

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
                "SELECT id, nombre, capacidad, anfitrion_id FROM propiedad WHERE id = $1",
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
                            propiedad_id, huesped_id, fecha_check_in, fecha_check_out,
                            monto_final, estado_reserva_id
                        )
                        VALUES ($1, $2, $3, $4, $5, $6)
                        RETURNING id
                    """

                    result = await conn.fetchrow(
                        query,
                        propiedad_id,
                        huesped_id,
                        check_in,
                        check_out,
                        total_price,
                        estado_id
                    )

                    reserva_id = result['id']
                    # Usar fecha actual ya que no retornamos fecha_creacion
                    fecha_creacion = date.today()

                    logger.info(f"Reserva {reserva_id} creada exitosamente")

                    # Marcar fechas como no disponibles en la tabla de disponibilidad
                    try:
                        await self._mark_dates_unavailable(propiedad_id, check_in, check_out)
                        logger.info(
                            f"Fechas marcadas como no disponibles para propiedad {propiedad_id}")
                    except Exception as e:
                        logger.warning(
                            f"Error marcando fechas como no disponibles: {str(e)}")
                        # No fallar la reserva por esto

            # Registrar evento en Cassandra (async, no bloquear si falla)
            await self._sync_reservation_to_cassandra(
                reserva_id=str(reserva_id),
                event_type="CREATED",
                propiedad_id=propiedad_id,
                huesped_id=str(huesped_id),
                check_in=check_in,
                check_out=check_out,
                monto_total=total_price,
                host_id=str(propiedad['anfitrion_id']),
                ciudad_id=None  # Se obtendrá automáticamente
            )

            # Sincronizar nuevas tablas de Cassandra
            await self._sync_nueva_reserva_cassandra(
                reserva_id=reserva_id,
                propiedad_id=propiedad_id,
                host_id=propiedad['anfitrion_id'],
                huesped_id=huesped_id,
                fecha_inicio=check_in,
                fecha_fin=check_out,
                precio_total=float(total_price),
                estado="confirmada"
            )

            # Crear/actualizar relación host-guest en Neo4j para análisis de comunidades
            try:
                if self.neo4j_service:
                    neo4j_result = await self.neo4j_service.create_host_guest_interaction(
                        host_user_id=propiedad['anfitrion_id'],
                        guest_user_id=huesped_id,
                        reservation_id=reserva_id,
                        reservation_date=check_in,
                        property_id=propiedad_id
                    )

                    if neo4j_result.get('success'):
                        total_interactions = neo4j_result['total_interactions']
                        logger.info(
                            f"Relación Neo4j actualizada. Total interacciones: {total_interactions}")

                        if neo4j_result.get('is_community'):
                            logger.info(
                                f"🏘️ ¡Nueva comunidad detectada! Host {propiedad['anfitrion_id']} - "
                                f"Guest {huesped_id} con {total_interactions} interacciones"
                            )
                    else:
                        logger.warning(
                            f"Error en relación Neo4j: {neo4j_result.get('error')}")

            except Exception as e:
                logger.warning(
                    f"Error creando relación Neo4j (reserva aún exitosa): {str(e)}")

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
                SELECT r.id, r.propiedad_id, r.fecha_check_in, r.fecha_check_out, er.nombre as estado
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

            # Liberar fechas en la tabla de disponibilidad
            try:
                await self._mark_dates_available(
                    propiedad_id=reserva['propiedad_id'],
                    check_in=reserva['fecha_check_in'], 
                    check_out=reserva['fecha_check_out']
                )
                logger.info(f"Fechas liberadas para propiedad {reserva['propiedad_id']}")
            except Exception as e:
                logger.warning(f"Error liberando fechas: {str(e)}")

            # Registrar evento en Cassandra
            await self._sync_reservation_to_cassandra(
                reserva_id=str(reserva_id),
                event_type="CANCELLED",
                propiedad_id=reserva['propiedad_id'],
                huesped_id=str(huesped_id),
                check_in=reserva['fecha_check_in'],
                check_out=reserva['fecha_check_out']
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

    async def _sync_nueva_reserva_cassandra(self, reserva_id: int, propiedad_id: int, 
                                          host_id: int, huesped_id: int, fecha_inicio: date, 
                                          fecha_fin: date, precio_total: float, estado: str):
        """
        Sincroniza una nueva reserva con las nuevas tablas de Cassandra.
        """
        try:
            from db.cassandra import cassandra_add_reserva, get_ciudad_id_for_propiedad
            from datetime import datetime
            
            # Obtener ciudad_id
            ciudad_id = await get_ciudad_id_for_propiedad(propiedad_id)
            if not ciudad_id:
                logger.warning(f"No se pudo obtener ciudad_id para propiedad {propiedad_id}")
                return

            # Preparar datos de la reserva
            reserva_data = {
                'reserva_id': reserva_id,
                'propiedad_id': propiedad_id,
                'host_id': host_id,
                'huesped_id': huesped_id,
                'ciudad_id': ciudad_id,
                'fecha_inicio': fecha_inicio.isoformat(),
                'fecha_fin': fecha_fin.isoformat(),
                'estado': estado,
                'precio_total': precio_total,
                'created_at': datetime.now().isoformat()
            }
            
            # Sincronizar en Cassandra
            await cassandra_add_reserva(reserva_data)
            
            logger.info(f"Reserva {reserva_id} sincronizada con tablas nuevas de Cassandra")
            
        except Exception as e:
            logger.error(f"Error sincronizando nueva reserva en Cassandra: {e}")

    async def _remove_reserva_cassandra(self, reserva_id: int, propiedad_id: int, 
                                       host_id: int, fecha_inicio: date):
        """
        Elimina una reserva de las nuevas tablas de Cassandra.
        """
        try:
            from db.cassandra import cassandra_remove_reserva, get_ciudad_id_for_propiedad
            
            # Obtener ciudad_id
            ciudad_id = await get_ciudad_id_for_propiedad(propiedad_id)
            if not ciudad_id:
                logger.warning(f"No se pudo obtener ciudad_id para propiedad {propiedad_id}")
                return

            # Preparar datos de la reserva
            reserva_data = {
                'reserva_id': reserva_id,
                'propiedad_id': propiedad_id,
                'host_id': host_id,
                'ciudad_id': ciudad_id,
                'fecha_inicio': fecha_inicio.isoformat()
            }
            
            # Eliminar de Cassandra
            await cassandra_remove_reserva(reserva_data)
            
            logger.info(f"Reserva {reserva_id} eliminada de las tablas nuevas de Cassandra")
            
        except Exception as e:
            logger.error(f"Error eliminando reserva de Cassandra: {e}")

    async def get_propiedades_disponibles_fecha(self, fecha: date, ciudad_id: int = None):
        """
        CU 4: Obtiene propiedades disponibles en una fecha específica usando Cassandra.
        """
        try:
            from db.cassandra import get_propiedades_disponibles_por_fecha
            
            propiedades = await get_propiedades_disponibles_por_fecha(fecha, ciudad_id)
            
            return {
                "success": True,
                "fecha": fecha.isoformat(),
                "ciudad_id": ciudad_id,
                "propiedades": propiedades,
                "total": len(propiedades)
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo propiedades disponibles: {e}")
            return {
                "success": False,
                "error": f"Error obteniendo propiedades: {str(e)}"
            }

    async def get_reservas_host(self, host_id: int, fecha: date):
        """
        CU 6: Obtiene reservas de un host en una fecha específica usando Cassandra.
        """
        try:
            from db.cassandra import get_reservas_por_host_fecha
            
            reservas = await get_reservas_por_host_fecha(host_id, fecha)
            
            return {
                "success": True,
                "host_id": host_id,
                "fecha": fecha.isoformat(),
                "reservas": reservas,
                "total": len(reservas)
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo reservas de host: {e}")
            return {
                "success": False,
                "error": f"Error obteniendo reservas: {str(e)}"
            }

    async def get_reservas_ciudad(self, ciudad_id: int, fecha: date):
        """
        CU 5: Obtiene reservas de una ciudad en una fecha específica usando Cassandra.
        """
        try:
            from db.cassandra import get_reservas_por_ciudad_fecha
            
            reservas = await get_reservas_por_ciudad_fecha(ciudad_id, fecha)
            
            return {
                "success": True,
                "ciudad_id": ciudad_id,
                "fecha": fecha.isoformat(),
                "reservas": reservas,
                "total": len(reservas)
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo reservas de ciudad: {e}")
            return {
                "success": False,
                "error": f"Error obteniendo reservas: {str(e)}"
            }
