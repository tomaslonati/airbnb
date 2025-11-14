"""
Registro y gestión centralizada de todas las rutas.
"""

from routes.base import route_registry
from routes.search_routes import (
    SearchPropertiesRoute, ClearSearchCacheRoute, SearchSuggestionsRoute
)
from routes.reservation_routes import (
    CreateReservationRoute, GetUserReservationsRoute,
    CancelReservationRoute, GetReservationDetailsRoute
)
from routes.analytics_routes import (
    BookingMetricsRoute, UserNetworkAnalysisRoute,
    RevenueAnalyticsRoute, PopularDestinationsRoute
)
from routes.admin_routes import (
    DatabaseStatusRoute, MigrationStatusRoute, RunMigrationsRoute,
    SystemHealthRoute, ClearAllCachesRoute
)
from utils.logging import get_logger

logger = get_logger(__name__)


def register_all_routes():
    """Registra todas las rutas disponibles en el sistema."""

    # Rutas de búsqueda
    search_routes = [
        SearchPropertiesRoute(),
        ClearSearchCacheRoute(),
        SearchSuggestionsRoute()
    ]

    for route in search_routes:
        route_registry.register_route(route)

    # Rutas de reservas
    reservation_routes = [
        CreateReservationRoute(),
        GetUserReservationsRoute(),
        CancelReservationRoute(),
        GetReservationDetailsRoute()
    ]

    for route in reservation_routes:
        route_registry.register_route(route)

    # Rutas de analíticas
    analytics_routes = [
        BookingMetricsRoute(),
        UserNetworkAnalysisRoute(),
        RevenueAnalyticsRoute(),
        PopularDestinationsRoute()
    ]

    for route in analytics_routes:
        route_registry.register_route(route)

    # Rutas administrativas
    admin_routes = [
        DatabaseStatusRoute(),
        MigrationStatusRoute(),
        RunMigrationsRoute(),
        SystemHealthRoute(),
        ClearAllCachesRoute()
    ]

    for route in admin_routes:
        route_registry.register_route(route)

    logger.info("Todas las rutas registradas",
                total_routes=len(route_registry.routes))


def get_available_routes():
    """Obtiene lista de todas las rutas disponibles."""
    return route_registry.list_routes()


async def execute_route(route_name: str, params: dict):
    """Ejecuta una ruta específica."""
    return await route_registry.execute_route(route_name, params)


# Registrar todas las rutas al importar el módulo
register_all_routes()
