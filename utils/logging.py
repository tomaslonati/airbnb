"""
Configuración de logging para el proyecto.
"""

import structlog
import logging
import sys
from config import app_config


def configure_logging():
    """Configura el logging estructurado."""

    # Configuración básica de logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, app_config.log_level.upper())
    )

    # Silenciar loggers verbosos de librerías externas
    logging.getLogger('astrapy').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)  
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)
    
    # Configuración de structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        context_class=dict,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str):
    """Obtiene un logger estructurado."""
    return structlog.get_logger(name)
