"""
Utilidades para optimización de rendimiento.
"""

import asyncio
import time
from functools import wraps
from utils.logging import get_logger

logger = get_logger(__name__)


def measure_time(func_name: str = None):
    """Decorador para medir el tiempo de ejecución de funciones."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            name = func_name or func.__name__
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.info(f"⏱️ {name} ejecutado en {execution_time:.2f}s")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"❌ {name} falló en {execution_time:.2f}s: {e}")
                raise
                
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            name = func_name or func.__name__
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.info(f"⏱️ {name} ejecutado en {execution_time:.2f}s")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"❌ {name} falló en {execution_time:.2f}s: {e}")
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
            
    return decorator


async def batch_execute(tasks: list, batch_size: int = 10, delay: float = 0.1):
    """
    Ejecuta tareas en lotes para evitar sobrecarga del sistema.
    
    Args:
        tasks: Lista de corrutinas a ejecutar
        batch_size: Tamaño del lote
        delay: Delay entre lotes en segundos
        
    Returns:
        Lista de resultados
    """
    results = []
    
    for i in range(0, len(tasks), batch_size):
        batch = tasks[i:i + batch_size]
        logger.info(f"🔄 Ejecutando lote {i//batch_size + 1}/{(len(tasks)-1)//batch_size + 1} ({len(batch)} tareas)")
        
        batch_results = await asyncio.gather(*batch, return_exceptions=True)
        results.extend(batch_results)
        
        # Pequeño delay entre lotes
        if i + batch_size < len(tasks):
            await asyncio.sleep(delay)
    
    return results


class PerformanceStats:
    """Clase para recopilar estadísticas de rendimiento."""
    
    def __init__(self):
        self.stats = {}
        
    def record(self, operation: str, duration: float, success: bool = True):
        """Registra estadísticas de una operación."""
        if operation not in self.stats:
            self.stats[operation] = {
                'total_calls': 0,
                'total_time': 0,
                'successes': 0,
                'failures': 0,
                'avg_time': 0
            }
        
        stats = self.stats[operation]
        stats['total_calls'] += 1
        stats['total_time'] += duration
        
        if success:
            stats['successes'] += 1
        else:
            stats['failures'] += 1
            
        stats['avg_time'] = stats['total_time'] / stats['total_calls']
    
    def get_summary(self) -> dict:
        """Obtiene un resumen de las estadísticas."""
        return self.stats
    
    def print_summary(self):
        """Imprime un resumen de las estadísticas."""
        logger.info("📊 ESTADÍSTICAS DE RENDIMIENTO:")
        for operation, stats in self.stats.items():
            success_rate = (stats['successes'] / stats['total_calls']) * 100
            logger.info(f"  • {operation}:")
            logger.info(f"    - Llamadas: {stats['total_calls']}")
            logger.info(f"    - Tiempo promedio: {stats['avg_time']:.2f}s")
            logger.info(f"    - Tasa de éxito: {success_rate:.1f}%")


# Instancia global para estadísticas
perf_stats = PerformanceStats()