"""
Gestor principal de migraciones para todas las bases de datos.
"""

import asyncio
from typing import List, Dict, Any
from migrations.base import MigrationManager
from migrations.postgres_migrations import (
    Migration001CreateUsers, Migration002CreateProperties,
    Migration003CreateReservations, Migration004CreateReviews
)
from migrations.cassandra_migrations import (
    Migration001CreateReservationEvents, Migration002CreateUserActivity,
    Migration003CreateSearchLogs, Migration004CreatePropertyMetrics
)
from migrations.mongo_migrations import (
    Migration001CreateCollections, Migration002CreateAggregatedReports,
    Migration003CreateUserBehaviorAnalytics
)
from migrations.neo4j_migrations import (
    Migration001CreateUserNodes, Migration002CreatePropertyNodes,
    Migration003CreateRelationships, Migration004CreateRecommendationGraph
)
from utils.logging import get_logger

logger = get_logger(__name__)


class DatabaseMigrationManager:
    """Gestor principal para todas las migraciones de bases de datos."""

    def __init__(self):
        self.postgres_manager = MigrationManager()
        self.cassandra_manager = MigrationManager()
        self.mongo_manager = MigrationManager()
        self.neo4j_manager = MigrationManager()

        self._register_all_migrations()

    def _register_all_migrations(self):
        """Registra todas las migraciones en sus respectivos gestores."""

        # Registrar migraciones de PostgreSQL
        postgres_migrations = [
            Migration001CreateUsers(),
            Migration002CreateProperties(),
            Migration003CreateReservations(),
            Migration004CreateReviews()
        ]

        for migration in postgres_migrations:
            self.postgres_manager.register_migration(migration)

        # Registrar migraciones de Cassandra
        cassandra_migrations = [
            Migration001CreateReservationEvents(),
            Migration002CreateUserActivity(),
            Migration003CreateSearchLogs(),
            Migration004CreatePropertyMetrics()
        ]

        for migration in cassandra_migrations:
            self.cassandra_manager.register_migration(migration)

        # Registrar migraciones de MongoDB
        mongo_migrations = [
            Migration001CreateCollections(),
            Migration002CreateAggregatedReports(),
            Migration003CreateUserBehaviorAnalytics()
        ]

        for migration in mongo_migrations:
            self.mongo_manager.register_migration(migration)

        # Registrar migraciones de Neo4j
        neo4j_migrations = [
            Migration001CreateUserNodes(),
            Migration002CreatePropertyNodes(),
            Migration003CreateRelationships(),
            Migration004CreateRecommendationGraph()
        ]

        for migration in neo4j_migrations:
            self.neo4j_manager.register_migration(migration)

        logger.info("Todas las migraciones registradas")

    async def migrate_all_databases(self):
        """Ejecuta todas las migraciones en todas las bases de datos."""
        logger.info("Iniciando migraciones en todas las bases de datos")

        try:
            # Ejecutar migraciones en paralelo para mayor eficiencia
            await asyncio.gather(
                self._migrate_postgres(),
                self._migrate_cassandra(),
                self._migrate_mongo(),
                self._migrate_neo4j(),
                return_exceptions=True
            )

            logger.info("Todas las migraciones completadas exitosamente")

        except Exception as e:
            logger.error("Error ejecutando migraciones", error=str(e))
            raise

    async def _migrate_postgres(self):
        """Ejecuta migraciones de PostgreSQL."""
        try:
            logger.info("Iniciando migraciones PostgreSQL")
            await self.postgres_manager.run_migrations()
            logger.info("Migraciones PostgreSQL completadas")
        except Exception as e:
            logger.error("Error en migraciones PostgreSQL", error=str(e))
            raise

    async def _migrate_cassandra(self):
        """Ejecuta migraciones de Cassandra."""
        try:
            logger.info("Iniciando migraciones Cassandra")
            await self.cassandra_manager.run_migrations()
            logger.info("Migraciones Cassandra completadas")
        except Exception as e:
            logger.error("Error en migraciones Cassandra", error=str(e))
            raise

    async def _migrate_mongo(self):
        """Ejecuta migraciones de MongoDB."""
        try:
            logger.info("Iniciando migraciones MongoDB")
            await self.mongo_manager.run_migrations()
            logger.info("Migraciones MongoDB completadas")
        except Exception as e:
            logger.error("Error en migraciones MongoDB", error=str(e))
            raise

    async def _migrate_neo4j(self):
        """Ejecuta migraciones de Neo4j."""
        try:
            logger.info("Iniciando migraciones Neo4j")
            await self.neo4j_manager.run_migrations()
            logger.info("Migraciones Neo4j completadas")
        except Exception as e:
            logger.error("Error en migraciones Neo4j", error=str(e))
            raise

    async def get_migration_status_all(self) -> Dict[str, Any]:
        """Obtiene el estado de migraciones de todas las bases de datos."""
        return {
            'postgres': self.postgres_manager.get_migration_status(),
            'cassandra': self.cassandra_manager.get_migration_status(),
            'mongodb': self.mongo_manager.get_migration_status(),
            'neo4j': self.neo4j_manager.get_migration_status()
        }

    async def rollback_all_databases(self, version: str):
        """Revierte migraciones en todas las bases de datos."""
        logger.warning(
            "Iniciando rollback en todas las bases de datos", version=version)

        try:
            await asyncio.gather(
                self.postgres_manager.rollback_migration(version),
                self.cassandra_manager.rollback_migration(version),
                self.mongo_manager.rollback_migration(version),
                self.neo4j_manager.rollback_migration(version),
                return_exceptions=True
            )

            logger.info("Rollback completado", version=version)

        except Exception as e:
            logger.error("Error en rollback", version=version, error=str(e))
            raise


# Instancia global del gestor de migraciones
migration_manager = DatabaseMigrationManager()
