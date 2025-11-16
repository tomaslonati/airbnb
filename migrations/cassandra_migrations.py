"""
Migraciones para AstraDB/Cassandra.
"""

from migrations.base import BaseMigration
from db import cassandra
from utils.logging import get_logger

logger = get_logger(__name__)


class Migration001CreateReservationEvents(BaseMigration):
    """Crea tabla de eventos de reservas."""

    def __init__(self):
        super().__init__("001", "Crear tabla reservation_events")

    async def up(self):
        """Crear tabla reservation_events."""
        query = """
            CREATE TABLE IF NOT EXISTS reservation_events (
                reservation_id UUID,
                event_time TIMESTAMP,
                event_type TEXT,
                property_id UUID,
                user_id UUID,
                check_in DATE,
                check_out DATE,
                metadata MAP<TEXT, TEXT>,
                PRIMARY KEY (reservation_id, event_time)
            ) WITH CLUSTERING ORDER BY (event_time DESC);
        """

        await cassandra.execute_query(query)
        logger.info("Tabla reservation_events creada")

    async def down(self):
        """Eliminar tabla reservation_events."""
        await cassandra.execute_query("DROP TABLE IF EXISTS reservation_events;")
        logger.info("Tabla reservation_events eliminada")


class Migration002CreateUserActivity(BaseMigration):
    """Crea tabla de actividad de usuarios."""

    def __init__(self):
        super().__init__("002", "Crear tabla user_activity")

    async def up(self):
        """Crear tabla user_activity."""
        query = """
            CREATE TABLE IF NOT EXISTS user_activity (
                user_id UUID,
                activity_date DATE,
                activity_time TIMESTAMP,
                activity_type TEXT,
                resource_id UUID,
                resource_type TEXT,
                ip_address INET,
                user_agent TEXT,
                session_id UUID,
                PRIMARY KEY ((user_id, activity_date), activity_time)
            ) WITH CLUSTERING ORDER BY (activity_time DESC);
        """

        await cassandra.execute_query(query)
        logger.info("Tabla user_activity creada")

    async def down(self):
        """Eliminar tabla user_activity."""
        await cassandra.execute_query("DROP TABLE IF EXISTS user_activity;")
        logger.info("Tabla user_activity eliminada")


class Migration003CreateSearchLogs(BaseMigration):
    """Crea tabla de logs de búsquedas."""

    def __init__(self):
        super().__init__("003", "Crear tabla search_logs")

    async def up(self):
        """Crear tabla search_logs."""
        query = """
            CREATE TABLE IF NOT EXISTS search_logs (
                search_date DATE,
                search_time TIMESTAMP,
                user_id UUID,
                search_query TEXT,
                city TEXT,
                check_in DATE,
                check_out DATE,
                guests INT,
                max_price DECIMAL,
                results_count INT,
                search_duration_ms INT,
                PRIMARY KEY (search_date, search_time)
            ) WITH CLUSTERING ORDER BY (search_time DESC);
        """

        await cassandra.execute_query(query)
        logger.info("Tabla search_logs creada")

    async def down(self):
        """Eliminar tabla search_logs."""
        await cassandra.execute_query("DROP TABLE IF EXISTS search_logs;")
        logger.info("Tabla search_logs eliminada")


class Migration004CreatePropertyMetrics(BaseMigration):
    """Crea tabla de métricas de propiedades por día."""

    def __init__(self):
        super().__init__("004", "Crear tabla property_daily_metrics")

    async def up(self):
        """Crear tabla property_daily_metrics."""
        query = """
            CREATE TABLE IF NOT EXISTS property_daily_metrics (
                property_id UUID,
                metric_date DATE,
                views INT,
                searches INT,
                bookings INT,
                revenue DECIMAL,
                avg_rating DECIMAL,
                occupancy_rate DECIMAL,
                PRIMARY KEY (property_id, metric_date)
            ) WITH CLUSTERING ORDER BY (metric_date DESC);
        """

        await cassandra.execute_query(query)
        logger.info("Tabla property_daily_metrics creada")

    async def down(self):
        """Eliminar tabla property_daily_metrics."""
        await cassandra.execute_query("DROP TABLE IF EXISTS property_daily_metrics;")
        logger.info("Tabla property_daily_metrics eliminada")

class Migration005CreatePropertiesByCity(BaseMigration):
    """
    Crea la tabla de búsqueda (Query Table) para propiedades por ciudad y capacidad.
    Esta es la tabla "craneada" para tu caso de uso.
    """
    
    def __init__(self):
        super().__init__("005", "Crear tabla properties_by_city_and_capacity")

    async def up(self):
        """Crear tabla properties_by_city_and_capacity y poblarla."""
        logger.info("Ejecutando migración 005: Creando 'properties_by_city_and_capacity'...")
        
        # 1. EL DDL (CREATE TABLE)
        # La estructura de la tabla diseñada para tu consulta.
        create_table_query = """
            CREATE TABLE IF NOT EXISTS properties_by_city_and_capacity (
                ciudad_nombre text,
                capacidad int,
                propiedad_id int,
                nombre_propiedad text,
                
                -- CLAVE PRIMARIA:
                PRIMARY KEY ((ciudad_nombre), capacidad, propiedad_id)
            );
        """
        
        await cassandra.execute_query(create_table_query)
        logger.info("Tabla 'properties_by_city_and_capacity' creada exitosamente.")
        
        
        logger.info("Poblando 'properties_by_city_and_capacity' con datos de Postgres...")
        
        inserts = [
            """
            INSERT INTO properties_by_city_and_capacity (ciudad_nombre, capacidad, propiedad_id, nombre_propiedad) 
            VALUES ('Buenos Aires', 4, 26, 'casa con pileta');
            """,
            """
            INSERT INTO properties_by_city_and_capacity (ciudad_nombre, capacidad, propiedad_id, nombre_propiedad) 
            VALUES ('Buenos Aires', 4, 24, 'depto en Palermo');
            """,
            """
            INSERT INTO properties_by_city_and_capacity (ciudad_nombre, capacidad, propiedad_id, nombre_propiedad) 
            VALUES ('Buenos Aires', 3, 25, 'monoambiente en el centro');
            """
        ]
        
        for query in inserts:
            # Usamos el mismo método 'execute_query' que SÍ funciona
            # cuando es llamado desde main.py
            await cassandra.execute_query(query)

        logger.info(f"¡Éxito! {len(inserts)} registros insertados en 'properties_by_city_and_capacity'.")


    async def down(self):
        """Eliminar tabla properties_by_city_and_capacity."""
        await cassandra.execute_query("DROP TABLE IF EXISTS properties_by_city_and_capacity;")
        logger.info("Tabla 'properties_by_city_and_capacity' eliminada")
        

