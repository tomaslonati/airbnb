"""
Base para todas las rutas/endpoints del sistema.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from utils.logging import get_logger

logger = get_logger(__name__)


class BaseRoute(ABC):
    """Clase base para todas las rutas del sistema."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta la lógica de la ruta."""
        pass

    async def validate_params(self, params: Dict[str, Any]) -> bool:
        """Valida los parámetros de entrada."""
        return True

    async def handle_error(self, error: Exception) -> Dict[str, Any]:
        """Maneja errores de la ruta."""
        logger.error("Error en ruta", route=self.name, error=str(error))
        return {
            'success': False,
            'error': str(error),
            'route': self.name
        }

    def __str__(self):
        return f"Route {self.name}: {self.description}"


class RouteRegistry:
    """Registro de todas las rutas disponibles."""

    def __init__(self):
        self.routes: Dict[str, BaseRoute] = {}

    def register_route(self, route: BaseRoute):
        """Registra una nueva ruta."""
        self.routes[route.name] = route
        logger.info("Ruta registrada", route=route.name)

    def get_route(self, name: str) -> Optional[BaseRoute]:
        """Obtiene una ruta por nombre."""
        return self.routes.get(name)

    def list_routes(self) -> Dict[str, str]:
        """Lista todas las rutas registradas."""
        return {name: route.description for name, route in self.routes.items()}

    async def execute_route(self, name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta una ruta específica."""
        route = self.get_route(name)

        if not route:
            error_msg = f"Ruta '{name}' no encontrada"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }

        try:
            # Validar parámetros
            is_valid = await route.validate_params(params)
            if not is_valid:
                return {
                    'success': False,
                    'error': 'Parámetros inválidos',
                    'route': name
                }

            # Ejecutar ruta
            logger.info("Ejecutando ruta", route=name, params=params)
            result = await route.execute(params)

            return {
                'success': True,
                'data': result,
                'route': name
            }

        except Exception as e:
            return await route.handle_error(e)


# Registro global de rutas
route_registry = RouteRegistry()
