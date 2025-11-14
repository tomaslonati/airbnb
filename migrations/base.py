"""
Base para gestión de migraciones de esquemas.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from utils.logging import get_logger

logger = get_logger(__name__)


class BaseMigration(ABC):
    """Clase base para todas las migraciones."""

    def __init__(self, version: str, description: str):
        self.version = version
        self.description = description
        self.executed_at = None

    @abstractmethod
    async def up(self):
        """Aplicar la migración."""
        pass

    @abstractmethod
    async def down(self):
        """Revertir la migración."""
        pass

    def __str__(self):
        return f"Migration {self.version}: {self.description}"


class MigrationManager:
    """Gestor principal de migraciones."""

    def __init__(self):
        self.migrations: List[BaseMigration] = []
        self.executed_migrations: Dict[str, Any] = {}

    def register_migration(self, migration: BaseMigration):
        """Registra una nueva migración."""
        self.migrations.append(migration)
        logger.info("Migración registrada", version=migration.version)

    async def run_migrations(self, target_version: str = None):
        """Ejecuta las migraciones pendientes."""
        logger.info("Iniciando proceso de migraciones")

        # Ordenar migraciones por versión
        self.migrations.sort(key=lambda m: m.version)

        for migration in self.migrations:
            if target_version and migration.version > target_version:
                break

            if migration.version not in self.executed_migrations:
                try:
                    logger.info("Ejecutando migración",
                                migration=str(migration))
                    await migration.up()
                    self.executed_migrations[migration.version] = {
                        'executed_at': asyncio.get_event_loop().time(),
                        'description': migration.description
                    }
                    logger.info("Migración completada",
                                version=migration.version)

                except Exception as e:
                    logger.error("Error en migración",
                                 migration=migration.version, error=str(e))
                    raise

        logger.info("Proceso de migraciones completado")

    async def rollback_migration(self, version: str):
        """Revierte una migración específica."""
        migration = next(
            (m for m in self.migrations if m.version == version), None)

        if not migration:
            raise ValueError(f"Migración {version} no encontrada")

        if version not in self.executed_migrations:
            raise ValueError(f"Migración {version} no ha sido ejecutada")

        try:
            logger.info("Revirtiendo migración", version=version)
            await migration.down()
            del self.executed_migrations[version]
            logger.info("Migración revertida", version=version)

        except Exception as e:
            logger.error("Error revirtiendo migración",
                         version=version, error=str(e))
            raise

    def get_migration_status(self) -> Dict[str, Any]:
        """Obtiene el estado actual de las migraciones."""
        return {
            'total_migrations': len(self.migrations),
            'executed_migrations': len(self.executed_migrations),
            'pending_migrations': len(self.migrations) - len(self.executed_migrations),
            'executed_versions': list(self.executed_migrations.keys()),
            'pending_versions': [m.version for m in self.migrations if m.version not in self.executed_migrations]
        }
