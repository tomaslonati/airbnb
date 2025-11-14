"""
Punto de entrada principal del CLI.
"""

import typer
import asyncio
import signal
import sys
from utils.logging import configure_logging, get_logger
from cli.commands import app as cli_app

# Configurar logging al inicio
configure_logging()
logger = get_logger(__name__)


def signal_handler(signum, frame):
    """Manejador de señales para cierre limpio."""
    logger.info("Recibida señal de interrupción, cerrando aplicación...")

    # Aquí podrías agregar lógica de limpieza de conexiones
    # Por ejemplo:
    # asyncio.run(cleanup_connections())

    sys.exit(0)


def main():
    """Función principal del CLI."""

    # Registrar manejadores de señales
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("Iniciando Airbnb Backend CLI")

    try:
        # Ejecutar la aplicación Typer
        cli_app()
    except KeyboardInterrupt:
        logger.info("Aplicación interrumpida por el usuario")
        sys.exit(0)
    except Exception as e:
        logger.error("Error fatal en la aplicación", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
