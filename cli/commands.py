"""
Comandos del CLI usando Typer.
"""

import typer
import asyncio
from datetime import date
from typing import Optional, List
from services.search import SearchService
from services.reservations import ReservationService
from services.analytics import AnalyticsService
from services.properties import PropertyService
from services.setup import SetupService
from services.auth import AuthService
from services.user import UserService
from services.mongo_host import MongoHostService
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


@app.command()
def setup():
    """Configura datos básicos del sistema (países, ciudades, amenities, etc.)."""

    async def _setup():
        setup_service = SetupService()

        typer.echo("🛠️  Configurando datos básicos del sistema...")
        typer.echo("=" * 60)

        # Confirmación
        confirm = typer.confirm(
            "¿Desea proceder con la configuración inicial?")
        if not confirm:
            typer.echo("❌ Configuración cancelada")
            return

        try:
            result = await setup_service.setup_all()

            if result["success"]:
                typer.echo("\n✅ Configuración completada exitosamente!")

                if result["demo_user"]:
                    demo = result["demo_user"]
                    typer.echo("\n👤 Usuario demo creado:")
                    typer.echo(f"   Email: {demo['email']}")
                    typer.echo(f"   Password: {demo['password']}")
                    typer.echo(f"   User ID: {demo['user_id']}")

            else:
                typer.echo("\n⚠️  Configuración completada con errores:")
                for error in result["errors"]:
                    typer.echo(f"   • {error}")

        except Exception as e:
            logger.error("Error en configuración", error=str(e))
            typer.echo(f"❌ Error durante la configuración: {e}")
            raise typer.Exit(1)

    asyncio.run(_setup())


@app.command()
def property(
    action: str = typer.Argument(...,
                                 help="Acción: 'create', 'list', o 'stats'"),
    name: Optional[str] = typer.Option(
        None, "--name", "-n", help="Nombre de la propiedad"),
    description: Optional[str] = typer.Option(
        None, "--description", "-d", help="Descripción"),
    capacity: Optional[int] = typer.Option(
        None, "--capacity", "-c", help="Capacidad de huéspedes"),
    city_id: Optional[int] = typer.Option(
        None, "--city", help="ID de la ciudad"),
    host_id: Optional[int] = typer.Option(
        None, "--host", help="ID del anfitrión"),
    type_id: Optional[int] = typer.Option(
        None, "--type", help="ID del tipo de propiedad"),
    interactive: bool = typer.Option(
        False, "--interactive", "-i", help="Modo interactivo")
):
    """Gestiona propiedades del sistema."""

    async def _property():
        property_service = PropertyService()

        if action == "create":
            if interactive:
                await _create_property_interactive(property_service)
            else:
                await _create_property_params(property_service, name, description, capacity, city_id, host_id, type_id)

        elif action == "list":
            await _list_properties(property_service)

        elif action == "stats":
            await _property_stats(property_service)

        else:
            typer.echo("❌ Acción inválida. Usa 'create', 'list', o 'stats'")
            raise typer.Exit(1)

    async def _create_property_interactive(service: PropertyService):
        """Crear propiedad en modo interactivo."""
        typer.echo("\n🏠 CREAR NUEVA PROPIEDAD")
        typer.echo("=" * 50)

        # Información básica
        name = typer.prompt("Nombre de la propiedad")
        description = typer.prompt("Descripción")
        capacity = typer.prompt("Capacidad (huéspedes)", type=int)

        # Seleccionar país y ciudad
        countries = await service.get_countries()
        if not countries:
            typer.echo("❌ No hay países configurados. Ejecute 'setup' primero.")
            return

        typer.echo("\n🌍 Países disponibles:")
        for i, country in enumerate(countries, 1):
            typer.echo(f"  {i}. {country['nombre']}")

        country_idx = typer.prompt("Seleccione país", type=int) - 1
        if not (0 <= country_idx < len(countries)):
            typer.echo("❌ Selección inválida")
            return

        selected_country = countries[country_idx]
        cities = await service.get_cities_by_country(selected_country['id'])

        if not cities:
            typer.echo("❌ No hay ciudades para este país")
            return

        typer.echo(f"\n🏙️ Ciudades en {selected_country['nombre']}:")
        for i, city in enumerate(cities, 1):
            typer.echo(f"  {i}. {city['nombre']} ({city['cp']})")

        city_idx = typer.prompt("Seleccione ciudad", type=int) - 1
        if not (0 <= city_idx < len(cities)):
            typer.echo("❌ Selección inválida")
            return

        selected_city = cities[city_idx]

        # Seleccionar anfitrión
        hosts = await service.get_hosts()
        if not hosts:
            typer.echo("❌ No hay anfitriones disponibles")
            return

        typer.echo("\n👤 Anfitriones disponibles:")
        for i, host in enumerate(hosts, 1):
            typer.echo(f"  {i}. {host['nombre']} ({host['email']})")

        host_idx = typer.prompt("Seleccione anfitrión", type=int) - 1
        if not (0 <= host_idx < len(hosts)):
            typer.echo("❌ Selección inválida")
            return

        selected_host = hosts[host_idx]

        # Seleccionar tipo de propiedad
        types = await service.get_property_types()
        if not types:
            typer.echo("❌ No hay tipos de propiedad configurados")
            return

        typer.echo("\n🏠 Tipos de propiedad:")
        for i, prop_type in enumerate(types, 1):
            typer.echo(f"  {i}. {prop_type['nombre']}")

        type_idx = typer.prompt("Seleccione tipo", type=int) - 1
        if not (0 <= type_idx < len(types)):
            typer.echo("❌ Selección inválida")
            return

        selected_type = types[type_idx]

        # Crear propiedad
        property_data = {
            'nombre': name,
            'descripcion': description,
            'capacidad': capacity,
            'ciudad_id': selected_city['id'],
            'anfitrion_id': selected_host['id'],
            'tipo_propiedad_id': selected_type['id']
        }

        try:
            property_id = await service.create_property(property_data)
            typer.echo(f"\n✅ Propiedad creada con ID: {property_id}")

            # Mostrar resumen
            summary = await service.get_property_summary(property_id)
            typer.echo("\n📋 Resumen:")
            typer.echo(f"   Nombre: {summary['nombre']}")
            typer.echo(f"   Ubicación: {summary['ciudad']}, {summary['pais']}")
            typer.echo(f"   Anfitrión: {summary['anfitrion']}")
            typer.echo(f"   Tipo: {summary['tipo_propiedad']}")

        except Exception as e:
            typer.echo(f"❌ Error creando propiedad: {e}")
            raise typer.Exit(1)

    async def _create_property_params(service: PropertyService, name, description, capacity, city_id, host_id, type_id):
        """Crear propiedad usando parámetros."""
        if not all([name, description, capacity, city_id, host_id, type_id]):
            typer.echo(
                "❌ Faltan parámetros requeridos. Use --interactive o proporcione todos los parámetros.")
            return

        property_data = {
            'nombre': name,
            'descripcion': description,
            'capacidad': capacity,
            'ciudad_id': city_id,
            'anfitrion_id': host_id,
            'tipo_propiedad_id': type_id
        }

        try:
            property_id = await service.create_property(property_data)
            typer.echo(f"✅ Propiedad creada con ID: {property_id}")
        except Exception as e:
            typer.echo(f"❌ Error creando propiedad: {e}")
            raise typer.Exit(1)

    async def _list_properties(service: PropertyService):
        """Listar propiedades."""
        typer.echo("🏠 Esta funcionalidad estará disponible próximamente")
        typer.echo("💡 Por ahora use 'property stats' para ver estadísticas")

    async def _property_stats(service: PropertyService):
        """Mostrar estadísticas de propiedades."""
        try:
            stats = await service.get_property_statistics()

            typer.echo("\n📊 ESTADÍSTICAS DE PROPIEDADES")
            typer.echo("=" * 50)
            typer.echo(f"Total de propiedades: {stats['total_properties']}")

            if stats['by_type']:
                typer.echo("\n🏠 Por tipo de propiedad:")
                for prop_type in stats['by_type']:
                    typer.echo(
                        f"   {prop_type['nombre']}: {prop_type['cantidad']}")

            if stats['by_city']:
                typer.echo("\n🌍 Por ciudad:")
                for city in stats['by_city']:
                    typer.echo(
                        f"   {city['ciudad']}, {city['pais']}: {city['cantidad']}")

        except Exception as e:
            typer.echo(f"❌ Error obteniendo estadísticas: {e}")
            raise typer.Exit(1)

    asyncio.run(_property())


@app.command()
def auth(
    action: str = typer.Argument(
        ..., help="Acción: 'login', 'register', 'logout', 'profile', o 'status'"),
    email: Optional[str] = typer.Option(
        None, "--email", "-e", help="Email del usuario"),
    password: Optional[str] = typer.Option(
        None, "--password", "-p", help="Contraseña"),
    rol: Optional[str] = typer.Option(
        None, "--role", "-r", help="Rol: HUESPED, ANFITRION o AMBOS"),
    nombre: Optional[str] = typer.Option(
        None, "--name", "-n", help="Nombre del usuario"),
    interactive: bool = typer.Option(
        False, "--interactive", "-i", help="Modo interactivo")
):
    """Gestiona autenticación y perfiles de usuario."""

    async def _auth():
        auth_service = AuthService()
        user_service = UserService()

        try:
            if action == "register":
                # Inicializar variables
                _email = email
                _password = password
                _rol = rol
                _nombre = nombre

                if interactive or not all([_email, _password, _rol]):
                    # Modo interactivo
                    typer.echo("📝 REGISTRO DE NUEVO USUARIO")
                    typer.echo("=" * 50)

                    if not _email:
                        _email = typer.prompt("📧 Email")
                    if not _password:
                        _password = typer.prompt(
                            "🔐 Contraseña", hide_input=True)
                    if not _rol:
                        typer.echo("\n🎭 Roles disponibles:")
                        typer.echo("1. HUESPED - Solo reservar propiedades")
                        typer.echo("2. ANFITRION - Solo publicar propiedades")
                        typer.echo("3. AMBOS - Reservar y publicar")

                        rol_choice = typer.prompt(
                            "Seleccionar rol (1-3)", type=int)
                        rol_map = {1: "HUESPED", 2: "ANFITRION", 3: "AMBOS"}
                        _rol = rol_map.get(rol_choice, "HUESPED")

                    if not _nombre:
                        _nombre = typer.prompt(
                            "👤 Nombre completo", default=_email.split('@')[0])

                # Registrar usuario
                result = await auth_service.register(_email, _password, _rol, _nombre)
                typer.echo(result.message)

                if result.success and result.user_profile:
                    typer.echo(f"✅ Bienvenido/a {result.user_profile.nombre}!")
                    typer.echo(f"🎭 Rol: {result.user_profile.rol}")
                else:
                    raise typer.Exit(1)

            elif action == "login":
                # Inicializar variables
                _email = email
                _password = password

                if interactive or not all([_email, _password]):
                    # Modo interactivo
                    typer.echo("🔐 INICIO DE SESIÓN")
                    typer.echo("=" * 30)

                    if not _email:
                        _email = typer.prompt("📧 Email")
                    if not _password:
                        _password = typer.prompt(
                            "🔐 Contraseña", hide_input=True)

                # Iniciar sesión
                result = await auth_service.login(_email, _password)
                typer.echo(result.message)

                if result.success and result.user_profile:
                    typer.echo(f"🎭 Rol: {result.user_profile.rol}")

                    # Mostrar estadísticas básicas
                    stats = await user_service.get_user_stats(result.user_profile)

                    if stats.huesped_stats:
                        typer.echo(
                            f"🏠 Reservas totales: {stats.huesped_stats.get('total_reservas', 0)}")

                    if stats.anfitrion_stats:
                        typer.echo(
                            f"🏡 Propiedades: {stats.anfitrion_stats.get('total_propiedades', 0)}")
                else:
                    raise typer.Exit(1)

            elif action == "logout":
                result = await auth_service.logout()
                typer.echo(result.message)

            elif action == "profile":
                user_profile = auth_service.get_current_user()

                if not user_profile:
                    typer.echo(
                        "❌ No hay sesión activa. Usa 'auth login' primero.")
                    raise typer.Exit(1)

                # Mostrar perfil completo
                typer.echo("👤 PERFIL DE USUARIO")
                typer.echo("=" * 40)
                typer.echo(f"📧 Email: {user_profile.email}")
                typer.echo(f"🎭 Rol: {user_profile.rol}")
                typer.echo(
                    f"📅 Registrado: {user_profile.creado_en.strftime('%d/%m/%Y')}")

                # Datos específicos por rol
                if user_profile.rol in ['HUESPED', 'AMBOS']:
                    huesped_profile = await user_service.get_huesped_profile(user_profile)
                    if huesped_profile:
                        typer.echo(f"\n🏠 DATOS DE HUÉSPED:")
                        typer.echo(f"   👤 Nombre: {huesped_profile.nombre}")
                        typer.echo(
                            f"   📞 Teléfono: {huesped_profile.telefono or 'No especificado'}")
                        typer.echo(
                            f"   🎫 Reservas totales: {huesped_profile.total_reservas}")
                        typer.echo(
                            f"   ✅ Reservas activas: {huesped_profile.reservas_activas}")

                if user_profile.rol in ['ANFITRION', 'AMBOS']:
                    anfitrion_profile = await user_service.get_anfitrion_profile(user_profile)
                    if anfitrion_profile:
                        typer.echo(f"\n🏡 DATOS DE ANFITRIÓN:")
                        typer.echo(f"   👤 Nombre: {anfitrion_profile.nombre}")
                        typer.echo(
                            f"   🏠 Propiedades: {anfitrion_profile.total_propiedades}")
                        typer.echo(
                            f"   ✅ Reservas completadas: {anfitrion_profile.cant_rvas_completadas}")

            elif action == "status":
                user_profile = auth_service.get_current_user()

                if user_profile:
                    typer.echo(
                        f"✅ Sesión activa: {user_profile.email} ({user_profile.rol})")
                else:
                    typer.echo("❌ No hay sesión activa")

            else:
                typer.echo(f"❌ Acción inválida: {action}")
                typer.echo(
                    "Acciones válidas: login, register, logout, profile, status")
                raise typer.Exit(1)

        except Exception as e:
            typer.echo(f"❌ Error en autenticación: {str(e)}")
            raise typer.Exit(1)

    asyncio.run(_auth())


@app.command()
def user(
    action: str = typer.Argument(
        ..., help="Acción: 'stats', 'reservations', 'properties', o 'update'"),
    limit: int = typer.Option(
        10, "--limit", "-l", help="Límite de resultados"),
    interactive: bool = typer.Option(
        False, "--interactive", "-i", help="Modo interactivo")
):
    """Gestiona datos y operaciones específicas del usuario."""

    async def _user():
        auth_service = AuthService()
        user_service = UserService()

        try:
            # Verificar autenticación
            user_profile = auth_service.get_current_user()
            if not user_profile:
                typer.echo("❌ No hay sesión activa. Usa 'auth login' primero.")
                raise typer.Exit(1)

            if action == "stats":
                # Estadísticas completas del usuario
                stats = await user_service.get_user_stats(user_profile)

                typer.echo("📊 ESTADÍSTICAS DEL USUARIO")
                typer.echo("=" * 40)
                typer.echo(
                    f"👤 Usuario: {user_profile.nombre or user_profile.email}")
                typer.echo(f"🎭 Rol: {user_profile.rol}")

                if stats.huesped_stats:
                    h_stats = stats.huesped_stats
                    typer.echo(f"\n🏠 COMO HUÉSPED:")
                    typer.echo(
                        f"   📋 Total reservas: {h_stats.get('total_reservas', 0)}")
                    typer.echo(
                        f"   ✅ Completadas: {h_stats.get('reservas_completadas', 0)}")
                    typer.echo(
                        f"   🔄 Activas: {h_stats.get('reservas_activas', 0)}")
                    typer.echo(
                        f"   ❌ Canceladas: {h_stats.get('reservas_canceladas', 0)}")
                    typer.echo(
                        f"   💰 Gasto total: ${h_stats.get('gasto_total', 0)}")

                if stats.anfitrion_stats:
                    a_stats = stats.anfitrion_stats
                    typer.echo(f"\n🏡 COMO ANFITRIÓN:")
                    typer.echo(
                        f"   🏠 Total propiedades: {a_stats.get('total_propiedades', 0)}")
                    typer.echo(
                        f"   📋 Reservas recibidas: {a_stats.get('total_reservas_recibidas', 0)}")
                    typer.echo(
                        f"   ✅ Reservas completadas: {a_stats.get('cant_rvas_completadas', 0)}")
                    typer.echo(
                        f"   💰 Ingresos totales: ${a_stats.get('ingresos_totales', 0)}")
                    typer.echo(
                        f"   ⭐ Puntaje promedio: {a_stats.get('puntaje_promedio', 0):.1f}/5")

            elif action == "reservations":
                # Mostrar reservas del huésped
                if not user_profile.huesped_id:
                    typer.echo("❌ Usuario no tiene perfil de huésped")
                    raise typer.Exit(1)

                reservas = await user_service.get_user_reservations(user_profile.huesped_id, limit)

                if not reservas:
                    typer.echo("📋 No tienes reservas registradas")
                    return

                typer.echo(f"📋 TUS RESERVAS (últimas {len(reservas)})")
                typer.echo("=" * 50)

                for reserva in reservas:
                    typer.echo(f"🏠 {reserva['propiedad_nombre']}")
                    typer.echo(f"   📍 {reserva['ciudad']}, {reserva['pais']}")
                    typer.echo(
                        f"   📅 {reserva['fecha_check_in']} - {reserva['fecha_check_out']}")
                    typer.echo(f"   💰 ${reserva['monto_final']}")
                    typer.echo(f"   📊 Estado: {reserva['estado']}")
                    typer.echo(
                        f"   👤 Anfitrión: {reserva['anfitrion_nombre']}")
                    typer.echo("")

            elif action == "properties":
                # Mostrar propiedades del anfitrión
                if not user_profile.anfitrion_id:
                    typer.echo("❌ Usuario no tiene perfil de anfitrión")
                    raise typer.Exit(1)

                propiedades = await user_service.get_anfitrion_properties(user_profile.anfitrion_id)

                if not propiedades:
                    typer.echo("🏠 No tienes propiedades registradas")
                    return

                typer.echo(f"🏡 TUS PROPIEDADES ({len(propiedades)})")
                typer.echo("=" * 40)

                for prop in propiedades:
                    typer.echo(f"🏠 {prop['nombre']}")
                    typer.echo(f"   📍 {prop['ciudad']}, {prop['pais']}")
                    typer.echo(f"   🏠 Tipo: {prop['tipo_propiedad']}")
                    typer.echo(f"   👥 Capacidad: {prop['capacidad']} personas")
                    typer.echo(
                        f"   📋 Reservas totales: {prop['total_reservas']}")
                    if prop['descripcion']:
                        typer.echo(f"   📝 {prop['descripcion'][:60]}...")
                    typer.echo("")

            else:
                typer.echo(f"❌ Acción inválida: {action}")
                typer.echo(
                    "Acciones válidas: stats, reservations, properties, update")
                raise typer.Exit(1)

        except Exception as e:
            typer.echo(f"❌ Error gestionando usuario: {str(e)}")
            raise typer.Exit(1)

    asyncio.run(_user())


@app.command()
def mongo(
    action: str = typer.Argument(...,
                                 help="Acción: 'hosts', 'ratings', 'stats', o 'verify'"),
    host_id: Optional[int] = typer.Option(
        None, "--host", "-h", help="ID del anfitrión"),
    guest_id: Optional[int] = typer.Option(
        None, "--guest", "-g", help="ID del huésped (para ratings)"),
    rating: Optional[float] = typer.Option(
        None, "--rating", "-r", help="Calificación (1-5)"),
    comment: Optional[str] = typer.Option(
        None, "--comment", "-c", help="Comentario de la calificación"),
    limit: int = typer.Option(10, "--limit", "-l", help="Límite de resultados")
):
    """Gestiona documentos y datos de MongoDB (anfitriones y calificaciones)."""

    async def _mongo():
        mongo_service = MongoHostService()

        try:
            if action == "verify":
                # Verificar conexión MongoDB
                typer.echo("🔍 Verificando conexión MongoDB...")
                result = await mongo_service.verify_connection()

                if result.get('success'):
                    typer.echo("✅ MongoDB conectado correctamente")
                else:
                    typer.echo(f"❌ Error MongoDB: {result.get('error')}")
                    raise typer.Exit(1)

            elif action == "hosts":
                # Listar todos los anfitriones en MongoDB
                typer.echo("🏠 DOCUMENTOS DE ANFITRIONES EN MONGODB")
                typer.echo("=" * 50)

                result = await mongo_service.get_all_hosts()

                if result.get('success'):
                    hosts = result['hosts']

                    if not hosts:
                        typer.echo(
                            "📝 No hay documentos de anfitriones en MongoDB")
                        return

                    typer.echo(f"Total de anfitriones: {len(hosts)}")
                    typer.echo()

                    for host in hosts:
                        host_id = host['host_id']
                        ratings_count = len(host.get('ratings', []))
                        stats = host.get('stats', {})
                        avg_rating = stats.get('average_rating', 0.0)
                        total_reviews = stats.get('total_reviews', 0)

                        typer.echo(f"🏠 Host ID: {host_id}")
                        typer.echo(
                            f"   ⭐ {ratings_count} calificaciones (promedio: {avg_rating:.1f})")
                        typer.echo(
                            f"   📝 {total_reviews} reviews con comentarios")

                        if 'created_at' in host:
                            typer.echo(f"   📅 Creado: {host['created_at']}")
                        typer.echo()
                else:
                    typer.echo(f"❌ Error: {result.get('error')}")
                    raise typer.Exit(1)

            elif action == "ratings":
                if not host_id:
                    typer.echo("❌ Especifica --host para ver calificaciones")
                    raise typer.Exit(1)

                # Si se proporcionan datos para crear rating
                if guest_id and rating:
                    typer.echo(
                        f"📝 Agregando calificación al host {host_id}...")

                    rating_data = {
                        "guest_id": guest_id,
                        "rating": rating,
                        "comment": comment or "",
                        "reservation_id": 999  # Placeholder - en producción vendría de la reserva
                    }

                    result = await mongo_service.add_rating(host_id, rating_data)

                    if result.get('success'):
                        typer.echo("✅ Calificación agregada exitosamente")
                    else:
                        typer.echo(f"❌ Error: {result.get('error')}")
                        raise typer.Exit(1)

                # Mostrar calificaciones del host
                typer.echo(f"⭐ CALIFICACIONES DEL HOST {host_id}")
                typer.echo("=" * 40)

                result = await mongo_service.get_host_ratings(host_id, limit)

                if result.get('success'):
                    ratings = result['ratings']

                    if not ratings:
                        typer.echo("📝 Este anfitrión no tiene calificaciones")
                        return

                    typer.echo(
                        f"Mostrando últimas {min(len(ratings), limit)} calificaciones:")
                    typer.echo()

                    for i, rating_data in enumerate(ratings, 1):
                        rating_val = rating_data.get('rating', 0)
                        guest = rating_data.get('guest_id', 'N/A')
                        comment = rating_data.get('comment', '')

                        stars = "⭐" * int(rating_val)
                        typer.echo(
                            f"{i}. {stars} ({rating_val}/5) - Huésped {guest}")
                        if comment:
                            typer.echo(f"   💬 \"{comment}\"")
                        typer.echo()
                else:
                    typer.echo(f"❌ Error: {result.get('error')}")
                    raise typer.Exit(1)

            elif action == "stats":
                if not host_id:
                    typer.echo("❌ Especifica --host para ver estadísticas")
                    raise typer.Exit(1)

                typer.echo(f"📊 ESTADÍSTICAS DEL HOST {host_id}")
                typer.echo("=" * 40)

                result = await mongo_service.get_host_stats(host_id)

                if result.get('success'):
                    stats = result['stats']

                    typer.echo(
                        f"Total calificaciones: {stats.get('total_ratings', 0)}")
                    typer.echo(
                        f"Promedio: {stats.get('average_rating', 0.0):.2f}/5")
                    typer.echo(
                        f"Reviews con comentarios: {stats.get('total_reviews', 0)}")

                    # Mostrar documento completo
                    doc_result = await mongo_service.get_host_document(host_id)
                    if doc_result.get('success'):
                        doc = doc_result['document']
                        if 'updated_at' in doc:
                            typer.echo(
                                f"Última actualización: {doc['updated_at']}")
                else:
                    typer.echo(f"❌ Error: {result.get('error')}")
                    raise typer.Exit(1)

            else:
                typer.echo("❌ Acción inválida.")
                typer.echo("Acciones válidas: hosts, ratings, stats, verify")
                typer.echo("\nEjemplos:")
                typer.echo(
                    "  mongo verify                    # Verificar conexión")
                typer.echo(
                    "  mongo hosts                     # Listar todos los anfitriones")
                typer.echo(
                    "  mongo ratings --host 1          # Ver calificaciones del host 1")
                typer.echo(
                    "  mongo ratings --host 1 --guest 5 --rating 4.5 --comment 'Excelente'")
                typer.echo(
                    "  mongo stats --host 1            # Estadísticas del host 1")
                raise typer.Exit(1)

        except Exception as e:
            typer.echo(f"❌ Error en MongoDB: {str(e)}")
            raise typer.Exit(1)

    asyncio.run(_mongo())


if __name__ == "__main__":
    app()
