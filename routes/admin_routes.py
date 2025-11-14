"""
Rutas de administración y mantenimiento del sistema.
"""

from typing import Dict, Any
from routes.base import BaseRoute
from migrations.manager import migration_manager
from utils.logging import get_logger

logger = get_logger(__name__)


class DatabaseStatusRoute(BaseRoute):
    """Ruta para verificar estado de las bases de datos."""

    def __init__(self):
        super().__init__(
            name="database_status",
            description="Verifica el estado de conexión de todas las bases de datos"
        )

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Verifica estado de las bases de datos."""
        status_results = {}

        # PostgreSQL
        try:
            from db import postgres
            # Intentar obtener el cliente para verificar conexión
            await postgres.get_client()
            status_results['postgres'] = {'status': 'connected', 'error': None}
        except Exception as e:
            status_results['postgres'] = {'status': 'error', 'error': str(e)}

        # MongoDB
        try:
            from db import mongo
            await mongo.get_client()
            status_results['mongodb'] = {'status': 'connected', 'error': None}
        except Exception as e:
            status_results['mongodb'] = {'status': 'error', 'error': str(e)}

        # Cassandra
        try:
            from db import cassandra
            await cassandra.get_client()
            status_results['cassandra'] = {
                'status': 'connected', 'error': None}
        except Exception as e:
            status_results['cassandra'] = {'status': 'error', 'error': str(e)}

        # Neo4j
        try:
            from db import neo4j
            await neo4j.get_client()
            status_results['neo4j'] = {'status': 'connected', 'error': None}
        except Exception as e:
            status_results['neo4j'] = {'status': 'error', 'error': str(e)}

        # Redis
        try:
            from db import redisdb
            await redisdb.get_client()
            status_results['redis'] = {'status': 'connected', 'error': None}
        except Exception as e:
            status_results['redis'] = {'status': 'error', 'error': str(e)}

        # Resumen general
        connected_count = sum(
            1 for db in status_results.values() if db['status'] == 'connected')
        total_databases = len(status_results)

        return {
            'overall_status': 'healthy' if connected_count == total_databases else 'partial' if connected_count > 0 else 'critical',
            'connected_databases': connected_count,
            'total_databases': total_databases,
            'database_details': status_results
        }


class MigrationStatusRoute(BaseRoute):
    """Ruta para verificar estado de las migraciones."""

    def __init__(self):
        super().__init__(
            name="migration_status",
            description="Obtiene el estado de las migraciones en todas las bases de datos"
        )

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Obtiene estado de las migraciones."""
        migration_status = await migration_manager.get_migration_status_all()

        # Calcular resumen
        total_migrations = sum(db['total_migrations']
                               for db in migration_status.values())
        executed_migrations = sum(db['executed_migrations']
                                  for db in migration_status.values())
        pending_migrations = sum(db['pending_migrations']
                                 for db in migration_status.values())

        return {
            'migration_summary': {
                'total_migrations': total_migrations,
                'executed_migrations': executed_migrations,
                'pending_migrations': pending_migrations,
                'completion_percentage': round((executed_migrations / total_migrations * 100) if total_migrations > 0 else 0, 2)
            },
            'database_details': migration_status
        }


class RunMigrationsRoute(BaseRoute):
    """Ruta para ejecutar migraciones."""

    def __init__(self):
        super().__init__(
            name="run_migrations",
            description="Ejecuta todas las migraciones pendientes"
        )

    async def validate_params(self, params: Dict[str, Any]) -> bool:
        """Valida parámetros para ejecutar migraciones."""
        # Verificar que se confirme explícitamente
        if not params.get('confirmed', False):
            logger.warning("Migraciones requieren confirmación explícita")
            return False

        return True

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta las migraciones."""
        try:
            await migration_manager.migrate_all_databases()

            # Obtener estado actualizado
            final_status = await migration_manager.get_migration_status_all()

            return {
                'migrations_executed': True,
                'final_status': final_status
            }

        except Exception as e:
            logger.error("Error ejecutando migraciones", error=str(e))
            return {
                'migrations_executed': False,
                'error': str(e)
            }


class SystemHealthRoute(BaseRoute):
    """Ruta para verificar salud general del sistema."""

    def __init__(self):
        super().__init__(
            name="system_health",
            description="Verificación completa de salud del sistema"
        )

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta verificación de salud del sistema."""
        health_checks = {}

        # Verificar configuración
        try:
            from config import db_config, app_config
            health_checks['configuration'] = {
                'status': 'ok',
                'app_name': app_config.app_name,
                'debug_mode': app_config.debug,
                'log_level': app_config.log_level
            }
        except Exception as e:
            health_checks['configuration'] = {
                'status': 'error', 'error': str(e)}

        # Verificar servicios
        try:
            from services.search import SearchService
            from services.reservations import ReservationService
            from services.analytics import AnalyticsService

            search_service = SearchService()
            reservation_service = ReservationService()
            analytics_service = AnalyticsService()

            health_checks['services'] = {
                'status': 'ok',
                'loaded_services': ['SearchService', 'ReservationService', 'AnalyticsService']
            }
        except Exception as e:
            health_checks['services'] = {'status': 'error', 'error': str(e)}

        # Verificar utilidades
        try:
            from utils.logging import get_logger
            from utils.retry import retry_on_connection_error

            test_logger = get_logger('health_check')
            test_logger.info("Health check ejecutado")

            health_checks['utilities'] = {'status': 'ok'}
        except Exception as e:
            health_checks['utilities'] = {'status': 'error', 'error': str(e)}

        # Calcular estado general
        ok_checks = sum(1 for check in health_checks.values()
                        if check['status'] == 'ok')
        total_checks = len(health_checks)

        overall_status = 'healthy' if ok_checks == total_checks else 'degraded' if ok_checks > 0 else 'critical'

        return {
            'overall_health': overall_status,
            'checks_passed': ok_checks,
            'total_checks': total_checks,
            'health_details': health_checks
        }


class ClearAllCachesRoute(BaseRoute):
    """Ruta para limpiar todos los caches del sistema."""

    def __init__(self):
        super().__init__(
            name="clear_all_caches",
            description="Limpia todos los caches de Redis"
        )

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Limpia todos los caches."""
        try:
            from services.search import SearchService

            search_service = SearchService()
            await search_service.clear_cache()  # Sin ciudad específica = limpiar todo

            return {
                'caches_cleared': True,
                'cleared_types': ['search_cache']
            }

        except Exception as e:
            return {
                'caches_cleared': False,
                'error': str(e)
            }
