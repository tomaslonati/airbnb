"""
Configuración de logging para el proyecto.
"""

import structlog
import logging
import sys
from config import app_config


def configure_logging():
    """Configura el logging estructurado con formato legible."""

    # Configuración básica de logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, app_config.log_level.upper())
    )

    # Configuración de structlog con formato legible
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(
                fmt="%H:%M:%S"),  # Solo hora:minuto:segundo
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            # Usar ConsoleRenderer en lugar de JSONRenderer para formato legible
            structlog.dev.ConsoleRenderer(
                colors=True,  # Colores para mejor legibilidad
                exception_formatter=structlog.dev.plain_traceback,
                level_styles={
                    "critical": "\033[95m",  # Magenta
                    "error": "\033[91m",     # Rojo
                    "warning": "\033[93m",   # Amarillo
                    "info": "\033[94m",      # Azul
                    "debug": "\033[92m",     # Verde
                },
                pad_event=20,  # Padding para alinear mensajes
            )
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        context_class=dict,
        cache_logger_on_first_use=True,
    )


def configure_simple_logging():
    """Configura logging simple sin colores para archivos o producción."""

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, app_config.log_level.upper())
    )

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="%H:%M:%S"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            # Formato simple sin colores
            structlog.processors.KeyValueRenderer(
                key_order=["timestamp", "level", "logger", "event"],
                drop_missing=True,
            )
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        context_class=dict,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str):
    """Obtiene un logger estructurado."""
    return structlog.get_logger(name)
