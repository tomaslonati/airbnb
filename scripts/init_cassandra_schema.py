"""
Script para crear las tablas CQL de Cassandra necesarias para el sistema de reservas.

Tablas a crear:
1. ocupacion_por_ciudad - Métricas de ocupación por ciudad y fecha
2. propiedades_disponibles_por_fecha - Disponibilidad de propiedades por fecha  
3. reservas_por_host_fecha - Reservas organizadas por host y fecha
"""

import asyncio
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra import ConsistencyLevel
from config import db_config
from utils.logging import get_logger

logger = get_logger(__name__)


class CassandraSchemaInitializer:
    """Inicializa el schema de Cassandra para el sistema de reservas."""

    def __init__(self):
        self.cluster = None
        self.session = None
        self.keyspace = "default_keyspace"

    async def connect(self):
        """Conecta con Cassandra."""
        try:
            auth_provider = PlainTextAuthProvider(
                username=db_config.cassandra_username,
                password=db_config.cassandra_password
            )

            self.cluster = Cluster(
                contact_points=[db_config.cassandra_host],
                port=db_config.cassandra_port,
                auth_provider=auth_provider
            )

            self.session = self.cluster.connect()
            logger.info(
                f"✅ Conectado a Cassandra en {db_config.cassandra_host}:{db_config.cassandra_port}")

        except Exception as e:
            logger.error(f"❌ Error conectando a Cassandra: {e}")
            raise

    async def create_keyspace(self):
        """Crea el keyspace si no existe."""
        try:
            cql = f"""
                CREATE KEYSPACE IF NOT EXISTS {self.keyspace}
                WITH REPLICATION = {{
                    'class': 'SimpleStrategy',
                    'replication_factor': 3
                }}
            """

            self.session.execute(cql)
            self.session.set_keyspace(self.keyspace)

            logger.info(f"✅ Keyspace '{self.keyspace}' creado/verificado")

        except Exception as e:
            logger.error(f"❌ Error creando keyspace: {e}")
            raise

    async def create_tables(self):
        """Crea todas las tablas necesarias."""
        tables = [
            self._get_ocupacion_por_ciudad_cql(),
            self._get_propiedades_disponibles_por_fecha_cql(),
            self._get_reservas_por_host_fecha_cql()
        ]

        for table_name, cql in tables:
            try:
                self.session.execute(cql)
                logger.info(f"✅ Tabla '{table_name}' creada/verificada")
            except Exception as e:
                logger.error(f"❌ Error creando tabla '{table_name}': {e}")
                raise

    def _get_ocupacion_por_ciudad_cql(self):
        """CQL para crear la tabla de ocupación por ciudad."""
        return "ocupacion_por_ciudad", """
            CREATE TABLE IF NOT EXISTS ocupacion_por_ciudad (
                ciudad_id bigint,
                fecha date,
                noches_ocupadas int,
                noches_disponibles int,
                PRIMARY KEY (ciudad_id, fecha)
            ) WITH CLUSTERING ORDER BY (fecha ASC)
            AND comment = 'Datos agregados de ocupación: una fila por (ciudad, fecha)'
        """

    def _get_propiedades_disponibles_por_fecha_cql(self):
        """CQL para crear la tabla de disponibilidad de propiedades."""
        return "propiedades_disponibles_por_fecha", """
            CREATE TABLE IF NOT EXISTS propiedades_disponibles_por_fecha (
                fecha date,
                propiedad_id int,
                disponible boolean,
                created_at timestamp,
                PRIMARY KEY (fecha, propiedad_id)
            ) WITH CLUSTERING ORDER BY (propiedad_id ASC)
            AND comment = 'Estado de disponibilidad de propiedades por fecha específica'
        """

    def _get_reservas_por_host_fecha_cql(self):
        """CQL para crear la tabla de reservas por host."""
        return "reservas_por_host_fecha", """
            CREATE TABLE IF NOT EXISTS reservas_por_host_fecha (
                host_id uuid,
                fecha date,
                reserva_id uuid,
                propiedad_id uuid,
                huesped_id uuid,
                monto_total double,
                created_at timestamp,
                PRIMARY KEY (host_id, fecha, reserva_id)
            ) WITH CLUSTERING ORDER BY (fecha DESC, reserva_id ASC)
            AND comment = 'Reservas organizadas por anfitrión y fecha para análisis'
        """

    async def close(self):
        """Cierra la conexión."""
        try:
            if self.session:
                self.session.shutdown()
            if self.cluster:
                self.cluster.shutdown()
            logger.info("🔌 Conexión cerrada")
        except Exception as e:
            logger.error(f"❌ Error cerrando conexión: {e}")


async def initialize_cassandra_schema():
    """Función principal para inicializar el schema."""
    initializer = CassandraSchemaInitializer()

    try:
        await initializer.connect()
        await initializer.create_keyspace()
        await initializer.create_tables()

        logger.info("🎉 Schema de Cassandra inicializado exitosamente")
        print("✅ Schema de Cassandra para reservas configurado correctamente")

    except Exception as e:
        logger.error(f"❌ Error inicializando schema: {e}")
        print(f"❌ Error: {e}")
        raise

    finally:
        await initializer.close()


if __name__ == "__main__":
    print("🚀 Inicializando schema de Cassandra para sistema de reservas...")
    asyncio.run(initialize_cassandra_schema())
