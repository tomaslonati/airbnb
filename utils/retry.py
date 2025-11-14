"""
Utilidades para reintentos con tenacity.
"""

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from utils.logging import get_logger
import asyncio

logger = get_logger(__name__)


def retry_on_connection_error(max_attempts: int = 3, base_wait: float = 1.0):
    """Decorador para reintentar operaciones de base de datos."""
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=base_wait, min=1, max=10),
        retry=retry_if_exception_type(
            (ConnectionError, OSError, asyncio.TimeoutError)),
        reraise=True,
        before_sleep=lambda retry_state: logger.warning(
            "Reintentando operación",
            attempt=retry_state.attempt_number,
            outcome=str(retry_state.outcome)
        )
    )


async def safe_execute(func, *args, **kwargs):
    """Ejecuta una función de manera segura con logging de errores."""
    try:
        result = await func(*args, **kwargs)
        logger.info("Operación ejecutada exitosamente", function=func.__name__)
        return result
    except Exception as e:
        logger.error(
            "Error en operación",
            function=func.__name__,
            error=str(e),
            error_type=type(e).__name__
        )
        raise
