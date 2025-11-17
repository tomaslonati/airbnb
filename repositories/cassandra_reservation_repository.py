"""
Repositorio de Cassandra para sincronización de reservas.
Maneja las tablas:
- ocupacion_por_ciudad
- propiedades_disponibles_por_fecha  
- reservas_por_host_fecha
"""

import asyncio
from datetime import date, timedelta
from typing import Optional, List, Any
from decimal import Decimal
from uuid import UUID
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra import ConsistencyLevel
from cassandra.policies import DCAwareRoundRobinPolicy
from config import db_config
from utils.logging import get_logger
from utils.retry import retry_on_connection_error

logger = get_logger(__name__)


class CassandraReservationRepository:
    """Repositorio para sincronización de datos de reservas en Cassandra."""
    
    def __init__(self):
        self.cluster = None
        self.session = None
        self.keyspace = "default_keyspace"
        
        # Prepared statements para mejor performance
        self._prepared_statements = {}
        
    def connect(self):
        """Establece conexión con Cassandra."""
        try:
            if self.session and not self.session.is_shutdown:
                return self.session
                
            # Configurar autenticación
            auth_provider = PlainTextAuthProvider(
                username=db_config.cassandra_username,
                password=db_config.cassandra_password
            )
            
            # Configurar cluster
            self.cluster = Cluster(
                contact_points=[db_config.cassandra_host],
                port=db_config.cassandra_port,
                auth_provider=auth_provider,
                load_balancing_policy=DCAwareRoundRobinPolicy()
            )
            
            # Conectar
            self.session = self.cluster.connect()
            self.session.set_keyspace(self.keyspace)
            
            # Configurar consistency level
            self.session.default_consistency_level = ConsistencyLevel.LOCAL_QUORUM
            
            logger.info(f"✅ Conectado a Cassandra keyspace: {self.keyspace}")
            
            # Preparar statements
            self._prepare_statements()
            
            return self.session
            
        except Exception as e:
            logger.error(f"❌ Error conectando a Cassandra: {e}")
            raise
    
    def _prepare_statements(self):
        """Prepara los statements CQL para mejor performance."""
        try:
            statements = {
                # Ocupación por ciudad
                'update_occupancy': """
                    UPDATE ocupacion_por_ciudad 
                    SET noches_ocupadas = noches_ocupadas + ?,
                        noches_disponibles = noches_disponibles + ?
                    WHERE ciudad_id = ? AND fecha = ?
                """,
                
                'init_occupancy': """
                    INSERT INTO ocupacion_por_ciudad (ciudad_id, fecha, noches_ocupadas, noches_disponibles)
                    VALUES (?, ?, ?, ?)
                    IF NOT EXISTS
                """,
                
                # Disponibilidad por fecha
                'update_availability': """
                    INSERT INTO propiedades_disponibles_por_fecha (fecha, propiedad_id, disponible, created_at)
                    VALUES (?, ?, ?, toTimestamp(now()))
                """,
                
                # Reservas por host
                'insert_host_reservation': """
                    INSERT INTO reservas_por_host_fecha 
                    (host_id, fecha, reserva_id, propiedad_id, huesped_id, monto_total, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, toTimestamp(now()))
                """,
                
                'delete_host_reservation': """
                    DELETE FROM reservas_por_host_fecha 
                    WHERE host_id = ? AND fecha = ? AND reserva_id = ?
                """
            }
            
            for name, cql in statements.items():
                self._prepared_statements[name] = self.session.prepare(cql)
                
            logger.info(f"✅ Preparados {len(statements)} statements CQL")
            
        except Exception as e:
            logger.error(f"❌ Error preparando statements: {e}")
            raise
    
    @retry_on_connection_error(max_attempts=3)
    def update_occupancy(
        self, 
        ciudad_id: int, 
        fecha: date, 
        occupied_delta: int, 
        available_delta: int
    ):
        """
        Actualiza la ocupación por ciudad para una fecha específica.
        
        Args:
            ciudad_id: ID de la ciudad
            fecha: Fecha específica
            occupied_delta: Cambio en noches ocupadas (+1 al ocupar, -1 al liberar)
            available_delta: Cambio en noches disponibles (-1 al ocupar, +1 al liberar)
        """
        try:
            session = self.connect()
            
            # Primero intentar crear el registro si no existe
            init_stmt = self._prepared_statements['init_occupancy']
            session.execute(init_stmt, [ciudad_id, fecha, 0, 1])
            
            # Luego actualizar
            update_stmt = self._prepared_statements['update_occupancy']
            session.execute(update_stmt, [occupied_delta, available_delta, ciudad_id, fecha])
            
            logger.debug(f"🏙️ Ocupación actualizada para ciudad {ciudad_id}, fecha {fecha}")
            
        except Exception as e:
            logger.error(f"❌ Error actualizando ocupación: {e}")
            # No relanzar la excepción para no romper el flujo de PostgreSQL
    
    @retry_on_connection_error(max_attempts=3)
    def update_availability(self, fecha: date, propiedad_id: int, disponible: bool):
        """
        Actualiza la disponibilidad de una propiedad en una fecha específica.
        
        Args:
            fecha: Fecha específica
            propiedad_id: ID de la propiedad
            disponible: True si está disponible, False si está ocupada
        """
        try:
            session = self.connect()
            stmt = self._prepared_statements['update_availability']
            session.execute(stmt, [fecha, propiedad_id, disponible])
            
            logger.debug(f"🏠 Disponibilidad actualizada para propiedad {propiedad_id}, fecha {fecha}: {disponible}")
            
        except Exception as e:
            logger.error(f"❌ Error actualizando disponibilidad: {e}")
            # No relanzar la excepción
    
    @retry_on_connection_error(max_attempts=3)
    def insert_host_reservation(
        self,
        host_id: str,
        fecha: date,
        reserva_id: str,
        propiedad_id: str,
        huesped_id: str,
        monto_total: Decimal
    ):
        """
        Inserta una reserva en la tabla de reservas por host.
        
        Args:
            host_id: ID del anfitrión
            fecha: Fecha de la reserva (check-in)
            reserva_id: ID de la reserva
            propiedad_id: ID de la propiedad
            huesped_id: ID del huésped
            monto_total: Monto total de la reserva
        """
        try:
            session = self.connect()
            stmt = self._prepared_statements['insert_host_reservation']
            
            # Convertir a UUID si es necesario
            host_uuid = UUID(host_id) if isinstance(host_id, str) else host_id
            reserva_uuid = UUID(reserva_id) if isinstance(reserva_id, str) else reserva_id
            propiedad_uuid = UUID(propiedad_id) if isinstance(propiedad_id, str) else propiedad_id
            huesped_uuid = UUID(huesped_id) if isinstance(huesped_id, str) else huesped_id
            
            session.execute(stmt, [
                host_uuid, fecha, reserva_uuid, propiedad_uuid, huesped_uuid, float(monto_total)
            ])
            
            logger.debug(f"📝 Reserva insertada para host {host_id}, fecha {fecha}")
            
        except Exception as e:
            logger.error(f"❌ Error insertando reserva de host: {e}")
            # No relanzar la excepción
    
    @retry_on_connection_error(max_attempts=3)
    def delete_host_reservation(self, host_id: str, fecha: date, reserva_id: str):
        """
        Elimina una reserva de la tabla de reservas por host.
        
        Args:
            host_id: ID del anfitrión
            fecha: Fecha de la reserva
            reserva_id: ID de la reserva
        """
        try:
            session = self.connect()
            stmt = self._prepared_statements['delete_host_reservation']
            
            # Convertir a UUID si es necesario
            host_uuid = UUID(host_id) if isinstance(host_id, str) else host_id
            reserva_uuid = UUID(reserva_id) if isinstance(reserva_id, str) else reserva_id
            
            session.execute(stmt, [host_uuid, fecha, reserva_uuid])
            
            logger.debug(f"🗑️ Reserva eliminada para host {host_id}, fecha {fecha}")
            
        except Exception as e:
            logger.error(f"❌ Error eliminando reserva de host: {e}")
            # No relanzar la excepción
    
    async def sync_reservation_creation(
        self,
        ciudad_id: int,
        host_id: str,
        propiedad_id: str,
        huesped_id: str,
        reserva_id: str,
        fecha_check_in: date,
        fecha_check_out: date,
        monto_total: Decimal
    ):
        """
        Sincroniza la creación de una reserva con todas las tablas de Cassandra.
        
        Args:
            ciudad_id: ID de la ciudad
            host_id: ID del anfitrión
            propiedad_id: ID de la propiedad
            huesped_id: ID del huésped
            reserva_id: ID de la reserva
            fecha_check_in: Fecha de entrada
            fecha_check_out: Fecha de salida
            monto_total: Monto total de la reserva
        """
        try:
            # Generar rango de fechas (desde check-in hasta check-out, excluyendo check-out)
            current_date = fecha_check_in
            
            while current_date < fecha_check_out:
                # 1. Actualizar ocupación por ciudad (incrementar ocupadas, decrementar disponibles)
                self.update_occupancy(ciudad_id, current_date, 1, -1)
                
                # 2. Marcar propiedad como no disponible
                self.update_availability(current_date, int(propiedad_id), False)
                
                current_date = current_date + timedelta(days=1)
            
            # 3. Insertar reserva por host (solo en fecha de check-in)
            self.insert_host_reservation(
                host_id, fecha_check_in, reserva_id, propiedad_id, huesped_id, monto_total
            )
            
            logger.info(f"✅ Reserva {reserva_id} sincronizada con Cassandra")
            
        except Exception as e:
            logger.error(f"❌ Error sincronizando creación de reserva: {e}")
    
    async def sync_reservation_cancellation(
        self,
        ciudad_id: int,
        host_id: str,
        propiedad_id: str,
        reserva_id: str,
        fecha_check_in: date,
        fecha_check_out: date
    ):
        """
        Sincroniza la cancelación de una reserva con todas las tablas de Cassandra.
        
        Args:
            ciudad_id: ID de la ciudad
            host_id: ID del anfitrión
            propiedad_id: ID de la propiedad
            reserva_id: ID de la reserva
            fecha_check_in: Fecha de entrada
            fecha_check_out: Fecha de salida
        """
        try:
            # Generar rango de fechas
            current_date = fecha_check_in
            
            while current_date < fecha_check_out:
                # 1. Actualizar ocupación por ciudad (decrementar ocupadas, incrementar disponibles)
                self.update_occupancy(ciudad_id, current_date, -1, 1)
                
                # 2. Marcar propiedad como disponible
                self.update_availability(current_date, int(propiedad_id), True)
                
                current_date = current_date + timedelta(days=1)
            
            # 3. Eliminar reserva por host
            self.delete_host_reservation(host_id, fecha_check_in, reserva_id)
            
            logger.info(f"✅ Cancelación de reserva {reserva_id} sincronizada con Cassandra")
            
        except Exception as e:
            logger.error(f"❌ Error sincronizando cancelación de reserva: {e}")
    
    async def sync_availability_generation(
        self,
        ciudad_id: int,
        propiedad_id: int,
        fecha_inicio: date,
        dias: int
    ):
        """
        Sincroniza la generación inicial de disponibilidad.
        
        Args:
            ciudad_id: ID de la ciudad
            propiedad_id: ID de la propiedad
            fecha_inicio: Fecha de inicio
            dias: Número de días a generar
        """
        try:
            current_date = fecha_inicio
            
            for _ in range(dias):
                # 1. Incrementar noches disponibles en ocupación por ciudad
                self.update_occupancy(ciudad_id, current_date, 0, 1)
                
                # 2. Marcar propiedad como disponible
                self.update_availability(current_date, propiedad_id, True)
                
                current_date = current_date + timedelta(days=1)
            
            logger.info(f"✅ Disponibilidad generada para propiedad {propiedad_id}, {dias} días")
            
        except Exception as e:
            logger.error(f"❌ Error sincronizando generación de disponibilidad: {e}")
    
    def close(self):
        """Cierra la conexión con Cassandra."""
        try:
            if self.session and not self.session.is_shutdown:
                self.session.shutdown()
            if self.cluster:
                self.cluster.shutdown()
                
            logger.info("🔌 Conexión con Cassandra cerrada")
            
        except Exception as e:
            logger.error(f"❌ Error cerrando conexión con Cassandra: {e}")


# Instancia global del repositorio
_cassandra_repo: Optional[CassandraReservationRepository] = None


async def get_cassandra_reservation_repository() -> CassandraReservationRepository:
    """Obtiene la instancia global del repositorio de Cassandra."""
    global _cassandra_repo
    
    if _cassandra_repo is None:
        _cassandra_repo = CassandraReservationRepository()
        _cassandra_repo.connect()  # Cambiar a síncrono
    
    return _cassandra_repo