"""
Rutas relacionadas con búsquedas de propiedades.
"""

from typing import Dict, Any
from routes.base import BaseRoute
from services.search import SearchService
from utils.logging import get_logger

logger = get_logger(__name__)


class SearchPropertiesRoute(BaseRoute):
    """Ruta para búsqueda de propiedades."""

    def __init__(self):
        super().__init__(
            name="search_properties",
            description="Busca propiedades disponibles por ciudad y filtros"
        )
        self.search_service = SearchService()

    async def validate_params(self, params: Dict[str, Any]) -> bool:
        """Valida parámetros de búsqueda."""
        required_fields = ['city']

        for field in required_fields:
            if field not in params or not params[field]:
                logger.warning("Campo requerido faltante", field=field)
                return False

        # Validar precio máximo si está presente
        if 'max_price' in params:
            try:
                max_price = float(params['max_price'])
                if max_price <= 0:
                    logger.warning("Precio máximo debe ser positivo")
                    return False
                params['max_price'] = max_price
            except (ValueError, TypeError):
                logger.warning("Precio máximo inválido")
                return False

        return True

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta la búsqueda de propiedades."""
        city = params['city']
        max_price = params.get('max_price')
        clear_cache = params.get('clear_cache', False)

        # Limpiar cache si se solicita
        if clear_cache:
            await self.search_service.clear_cache(city)

        # Realizar búsqueda
        properties = await self.search_service.search_properties(city, max_price)

        return {
            'city': city,
            'max_price': max_price,
            'properties_found': len(properties),
            'properties': properties,
            'cache_cleared': clear_cache
        }


class ClearSearchCacheRoute(BaseRoute):
    """Ruta para limpiar el cache de búsquedas."""

    def __init__(self):
        super().__init__(
            name="clear_search_cache",
            description="Limpia el cache de búsquedas para una ciudad específica o todas"
        )
        self.search_service = SearchService()

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Limpia el cache de búsquedas."""
        city = params.get('city')

        await self.search_service.clear_cache(city)

        return {
            'cache_cleared': True,
            'city': city if city else 'all_cities'
        }


class SearchSuggestionsRoute(BaseRoute):
    """Ruta para obtener sugerencias de búsqueda."""

    def __init__(self):
        super().__init__(
            name="search_suggestions",
            description="Obtiene sugerencias de ciudades populares para búsqueda"
        )

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Obtiene sugerencias de búsqueda."""
        # En una implementación real, esto vendría de la base de datos
        popular_cities = [
            {
                'city': 'Buenos Aires',
                'country': 'Argentina',
                'property_count': 1250,
                'avg_price': 185.50,
                'popular_areas': ['Palermo', 'Recoleta', 'San Telmo']
            },
            {
                'city': 'Córdoba',
                'country': 'Argentina',
                'property_count': 680,
                'avg_price': 142.30,
                'popular_areas': ['Nueva Córdoba', 'Centro', 'Güemes']
            },
            {
                'city': 'Mendoza',
                'country': 'Argentina',
                'property_count': 420,
                'avg_price': 158.75,
                'popular_areas': ['Ciudad', 'Chacras de Coria', 'Maipú']
            },
            {
                'city': 'Rosario',
                'country': 'Argentina',
                'property_count': 340,
                'avg_price': 125.90,
                'popular_areas': ['Centro', 'Pichincha', 'Fisherton']
            },
            {
                'city': 'Bariloche',
                'country': 'Argentina',
                'property_count': 280,
                'avg_price': 195.40,
                'popular_areas': ['Centro', 'Llao Llao', 'Dina Huapi']
            }
        ]

        query = params.get('query', '').lower()

        if query:
            # Filtrar ciudades por consulta
            filtered_cities = [
                city for city in popular_cities
                if query in city['city'].lower() or query in city['country'].lower()
            ]
            return {
                'query': query,
                'suggestions': filtered_cities
            }

        return {
            'popular_cities': popular_cities
        }
