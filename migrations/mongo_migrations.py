"""
Migraciones para MongoDB Atlas.
"""

from migrations.base import BaseMigration
from db import mongo
from utils.logging import get_logger

logger = get_logger(__name__)


class Migration001CreateCollections(BaseMigration):
    """Crea colecciones e índices principales."""

    def __init__(self):
        super().__init__("001", "Crear colecciones principales")

    async def up(self):
        """Crear colecciones e índices."""
        database = await mongo.get_database()

        # Crear colección de métricas de reservas
        reservations_metrics = database.reservations_metrics

        # Índices para métricas de reservas
        await reservations_metrics.create_index([("created_at", -1)])
        await reservations_metrics.create_index([("city", 1), ("created_at", -1)])
        await reservations_metrics.create_index([("status", 1), ("created_at", -1)])
        await reservations_metrics.create_index([("property_id", 1), ("created_at", -1)])

        # Crear colección de análisis de búsquedas
        search_analytics = database.search_analytics

        # Índices para análisis de búsquedas
        await search_analytics.create_index([("date", -1)])
        await search_analytics.create_index([("city", 1), ("date", -1)])
        await search_analytics.create_index([("search_terms", "text")])

        # Crear colección de métricas de rendimiento
        performance_metrics = database.performance_metrics

        # Índices para métricas de rendimiento
        await performance_metrics.create_index([("timestamp", -1)])
        await performance_metrics.create_index([("metric_type", 1), ("timestamp", -1)])

        logger.info("Colecciones e índices creados en MongoDB")

    async def down(self):
        """Eliminar colecciones."""
        database = await mongo.get_database()

        collections_to_drop = [
            "reservations_metrics",
            "search_analytics",
            "performance_metrics"
        ]

        for collection_name in collections_to_drop:
            await database.drop_collection(collection_name)

        logger.info("Colecciones eliminadas de MongoDB")


class Migration002CreateAggregatedReports(BaseMigration):
    """Crea colecciones para reportes agregados."""

    def __init__(self):
        super().__init__("002", "Crear colecciones de reportes")

    async def up(self):
        """Crear colecciones de reportes."""
        database = await mongo.get_database()

        # Reportes diarios
        daily_reports = database.daily_reports
        await daily_reports.create_index([("date", -1)])
        await daily_reports.create_index([("report_type", 1), ("date", -1)])

        # Reportes mensuales
        monthly_reports = database.monthly_reports
        await monthly_reports.create_index([("year", -1), ("month", -1)])
        await monthly_reports.create_index([("report_type", 1), ("year", -1), ("month", -1)])

        # KPIs en tiempo real
        real_time_kpis = database.real_time_kpis
        await real_time_kpis.create_index([("updated_at", -1)])
        await real_time_kpis.create_index([("kpi_type", 1)])

        logger.info("Colecciones de reportes creadas")

    async def down(self):
        """Eliminar colecciones de reportes."""
        database = await mongo.get_database()

        collections_to_drop = [
            "daily_reports",
            "monthly_reports",
            "real_time_kpis"
        ]

        for collection_name in collections_to_drop:
            await database.drop_collection(collection_name)

        logger.info("Colecciones de reportes eliminadas")


class Migration003CreateUserBehaviorAnalytics(BaseMigration):
    """Crea colecciones para análisis de comportamiento de usuarios."""

    def __init__(self):
        super().__init__("003", "Crear análisis de comportamiento")

    async def up(self):
        """Crear colecciones de análisis de comportamiento."""
        database = await mongo.get_database()

        # Sesiones de usuario
        user_sessions = database.user_sessions
        await user_sessions.create_index([("user_id", 1), ("start_time", -1)])
        await user_sessions.create_index([("start_time", -1)])
        await user_sessions.create_index([("session_id", 1)])

        # Patrones de búsqueda
        search_patterns = database.search_patterns
        await search_patterns.create_index([("user_id", 1)])
        await search_patterns.create_index([("pattern_type", 1), ("created_at", -1)])

        # Segmentación de usuarios
        user_segments = database.user_segments
        await user_segments.create_index([("user_id", 1)])
        await user_segments.create_index([("segment_name", 1)])
        await user_segments.create_index([("last_updated", -1)])

        logger.info("Colecciones de análisis de comportamiento creadas")

    async def down(self):
        """Eliminar colecciones de análisis de comportamiento."""
        database = await mongo.get_database()

        collections_to_drop = [
            "user_sessions",
            "search_patterns",
            "user_segments"
        ]

        for collection_name in collections_to_drop:
            await database.drop_collection(collection_name)

        logger.info("Colecciones de análisis de comportamiento eliminadas")
