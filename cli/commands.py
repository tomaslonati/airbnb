"""
Comandos del CLI usando Typer.
"""

import typer
import asyncio
from datetime import date
from typing import Optional
from services.search import SearchService
from services.reservations import ReservationService
from services.analytics import AnalyticsService
from routes.registry import execute_route, get_available_routes
from migrations.manager import migration_manager
from utils.logging import get_logger, configure_logging

# Configurar logging al importar
configure_logging()
logger = get_logger(__name__)

app = typer.Typer(
    name="airbnb-backend",
    help="Backend CLI para sistema tipo Airbnb con múltiples bases de datos"
)


@app.command()
def search(
    city: str = typer.Argument(..., help="Ciudad donde buscar propiedades"),
    max_price: Optional[float] = typer.Option(
        None, "--max-price", "-p", help="Precio máximo por noche"),
    clear_cache: bool = typer.Option(
        False, "--clear-cache", "-c", help="Limpiar cache antes de buscar")
):
    """Busca propiedades disponibles en una ciudad."""

    async def _search():
        logger.info("Iniciando búsqueda", city=city, max_price=max_price)

        search_service = SearchService()

        if clear_cache:
            await search_service.clear_cache(city)
            typer.echo(f"✅ Cache limpiado para {city}")

        properties = await search_service.search_properties(city, max_price)

        if not properties:
            typer.echo(f"❌ No se encontraron propiedades en {city}")
            return

        typer.echo(f"\n🏠 Propiedades encontradas en {city}:")
        typer.echo("=" * 60)

        for prop in properties:
            price_info = f"${prop['price']}/noche"
            rating_info = f"⭐ {prop['rating']}" if prop['rating'] else "Sin rating"
            availability = "✅ Disponible" if prop['availability'] else "❌ No disponible"

            typer.echo(f"📍 {prop['title']}")
            typer.echo(f"   ID: {prop['id']}")
            typer.echo(
                f"   Precio: {price_info} | {rating_info} | {availability}")
            typer.echo()

        typer.echo(f"Total encontradas: {len(properties)}")

    asyncio.run(_search())


@app.command()
def reservation(
    action: str = typer.Argument(..., help="Acción: 'create' o 'list'"),
    property_id: Optional[str] = typer.Option(
        None, "--property", "-prop", help="ID de la propiedad"),
    user_id: str = typer.Option(..., "--user", "-u", help="ID del usuario"),
    check_in: Optional[str] = typer.Option(
        None, "--check-in", "-ci", help="Fecha de entrada (YYYY-MM-DD)"),
    check_out: Optional[str] = typer.Option(
        None, "--check-out", "-co", help="Fecha de salida (YYYY-MM-DD)")
):
    """Gestiona reservas de propiedades."""

    async def _reservation():
        reservation_service = ReservationService()

        if action == "create":
            if not all([property_id, check_in, check_out]):
                typer.echo(
                    "❌ Para crear una reserva necesitas: --property, --check-in, --check-out")
                raise typer.Exit(1)

            try:
                check_in_date = date.fromisoformat(check_in)
                check_out_date = date.fromisoformat(check_out)

                logger.info("Creando reserva",
                            property_id=property_id, user_id=user_id)

                reservation = await reservation_service.create_reservation(
                    property_id, user_id, check_in_date, check_out_date
                )

                typer.echo("\n✅ Reserva creada exitosamente!")
                typer.echo("=" * 50)
                typer.echo(f"ID Reserva: {reservation['id']}")
                typer.echo(f"Propiedad: {reservation['property_id']}")
                typer.echo(f"Usuario: {reservation['user_id']}")
                typer.echo(f"Check-in: {reservation['check_in']}")
                typer.echo(f"Check-out: {reservation['check_out']}")
                typer.echo(f"Estado: {reservation['status']}")

            except ValueError as e:
                typer.echo(f"❌ Error en fechas: {e}")
                raise typer.Exit(1)

        elif action == "list":
            logger.info("Listando reservas", user_id=user_id)

            reservations = await reservation_service.get_user_reservations(user_id)

            if not reservations:
                typer.echo(f"📋 No hay reservas para el usuario {user_id}")
                return

            typer.echo(f"\n📋 Reservas del usuario {user_id}:")
            typer.echo("=" * 60)

            for res in reservations:
                typer.echo(f"🏠 {res['id']}")
                typer.echo(f"   Propiedad: {res['property_id']}")
                typer.echo(
                    f"   Fechas: {res['check_in']} → {res['check_out']}")
                typer.echo(f"   Estado: {res['status']}")
                typer.echo(f"   Creada: {res['created_at']}")
                typer.echo()

            typer.echo(f"Total reservas: {len(reservations)}")

        else:
            typer.echo("❌ Acción inválida. Usa 'create' o 'list'")
            raise typer.Exit(1)

    asyncio.run(_reservation())


@app.command()
def analytics(
    report_type: str = typer.Argument(...,
                                      help="Tipo de reporte: 'bookings' o 'network'"),
    user_id: Optional[str] = typer.Option(
        None, "--user", "-u", help="ID del usuario (para análisis de red)"),
    days: int = typer.Option(
        30, "--days", "-d", help="Días hacia atrás para análisis")
):
    """Genera reportes analíticos y métricas."""

    async def _analytics():
        analytics_service = AnalyticsService()

        if report_type == "bookings":
            logger.info("Generando reporte de reservas", days=days)

            metrics = await analytics_service.get_booking_metrics(days)

            typer.echo(f"\n📊 Métricas de Reservas - Últimos {days} días")
            typer.echo("=" * 60)
            typer.echo(
                f"Período: {metrics['start_date'][:10]} → {metrics['end_date'][:10]}")
            typer.echo()

            stats = metrics['booking_stats']
            typer.echo("📈 Estadísticas Generales:")
            typer.echo(f"   Total reservas: {stats['total_bookings']}")
            typer.echo(f"   Ingresos totales: ${stats['total_revenue']:,.2f}")
            typer.echo()

            if stats.get('by_status'):
                typer.echo("📋 Por Estado:")
                for status, count in stats['by_status'].items():
                    typer.echo(f"   {status}: {count}")
                typer.echo()

            if metrics.get('top_cities'):
                typer.echo("🏙️ Ciudades Populares:")
                for city_data in metrics['top_cities'][:5]:
                    typer.echo(
                        f"   {city_data['city']}: {city_data['booking_count']} reservas "
                        f"(promedio: ${city_data['avg_price']})"
                    )

        elif report_type == "network":
            if not user_id:
                typer.echo(
                    "❌ Para análisis de red necesitas especificar --user")
                raise typer.Exit(1)

            logger.info("Generando análisis de red", user_id=user_id)

            analysis = await analytics_service.get_user_network_analysis(user_id)

            typer.echo(f"\n🕸️ Análisis de Red - Usuario {user_id}")
            typer.echo("=" * 60)

            # Métricas de centralidad
            metrics = analysis['centrality_metrics']
            typer.echo("📊 Métricas de Conectividad:")
            typer.echo(
                f"   Relaciones totales: {metrics['total_relationships']}")
            typer.echo(f"   Amigos: {metrics['friends_count']}")
            typer.echo(f"   Hosts contactados: {metrics['hosted_count']}")
            typer.echo()

            # Conexiones directas
            connections = analysis['direct_connections']
            if connections:
                typer.echo("👥 Conexiones Directas:")
                for conn in connections[:10]:  # Mostrar primeras 10
                    typer.echo(
                        f"   {conn['name']} ({conn['relationship_type']})")
                typer.echo()

            # Recomendaciones
            recommendations = analysis['recommendations']
            if recommendations:
                typer.echo("💡 Propiedades Recomendadas por tu Red:")
                for rec in recommendations[:5]:  # Mostrar primeras 5
                    typer.echo(
                        f"   {rec['title']} en {rec['city']} "
                        f"({rec['friend_recommendations']} amigos la recomiendan)"
                    )

        else:
            typer.echo("❌ Tipo de reporte inválido. Usa 'bookings' o 'network'")
            raise typer.Exit(1)

    asyncio.run(_analytics())


@app.command()
def migrate(
    action: str = typer.Argument(...,
                                 help="Acción: 'run', 'status' o 'rollback'"),
    version: Optional[str] = typer.Option(
        None, "--version", "-v", help="Versión específica (para rollback)"),
    force: bool = typer.Option(
        False, "--force", "-f", help="Forzar ejecución sin confirmación")
):
    """Gestiona migraciones de base de datos."""

    async def _migrate():
        if action == "status":
            result = await execute_route("migration_status", {})

            if result['success']:
                data = result['data']
                summary = data['migration_summary']

                typer.echo(f"\n📊 Estado de Migraciones")
                typer.echo("=" * 50)
                typer.echo(f"Total migraciones: {summary['total_migrations']}")
                typer.echo(f"Ejecutadas: {summary['executed_migrations']}")
                typer.echo(f"Pendientes: {summary['pending_migrations']}")
                typer.echo(f"Completado: {summary['completion_percentage']}%")
                typer.echo()

                for db, details in data['database_details'].items():
                    typer.echo(f"🗄️ {db.upper()}:")
                    typer.echo(
                        f"   Ejecutadas: {details['executed_migrations']}/{details['total_migrations']}")
                    if details['pending_versions']:
                        typer.echo(
                            f"   Pendientes: {', '.join(details['pending_versions'])}")
                    typer.echo()
            else:
                typer.echo(f"❌ Error: {result['error']}")

        elif action == "run":
            if not force:
                confirm = typer.confirm(
                    "¿Ejecutar todas las migraciones pendientes?")
                if not confirm:
                    typer.echo("❌ Operación cancelada")
                    return

            result = await execute_route("run_migrations", {"confirmed": True})

            if result['success']:
                typer.echo("✅ Migraciones ejecutadas exitosamente")
            else:
                typer.echo(
                    f"❌ Error ejecutando migraciones: {result['error']}")

        elif action == "rollback":
            if not version:
                typer.echo("❌ Especifica la versión a revertir con --version")
                return

            if not force:
                confirm = typer.confirm(f"¿Revertir migración {version}?")
                if not confirm:
                    typer.echo("❌ Operación cancelada")
                    return

            try:
                await migration_manager.rollback_all_databases(version)
                typer.echo(f"✅ Migración {version} revertida")
            except Exception as e:
                typer.echo(f"❌ Error en rollback: {e}")

        else:
            typer.echo("❌ Acción inválida. Usa 'run', 'status' o 'rollback'")

    asyncio.run(_migrate())


@app.command()
def status():
    """Verifica el estado de las conexiones y salud del sistema."""

    async def _check_status():
        typer.echo("🔍 Verificando estado del sistema...")
        typer.echo("=" * 50)

        # Verificar salud del sistema usando rutas
        health_result = await execute_route("system_health", {})

        if health_result['success']:
            health_data = health_result['data']
            overall = health_data['overall_health']

            status_emoji = "✅" if overall == "healthy" else "🟡" if overall == "degraded" else "❌"
            typer.echo(f"{status_emoji} Estado general: {overall.upper()}")
            typer.echo(
                f"Verificaciones: {health_data['checks_passed']}/{health_data['total_checks']}")
            typer.echo()

            for component, details in health_data['health_details'].items():
                status_icon = "✅" if details['status'] == 'ok' else "❌"
                typer.echo(
                    f"{status_icon} {component.title()}: {details['status']}")
                if details['status'] == 'error':
                    typer.echo(f"   Error: {details['error']}")
            typer.echo()

        # Verificar estado de bases de datos
        db_result = await execute_route("database_status", {})

        if db_result['success']:
            db_data = db_result['data']
            typer.echo(
                f"🗄️ Bases de Datos: {db_data['connected_databases']}/{db_data['total_databases']} conectadas")

            for db, details in db_data['database_details'].items():
                status_icon = "✅" if details['status'] == 'connected' else "❌"
                typer.echo(f"{status_icon} {db.upper()}: {details['status']}")
                if details['error']:
                    typer.echo(f"   Error: {details['error']}")

        typer.echo()
        typer.echo("💡 Usa 'migrate status' para verificar migraciones")
        typer.echo("💡 Usa comandos específicos para probar funcionalidad")

    asyncio.run(_check_status())


@app.command()
def routes():
    """Lista todas las rutas disponibles en el sistema."""

    async def _list_routes():
        available_routes = get_available_routes()

        typer.echo("\n🛣️ Rutas Disponibles")
        typer.echo("=" * 60)

        # Agrupar rutas por categoría
        categories = {
            'Búsquedas': [r for r in available_routes.keys() if 'search' in r],
            'Reservas': [r for r in available_routes.keys() if 'reservation' in r],
            'Analíticas': [r for r in available_routes.keys() if any(x in r for x in ['booking', 'network', 'revenue', 'popular'])],
            'Administración': [r for r in available_routes.keys() if any(x in r for x in ['database', 'migration', 'system', 'cache'])]
        }

        for category, routes in categories.items():
            if routes:
                typer.echo(f"\n📂 {category}:")
                for route_name in routes:
                    description = available_routes[route_name]
                    typer.echo(f"   • {route_name}: {description}")

        typer.echo(f"\n📊 Total rutas disponibles: {len(available_routes)}")
        typer.echo("\n💡 Las rutas se usan internamente por los comandos del CLI")
        typer.echo("💡 También están disponibles para integración programática")

    asyncio.run(_list_routes())


@app.command()
def admin(
    action: str = typer.Argument(..., help="Acción: 'clear-cache' o 'health'"),
    force: bool = typer.Option(
        False, "--force", "-f", help="Forzar ejecución sin confirmación")
):
    """Comandos administrativos del sistema."""

    async def _admin():
        if action == "clear-cache":
            if not force:
                confirm = typer.confirm("¿Limpiar todos los caches?")
                if not confirm:
                    typer.echo("❌ Operación cancelada")
                    return

            result = await execute_route("clear_all_caches", {})

            if result['success']:
                data = result['data']
                typer.echo("✅ Caches limpiados exitosamente")
                typer.echo(
                    f"Tipos limpiados: {', '.join(data['cleared_types'])}")
            else:
                typer.echo(f"❌ Error limpiando caches: {result['error']}")

        elif action == "health":
            result = await execute_route("system_health", {})

            if result['success']:
                data = result['data']
                typer.echo(f"\n🏥 Diagnóstico de Salud del Sistema")
                typer.echo("=" * 50)
                typer.echo(f"Estado general: {data['overall_health'].upper()}")
                typer.echo(
                    f"Verificaciones exitosas: {data['checks_passed']}/{data['total_checks']}")
                typer.echo()

                for component, details in data['health_details'].items():
                    icon = "✅" if details['status'] == 'ok' else "❌"
                    typer.echo(f"{icon} {component.title()}")
                    if 'loaded_services' in details:
                        typer.echo(
                            f"   Servicios: {', '.join(details['loaded_services'])}")
                    if details['status'] == 'error':
                        typer.echo(f"   Error: {details['error']}")
            else:
                typer.echo(f"❌ Error en diagnóstico: {result['error']}")

        else:
            typer.echo("❌ Acción inválida. Usa 'clear-cache' o 'health'")

    asyncio.run(_admin())


if __name__ == "__main__":
    app()
