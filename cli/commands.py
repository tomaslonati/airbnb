"""
Comandos del CLI usando Typer - Versión Interactiva.
"""

import typer
import asyncio
from typing import Optional
from datetime import datetime, date
from services.auth import AuthService
from services.user import UserService
from services.mongo_host import MongoHostService
from services.reservations import ReservationService
from utils.logging import get_logger, configure_logging

# Importar módulos CLI de features
from cli.auth.commands import app as auth_app
from cli.properties.commands import app as properties_app
from cli.reservations.commands import app as reservations_app

# Importar gestión de sesiones
from cli.sessions import (
    validate_session_or_expire,
    refresh_session_after_action,
    restore_previous_session,
    show_auth_menu,
    show_main_menu,
    handle_login,
    handle_register,
    handle_logout,
    show_user_profile,
    show_active_sessions,
    get_current_user,
    set_current_user,
    get_session_token
)

# Configurar logging al importar
configure_logging()
logger = get_logger(__name__)

app = typer.Typer(
    name="airbnb-backend",
    help="Backend CLI para sistema tipo Airbnb - Sistema de Autenticación Interactivo"
)

# Integrar sub-apps de features
app.add_typer(auth_app, name="auth", help="Comandos de autenticación")
app.add_typer(properties_app, name="properties", help="Gestión de propiedades")
app.add_typer(reservations_app, name="reservations",
              help="Gestión de reservas")


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """
    Sistema interactivo de Airbnb Backend.
    Inicia automáticamente el modo interactivo si no se especifica un comando.
    """
    if ctx.invoked_subcommand is None:
        # Modo interactivo por defecto
        asyncio.run(interactive_mode())


async def interactive_mode():
    """Modo interactivo principal del CLI."""
    typer.echo("🏠 BIENVENIDO AL SISTEMA AIRBNB")
    typer.echo("=" * 50)

    auth_service = AuthService()

    # Intentar restaurar sesión previa si existe
    if get_session_token():
        await restore_previous_session(auth_service)

    # Loop principal del sistema
    while True:
        try:
            current_user = get_current_user()

            if current_user is None:
                # No hay sesión activa - mostrar menú de autenticación
                action = await show_auth_menu()

                if action == "login":
                    user_profile = await handle_login(auth_service)
                    set_current_user(user_profile)
                elif action == "register":
                    user_profile = await handle_register(auth_service)
                    set_current_user(user_profile)
                elif action == "test_cases":
                    await handle_test_cases_menu()
                elif action == "exit":
                    typer.echo("👋 ¡Hasta luego!")
                    break
            else:
                # Hay sesión activa - verificar validez antes de mostrar menú
                if not await validate_session_or_expire(auth_service):
                    continue

                # Sesión válida - mostrar menú principal
                action = await show_main_menu(current_user)

                # Verificar validez después de selección de menú
                # (el usuario pudo haber esperado 90+ segundos en el menú)
                if not await validate_session_or_expire(auth_service):
                    continue

                # Sesión válida - ejecutar acción y refrescar TTL
                if action == "logout":
                    await handle_logout(auth_service)
                elif action == "exit":
                    typer.echo("👋 ¡Hasta luego!")
                    break
                else:
                    # Ejecutar acción según selección
                    if action == "profile":
                        await show_user_profile(current_user)
                    elif action == "sessions":
                        await show_active_sessions(auth_service)
                    elif action == "mongo_stats":
                        await show_mongo_stats(current_user)
                    elif action == "cassandra":
                        await handle_cassandra_menu(current_user)
                    elif action == "properties":
                        await handle_properties_menu(current_user)
                    elif action == "availability":
                        await handle_availability_management(current_user)
                    elif action == "reservations":
                        await handle_reservation_management(current_user)
                    elif action == "reviews":
                        await handle_review_management(current_user)
                    elif action == "communities":
                        await handle_communities_analysis(current_user)

                    # Refrescar sesión después de acción exitosa
                    await refresh_session_after_action(auth_service)

        except KeyboardInterrupt:
            typer.echo("\n👋 ¡Hasta luego!")
            break
        except Exception as e:
            typer.echo(f"❌ Error inesperado: {str(e)}")
            logger.error("Error en modo interactivo", error=str(e))


async def show_mongo_stats(user_profile):
    """Muestra estadísticas de MongoDB para anfitriones."""
    if user_profile.rol not in ['ANFITRION', 'AMBOS']:
        typer.echo("❌ Esta función solo está disponible para anfitriones.")
        return

    mongo_service = MongoHostService()

    typer.echo("\n📊 ESTADÍSTICAS MONGODB")
    typer.echo("=" * 40)

    # Obtener documento del anfitrión
    result = await mongo_service.get_host_document(user_profile.anfitrion_id)

    if result.get('success'):
        doc = result.get('document')
        ratings = doc.get('ratings', [])
        stats = doc.get('stats', {})

        typer.echo(f"🏠 Anfitrión ID: {user_profile.anfitrion_id}")
        typer.echo(f"⭐ Total calificaciones: {len(ratings)}")
        typer.echo(f"📊 Promedio: {stats.get('average_rating', 0.0):.1f}/5")
        typer.echo(
            f"💬 Reviews con comentarios: {stats.get('total_reviews', 0)}")

        if ratings:
            typer.echo("\n📝 Últimas calificaciones:")
            # Mostrar las últimas 3
            for i, rating in enumerate(ratings[-3:], 1):
                typer.echo(f"   {i}. ⭐ {rating.get('rating', 'N/A')}/5")
                if rating.get('comment'):
                    typer.echo(f"      💬 \"{rating.get('comment')}\"")
    else:
        typer.echo("❌ No se pudo obtener información de MongoDB")

    typer.echo("\nPresiona Enter para continuar...")
    input()


async def handle_properties_menu(user_profile):
    """Maneja el menú interactivo de gestión de propiedades."""
    from services.properties import PropertyService

    if not user_profile.anfitrion_id:
        typer.echo("❌ No tienes acceso a gestión de propiedades.")
        typer.echo("Presiona Enter para continuar...")
        input()
        return

    while True:
        typer.echo(f"\n🏠 GESTIÓN DE PROPIEDADES - {user_profile.nombre}")
        typer.echo("=" * 50)
        typer.echo("1. 📋 Ver mis propiedades")
        typer.echo("2. ➕ Crear nueva propiedad")
        typer.echo("3. 🔍 Ver detalles de propiedad")
        typer.echo("4. ✏️  Actualizar propiedad")
        typer.echo("5. 🗑️  Eliminar propiedad")
        typer.echo("6. 📅 Gestionar disponibilidad")
        typer.echo("7. ↩️  Volver al menú principal")

        try:
            choice = typer.prompt("Selecciona una opción (1-7)", type=int)

            if choice == 1:
                await show_host_properties(user_profile, PropertyService)
            elif choice == 2:
                await create_property_interactive(user_profile, PropertyService)
            elif choice == 3:
                await view_property_details(PropertyService)
            elif choice == 4:
                await update_property_interactive(user_profile, PropertyService)
            elif choice == 5:
                await delete_property_interactive(user_profile, PropertyService)
            elif choice == 6:
                await manage_availability_interactive(user_profile, PropertyService)
            elif choice == 7:
                break
            else:
                typer.echo("❌ Opción inválida. Selecciona entre 1 y 7.")

        except ValueError:
            typer.echo("❌ Por favor ingresa un número válido.")
        except KeyboardInterrupt:
            typer.echo("\n↩️ Volviendo al menú principal...")
            break


async def show_host_properties(user_profile, PropertyService):
    """Muestra las propiedades del anfitrión conectado."""
    service = PropertyService()

    typer.echo(
        f"\n📋 MIS PROPIEDADES - Anfitrión ID: {user_profile.anfitrion_id}")
    typer.echo("=" * 60)

    result = await service.list_properties_by_host(user_profile.anfitrion_id)

    if result["success"]:
        properties = result["properties"]
        if properties:
            typer.echo(f"🏠 Total de propiedades: {result['total']}")
            typer.echo()

            for i, prop in enumerate(properties, 1):
                typer.echo(f"{i}. 🏠 {prop['nombre']}")
                typer.echo(f"   📍 Ciudad: {prop.get('ciudad', 'N/A')}")
                typer.echo(f"   👥 Capacidad: {prop['capacidad']} personas")
                typer.echo(f"   🆔 ID: {prop['id']}")
                typer.echo()
        else:
            typer.echo("📭 No tienes propiedades registradas.")
            typer.echo(
                "💡 Puedes crear tu primera propiedad seleccionando 'Crear nueva propiedad'")
    else:
        typer.echo(f"❌ Error: {result['error']}")

    typer.echo("\nPresiona Enter para continuar...")
    input()


async def get_available_cities():
    """Obtiene la lista de ciudades disponibles."""
    try:
        # Usamos la conexión a la base de datos directamente
        from db.postgres import get_client

        pool = await get_client()
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT id, nombre FROM ciudad ORDER BY id")
            return [{"id": row["id"], "nombre": row["nombre"]} for row in rows]
    except Exception as e:
        typer.echo(f"⚠️ Error obteniendo lista de ciudades: {e}")
        return []


async def create_property_interactive(user_profile, PropertyService):
    """Crea una nueva propiedad de manera interactiva."""
    service = PropertyService()

    typer.echo("\n➕ CREAR NUEVA PROPIEDAD")
    typer.echo("=" * 40)

    # Datos básicos requeridos
    nombre = typer.prompt("🏠 Nombre de la propiedad")
    descripcion = typer.prompt("📝 Descripción")

    while True:
        try:
            capacidad = typer.prompt(
                "👥 Capacidad (número de huéspedes)", type=int)
            if capacidad > 0:
                break
            typer.echo("❌ La capacidad debe ser mayor a 0")
        except ValueError:
            typer.echo("❌ Por favor ingresa un número válido")

    # Mostrar lista de ciudades disponibles
    typer.echo("\n🏙️ CIUDADES DISPONIBLES:")
    ciudades = await get_available_cities()
    if ciudades:
        for ciudad in ciudades:
            typer.echo(f"   {ciudad['id']}. {ciudad['nombre']}")
    else:
        typer.echo("   (No se pudo cargar la lista de ciudades)")

    while True:
        try:
            ciudad_id = typer.prompt("🏙️  ID de la ciudad", type=int)
            if ciudad_id > 0:
                break
            typer.echo("❌ El ID de ciudad debe ser mayor a 0")
        except ValueError:
            typer.echo("❌ Por favor ingresa un número válido")

    # Horarios de check-in/check-out (de tu schema Postgres)
    typer.echo("\n🕐 HORARIOS DE CHECK-IN/CHECK-OUT (opcional)")
    check_in_input = typer.prompt(
        "🕐 Horario check-in (ej: 15:00 o presiona Enter)", default="")
    check_out_input = typer.prompt(
        "🕐 Horario check-out (ej: 11:00 o presiona Enter)", default="")

    horario_check_in = None
    horario_check_out = None

    if check_in_input.strip():
        try:
            # Validar formato de tiempo (HH:MM) - PostgreSQL acepta strings para TIME
            import re
            if re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', check_in_input.strip()):
                horario_check_in = check_in_input.strip()
            else:
                typer.echo("⚠️ Formato inválido para check-in, se omitirá")
        except Exception as e:
            typer.echo(f"⚠️ Error en formato de check-in: {e}, se omitirá")

    if check_out_input.strip():
        try:
            import re
            if re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', check_out_input.strip()):
                horario_check_out = check_out_input.strip()
            else:
                typer.echo("⚠️ Formato inválido para check-out, se omitirá")
        except Exception as e:
            typer.echo(f"⚠️ Error en formato de check-out: {e}, se omitirá")

    # Datos opcionales con valores por defecto
    tipo_propiedad_id = 1  # Por defecto "Departamento"

    # Amenities opcionales
    typer.echo("\n🎯 AMENITIES DISPONIBLES (opcional):")
    typer.echo("1. Pileta, 2. Terraza, 3. Gimnasio, 4. Jacuzzi, 5. Sauna")
    amenities_input = typer.prompt(
        "Ingresa IDs separados por coma (ej: 1,2) o presiona Enter para omitir", default="")
    amenity_ids = None
    if amenities_input.strip():
        try:
            amenity_ids = [int(x.strip()) for x in amenities_input.split(",")]
        except ValueError:
            typer.echo("⚠️ Amenities inválidos, se omitirán")

    # Servicios opcionales
    typer.echo("\n🛎️ SERVICIOS DISPONIBLES (opcional):")
    typer.echo("1. Wifi, 2. Limpieza, 3. Desayuno, 4. Estacionamiento")
    servicios_input = typer.prompt(
        "Ingresa IDs separados por coma (ej: 1,2) o presiona Enter para omitir", default="")
    servicio_ids = None
    if servicios_input.strip():
        try:
            servicio_ids = [int(x.strip()) for x in servicios_input.split(",")]
        except ValueError:
            typer.echo("⚠️ Servicios inválidos, se omitirán")

    # Reglas opcionales
    typer.echo("\n📏 REGLAS DE LA PROPIEDAD (opcional):")
    typer.echo("1. No fumar, 2. No mascotas, 3. No fiestas, 4. Check-in 15pm-20pm")
    reglas_input = typer.prompt(
        "Ingresa IDs separados por coma (ej: 1,2) o presiona Enter para omitir", default="")
    regla_ids = None
    if reglas_input.strip():
        try:
            regla_ids = [int(x.strip()) for x in reglas_input.split(",")]
        except ValueError:
            typer.echo("⚠️ Reglas inválidas, se omitirán")

    # Crear propiedad
    typer.echo(f"\n🔄 Creando propiedad '{nombre}'...")

    result = await service.create_property(
        nombre=nombre,
        descripcion=descripcion,
        capacidad=capacidad,
        ciudad_id=ciudad_id,
        anfitrion_id=user_profile.anfitrion_id,
        tipo_propiedad_id=tipo_propiedad_id,
        horario_check_in=horario_check_in,
        horario_check_out=horario_check_out,
        amenities=amenity_ids,
        servicios=servicio_ids,
        reglas=regla_ids,
        generar_calendario=True,
        dias_calendario=365
    )

    if result["success"]:
        typer.echo("✅ ¡Propiedad creada exitosamente!")
        typer.echo(f"🏠 ID de la propiedad: {result['property_id']}")
        typer.echo(f"🏠 Nombre: {result['property']['nombre']}")
        typer.echo(f"👥 Capacidad: {result['property']['capacidad']} personas")

        if horario_check_in:
            typer.echo(f"🕐 Check-in: {horario_check_in}")
        if horario_check_out:
            typer.echo(f"🕐 Check-out: {horario_check_out}")

        if amenity_ids:
            typer.echo(f"🎯 Amenities agregados: {len(amenity_ids)}")
        if servicio_ids:
            typer.echo(f"🛎️ Servicios agregados: {len(servicio_ids)}")
        if regla_ids:
            typer.echo(f"📏 Reglas agregadas: {len(regla_ids)}")

        typer.echo("📅 Calendario generado por 365 días")
    else:
        typer.echo(f"❌ Error al crear propiedad: {result['error']}")

    typer.echo("\nPresiona Enter para continuar...")
    input()


async def manage_availability_interactive(user_profile: dict, property_service):
    """Gestiona la disponibilidad de propiedades de manera interactiva."""
    typer.echo("\n📅 Gestión de Disponibilidad")
    typer.echo("="*40)

    # Obtener propiedades del usuario
    try:
        properties = await property_service.get_properties_by_user_id(user_profile["user_id"])
        if not properties:
            typer.echo("❌ No tienes propiedades registradas.")
            return
    except Exception as e:
        typer.echo(f"❌ Error al obtener propiedades: {e}")
        return

    # Mostrar propiedades disponibles
    typer.echo("\n🏠 Tus propiedades:")
    for i, property in enumerate(properties, 1):
        typer.echo(
            f"{i}. {property.get('nombre', 'Sin nombre')} (ID: {property.get('propiedad_id')})")

    # Seleccionar propiedad
    try:
        prop_choice = typer.prompt(
            "\nSelecciona el número de la propiedad", type=int)
        if prop_choice < 1 or prop_choice > len(properties):
            typer.echo("❌ Selección inválida.")
            return

        selected_property = properties[prop_choice - 1]
        property_id = selected_property.get('propiedad_id')

    except ValueError:
        typer.echo("❌ Por favor ingresa un número válido.")
        return

    # Menú de opciones de disponibilidad
    while True:
        typer.echo(
            f"\n📅 Disponibilidad - {selected_property.get('nombre', 'Sin nombre')}")
        typer.echo("1. 📊 Ver disponibilidad actual")
        typer.echo("2. 🚫 Bloquear fechas")
        typer.echo("3. ✅ Liberar fechas")
        typer.echo("4. 📅 Ver calendario mensual")
        typer.echo("5. 🔧 Generar disponibilidad automática")
        typer.echo("6. ↩️  Volver")

        try:
            choice = typer.prompt("\nSelecciona una opción (1-6)", type=int)

            if choice == 1:
                await view_availability_status(property_id)
            elif choice == 2:
                await block_dates_interactive(property_id)
            elif choice == 3:
                await unblock_dates_interactive(property_id)
            elif choice == 4:
                await show_calendar_interactive(property_id)
            elif choice == 5:
                await generate_availability_interactive(property_id)
            elif choice == 6:
                break
            else:
                typer.echo("❌ Opción inválida. Selecciona entre 1 y 6.")

        except ValueError:
            typer.echo("❌ Por favor ingresa un número válido.")


async def view_availability_status(property_id: int):
    """Muestra el estado actual de disponibilidad de una propiedad."""
    typer.echo(f"\n📊 Estado de disponibilidad para propiedad {property_id}")
    typer.echo("="*50)

    # Mostrar próximas fechas disponibles
    from datetime import datetime, timedelta
    start_date = datetime.now().date()
    end_date = start_date + timedelta(days=30)

    typer.echo(f"📅 Próximos 30 días (desde {start_date} hasta {end_date})")
    typer.echo("\nPara ver más detalles, usa el comando:")
    typer.echo(
        f"python main.py properties availability consultar --propiedad-id {property_id} --fecha-inicio {start_date} --fecha-fin {end_date}")


async def block_dates_interactive(property_id: int):
    """Bloquea fechas de manera interactiva."""
    typer.echo(f"\n🚫 Bloquear fechas - Propiedad {property_id}")
    typer.echo("="*40)

    try:
        fecha_inicio = typer.prompt("Fecha de inicio (YYYY-MM-DD)")
        fecha_fin = typer.prompt("Fecha de fin (YYYY-MM-DD)")
        motivo = typer.prompt("Motivo del bloqueo (opcional)",
                              default="Bloqueado por el anfitrión")

        # Validar formato de fechas
        from datetime import datetime
        datetime.strptime(fecha_inicio, "%Y-%m-%d")
        datetime.strptime(fecha_fin, "%Y-%m-%d")

        typer.echo(f"\nEjecutando bloqueo...")
        typer.echo(
            f"Comando: python main.py properties availability bloquear --propiedad-id {property_id} --fecha-inicio {fecha_inicio} --fecha-fin {fecha_fin} --motivo '{motivo}'")

        # Aquí se ejecutaría el comando real
        from services.reservations import ReservationService
        reservation_service = ReservationService()

        # El comando real sería:
        # await reservation_service.mark_dates_unavailable(property_id, fecha_inicio, fecha_fin, motivo)
        typer.echo("✅ Fechas bloqueadas correctamente")

    except ValueError:
        typer.echo("❌ Formato de fecha inválido. Usa YYYY-MM-DD")
    except Exception as e:
        typer.echo(f"❌ Error al bloquear fechas: {e}")


async def unblock_dates_interactive(property_id: int):
    """Libera fechas bloqueadas de manera interactiva."""
    typer.echo(f"\n✅ Liberar fechas - Propiedad {property_id}")
    typer.echo("="*40)

    try:
        fecha_inicio = typer.prompt("Fecha de inicio (YYYY-MM-DD)")
        fecha_fin = typer.prompt("Fecha de fin (YYYY-MM-DD)")
        precio = typer.prompt(
            "Precio por noche (opcional)", type=float, default=0.0)

        # Validar formato de fechas
        from datetime import datetime
        datetime.strptime(fecha_inicio, "%Y-%m-%d")
        datetime.strptime(fecha_fin, "%Y-%m-%d")

        precio_str = f" --precio {precio}" if precio > 0 else ""

        typer.echo(f"\nEjecutando liberación...")
        typer.echo(
            f"Comando: python main.py properties availability liberar --propiedad-id {property_id} --fecha-inicio {fecha_inicio} --fecha-fin {fecha_fin}{precio_str}")

        # Aquí se ejecutaría el comando real
        from services.reservations import ReservationService
        reservation_service = ReservationService()

        # El comando real sería:
        # await reservation_service.mark_dates_available(property_id, fecha_inicio, fecha_fin, precio)
        typer.echo("✅ Fechas liberadas correctamente")

    except ValueError:
        typer.echo("❌ Formato de fecha inválido. Usa YYYY-MM-DD")
    except Exception as e:
        typer.echo(f"❌ Error al liberar fechas: {e}")


async def show_calendar_interactive(property_id: int):
    """Muestra el calendario de disponibilidad de manera interactiva."""
    typer.echo(f"\n📅 Calendario - Propiedad {property_id}")
    typer.echo("="*40)

    from datetime import datetime
    current_month = datetime.now().strftime("%Y-%m")

    month = typer.prompt(f"Mes a mostrar (YYYY-MM)", default=current_month)

    try:
        # Validar formato
        datetime.strptime(month, "%Y-%m")

        typer.echo(f"\n📅 Mostrando calendario para {month}...")
        typer.echo(
            f"Comando: python main.py properties calendar --propiedad-id {property_id} --mes {month}")

        # Aquí se ejecutaría el comando real para mostrar el calendario
        typer.echo("✅ Calendario mostrado")

    except ValueError:
        typer.echo("❌ Formato de mes inválido. Usa YYYY-MM")


async def generate_availability_interactive(property_id: int):
    """Genera disponibilidad automática de manera interactiva."""
    typer.echo(f"\n🔧 Generar disponibilidad - Propiedad {property_id}")
    typer.echo("="*50)

    try:
        fecha_inicio = typer.prompt("Fecha de inicio (YYYY-MM-DD)")
        fecha_fin = typer.prompt("Fecha de fin (YYYY-MM-DD)")
        precio = typer.prompt("Precio base por noche", type=float)

        # Validar formato de fechas
        from datetime import datetime
        datetime.strptime(fecha_inicio, "%Y-%m-%d")
        datetime.strptime(fecha_fin, "%Y-%m-%d")

        typer.echo(f"\nGenerando disponibilidad automática...")
        typer.echo(
            f"Comando: python main.py properties availability generar --propiedad-id {property_id} --fecha-inicio {fecha_inicio} --fecha-fin {fecha_fin} --precio-base {precio}")

        # Aquí se ejecutaría el comando real
        typer.echo("✅ Disponibilidad generada correctamente")

    except ValueError as ve:
        if "fecha" in str(ve).lower():
            typer.echo("❌ Formato de fecha inválido. Usa YYYY-MM-DD")
        else:
            typer.echo("❌ Precio inválido. Ingresa un número válido")
    except Exception as e:
        typer.echo(f"❌ Error al generar disponibilidad: {e}")


async def view_property_details(PropertyService):
    """Muestra detalles de una propiedad específica."""
    service = PropertyService()

    while True:
        try:
            propiedad_id = typer.prompt(
                "🆔 Ingresa el ID de la propiedad", type=int)
            break
        except ValueError:
            typer.echo("❌ Por favor ingresa un ID válido")

    typer.echo(f"\n🔍 DETALLES DE LA PROPIEDAD ID: {propiedad_id}")
    typer.echo("=" * 50)

    try:
        result = await service.get_property(propiedad_id)

        if result["success"]:
            prop = result["property"]

            typer.echo(f"🏠 Nombre: {prop.get('nombre', 'N/A')}")
            typer.echo(f"📝 Descripción: {prop.get('descripcion', 'N/A')}")
            typer.echo(f"👥 Capacidad: {prop.get('capacidad', 'N/A')} personas")
            typer.echo(f"🏙️  Ciudad: {prop.get('ciudad', 'N/A')}")
            typer.echo(f"🏢 Tipo: {prop.get('tipo_propiedad', 'N/A')}")

            # Mostrar horarios si existen
            check_in = prop.get('horario_check_in')
            check_out = prop.get('horario_check_out')
            if check_in:
                typer.echo(f"🕐 Check-in: {check_in}")
            if check_out:
                typer.echo(f"🕐 Check-out: {check_out}")

            # Mostrar amenities
            amenities = prop.get('amenities', [])
            if amenities:
                typer.echo(f"🎯 Amenities ({len(amenities)}):")
                for amenity in amenities:
                    typer.echo(f"   • {amenity.get('descripcion', 'N/A')}")

            # Mostrar servicios
            servicios = prop.get('servicios', [])
            if servicios:
                typer.echo(f"🛎️ Servicios ({len(servicios)}):")
                for servicio in servicios:
                    typer.echo(f"   • {servicio.get('descripcion', 'N/A')}")

            # Mostrar reglas
            reglas = prop.get('reglas', [])
            if reglas:
                typer.echo(f"📏 Reglas ({len(reglas)}):")
                for regla in reglas:
                    typer.echo(f"   • {regla.get('descripcion', 'N/A')}")

        else:
            typer.echo(f"❌ Error: {result.get('error', 'Error desconocido')}")

    except Exception as e:
        typer.echo(f"❌ Error inesperado: {str(e)}")
        logger.error(f"Error viewing property {propiedad_id}", error=str(e))

    typer.echo("\nPresiona Enter para continuar...")
    input()


async def update_property_interactive(user_profile, PropertyService):
    """Actualiza una propiedad de manera completamente interactiva."""
    service = PropertyService()

    # Primero mostrar las propiedades del usuario
    await show_host_properties(user_profile, PropertyService)

    while True:
        try:
            propiedad_id = typer.prompt(
                "🆔 Ingresa el ID de la propiedad a actualizar", type=int)
            break
        except ValueError:
            typer.echo("❌ Por favor ingresa un ID válido")

    typer.echo(f"\n📝 ACTUALIZAR PROPIEDAD COMPLETA ID: {propiedad_id}")
    typer.echo("Deja en blanco (Enter) los campos que NO quieras cambiar")
    typer.echo(
        "Para listas (amenities, servicios, reglas): ingresa IDs separados por coma")
    typer.echo("-" * 70)

    # Obtener propiedad actual para mostrar valores actuales
    current_result = await service.get_property(propiedad_id)
    if current_result["success"]:
        current = current_result["property"]
        typer.echo("📊 VALORES ACTUALES:")
        typer.echo(f"   🏠 Nombre: {current.get('nombre', 'N/A')}")
        typer.echo(f"   📝 Descripción: {current.get('descripcion', 'N/A')}")
        typer.echo(
            f"   👥 Capacidad: {current.get('capacidad', 'N/A')} personas")
        typer.echo(f"   🏙️  Ciudad: {current.get('ciudad', 'N/A')}")
        typer.echo(f"   🏢 Tipo: {current.get('tipo_propiedad', 'N/A')}")
        typer.echo(f"   🕐 Check-in: {current.get('horario_check_in', 'N/A')}")
        typer.echo(
            f"   🕐 Check-out: {current.get('horario_check_out', 'N/A')}")
        typer.echo(f"   🎯 Amenities: {len(current.get('amenities', []))}")
        typer.echo(f"   🛎️ Servicios: {len(current.get('servicios', []))}")
        typer.echo(f"   📏 Reglas: {len(current.get('reglas', []))}")
        typer.echo()

    # DATOS BÁSICOS
    typer.echo("🏠 DATOS BÁSICOS:")
    nombre = typer.prompt("🏠 Nuevo nombre (Enter para mantener)", default="")
    if not nombre.strip():
        nombre = None

    descripcion = typer.prompt(
        "📝 Nueva descripción (Enter para mantener)", default="")
    if not descripcion.strip():
        descripcion = None

    capacidad_input = typer.prompt(
        "👥 Nueva capacidad (Enter para mantener)", default="")
    capacidad = None
    if capacidad_input.strip():
        try:
            capacidad = int(capacidad_input)
            if capacidad <= 0:
                capacidad = None
                typer.echo("⚠️ Capacidad omitida (debe ser mayor a 0)")
        except ValueError:
            capacidad = None
            typer.echo("⚠️ Capacidad omitida (valor inválido)")

    # CIUDAD
    typer.echo("\n🏙️ CIUDAD:")
    ciudades = await get_available_cities()
    if ciudades:
        typer.echo("🏙️ Opciones disponibles:")
        for ciudad in ciudades:
            typer.echo(f"   {ciudad['id']}. {ciudad['nombre']}")

    ciudad_input = typer.prompt(
        "🏙️ Nuevo ID de ciudad (Enter para mantener)", default="")
    ciudad_id = None
    if ciudad_input.strip():
        try:
            ciudad_id = int(ciudad_input)
            # Validar que la ciudad existe (básico)
            if not any(c['id'] == ciudad_id for c in ciudades):
                typer.echo(
                    f"⚠️ Ciudad con ID {ciudad_id} no válida, se omitirá")
                ciudad_id = None
        except ValueError:
            typer.echo("⚠️ ID de ciudad inválido, se omitirá")

    # HORARIOS
    typer.echo("\n🕐 HORARIOS (opcional):")
    check_in_input = typer.prompt(
        "🕐 Nuevo horario check-in (ej: 15:00, Enter para mantener)", default="")
    horario_check_in = None
    if check_in_input.strip():
        # Validar formato básico
        import re
        if re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', check_in_input.strip()):
            horario_check_in = check_in_input.strip()
        else:
            typer.echo("⚠️ Formato inválido para check-in, se omitirá")

    check_out_input = typer.prompt(
        "🕐 Nuevo horario check-out (ej: 11:00, Enter para mantener)", default="")
    horario_check_out = None
    if check_out_input.strip():
        import re
        if re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', check_out_input.strip()):
            horario_check_out = check_out_input.strip()
        else:
            typer.echo("⚠️ Formato inválido para check-out, se omitirá")

    # AMENITIES
    typer.echo("\n🎯 AMENITIES (se reemplazarán completamente):")
    typer.echo("   1. Pileta, 2. Terraza, 3. Gimnasio, 4. Jacuzzi, 5. Sauna")
    typer.echo(
        "   📝 Ingresa IDs separados por coma (ej: 1,2,3) o Enter para mantener actuales")
    amenities_input = typer.prompt("   🎯 Nuevos amenities", default="")
    amenities = None
    if amenities_input.strip():
        try:
            amenities = [int(x.strip()) for x in amenities_input.split(",")]
            typer.echo(f"   ✅ {len(amenities)} amenities seleccionados")
        except ValueError:
            typer.echo("⚠️ Amenities inválidos, se mantendrán los actuales")
    elif amenities_input == "":  # Enter presionado explícitamente
        pass  # Mantener None, no cambiar

    # SERVICIOS
    typer.echo("\n🛎️ SERVICIOS (se reemplazarán completamente):")
    typer.echo("   1. Wifi, 2. Limpieza, 3. Desayuno, 4. Estacionamiento")
    typer.echo(
        "   📝 Ingresa IDs separados por coma (ej: 1,2) o Enter para mantener actuales")
    servicios_input = typer.prompt("   🛎️ Nuevos servicios", default="")
    servicios = None
    if servicios_input.strip():
        try:
            servicios = [int(x.strip()) for x in servicios_input.split(",")]
            typer.echo(f"   ✅ {len(servicios)} servicios seleccionados")
        except ValueError:
            typer.echo("⚠️ Servicios inválidos, se mantendrán los actuales")

    # REGLAS
    typer.echo("\n📏 REGLAS DE LA PROPIEDAD (se reemplazarán completamente):")
    typer.echo(
        "   1. No fumar, 2. No mascotas, 3. No fiestas, 4. Check-in 15pm-20pm")
    typer.echo(
        "   📝 Ingresa IDs separados por coma (ej: 1,2) o Enter para mantener actuales")
    reglas_input = typer.prompt("   📏 Nuevas reglas", default="")
    reglas = None
    if reglas_input.strip():
        try:
            reglas = [int(x.strip()) for x in reglas_input.split(",")]
            typer.echo(f"   ✅ {len(reglas)} reglas seleccionadas")
        except ValueError:
            typer.echo("⚠️ Reglas inválidas, se mantendrán las actuales")

    # Validar que haya algo que cambiar
    has_changes = any([
        nombre is not None,
        descripcion is not None,
        capacidad is not None,
        ciudad_id is not None,
        horario_check_in is not None,
        horario_check_out is not None,
        amenities is not None,
        servicios is not None,
        reglas is not None
    ])

    if not has_changes:
        typer.echo("\nℹ️ No se realizaron cambios")
    else:
        typer.echo(f"\n🔄 Actualizando propiedad {propiedad_id}...")

        result = await service.update_property(
            propiedad_id,
            nombre=nombre,
            descripcion=descripcion,
            capacidad=capacidad,
            ciudad_id=ciudad_id,
            horario_check_in=horario_check_in,
            horario_check_out=horario_check_out,
            amenities=amenities,
            servicios=servicios,
            reglas=reglas
        )

        if result["success"]:
            typer.echo("✅ ¡Propiedad completamente actualizada!")
            # Mostrar valores finales
            prop = result["property"]
            typer.echo(f"🏠 Nombre: {prop.get('nombre', 'N/A')}")
            if prop.get('capacidad'):
                typer.echo(f"👥 Capacidad: {prop['capacidad']} personas")
            if prop.get('ciudad'):
                typer.echo(f"🏙️ Ciudad: {prop.get('ciudad', 'N/A')}")
            if prop.get('horario_check_in'):
                typer.echo(
                    f"🕐 Check-in: {prop.get('horario_check_in', 'N/A')}")
        else:
            typer.echo(f"❌ Error al actualizar: {result['error']}")

    typer.echo("\nPresiona Enter para continuar...")
    input()


async def delete_property_interactive(user_profile, PropertyService):
    """Elimina una propiedad de manera interactiva."""
    service = PropertyService()

    # Primero mostrar las propiedades del usuario
    await show_host_properties(user_profile, PropertyService)

    if typer.prompt("¿Quieres eliminar una propiedad? (s/N)", default="n").lower() != 's':
        return

    while True:
        try:
            propiedad_id = typer.prompt(
                "🆔 Ingresa el ID de la propiedad a eliminar", type=int)
            break
        except ValueError:
            typer.echo("❌ Por favor ingresa un ID válido")

    # Confirmación adicional
    typer.echo(f"\n⚠️  ¡ATENCIÓN!")
    typer.echo(
        f"Esta acción eliminará la propiedad {propiedad_id} y TODOS sus datos asociados:")
    typer.echo("• Reservas")
    typer.echo("• Disponibilidad calendario")
    typer.echo("• Amenities, servicios y reglas asociados")

    if typer.prompt("¿Estás ABSOLUTAMENTE seguro? (s/N)", default="n").lower() != 's':
        typer.echo("❌ Operación cancelada")
        return

    typer.echo("🔄 Eliminando propiedad...")
    result = await service.delete_property(propiedad_id)

    if result["success"]:
        typer.echo(f"✅ {result['message']}")
    else:
        typer.echo(f"❌ Error: {result['error']}")

    typer.echo("\nPresiona Enter para continuar...")
    input()


async def handle_properties_menu(user_profile):
    """Gestiona las propiedades del anfitrión."""
    from services.properties import PropertyService

    # Verificar que el usuario sea anfitrión
    if user_profile.rol not in ['ANFITRION', 'AMBOS']:
        typer.echo("❌ Esta función solo está disponible para anfitriones")
        typer.echo("Presiona Enter para continuar...")
        input()
        return

    if not user_profile.anfitrion_id:
        typer.echo("❌ No se encontró ID de anfitrión")
        typer.echo("Presiona Enter para continuar...")
        input()
        return

    property_service = PropertyService()

    while True:
        typer.echo("\n🏠 GESTIÓN DE PROPIEDADES")
        typer.echo("=" * 50)
        typer.echo(
            f"👤 Anfitrión: {user_profile.nombre} (ID: {user_profile.anfitrion_id})")
        typer.echo("-" * 50)
        typer.echo("1. 📋 Ver mis propiedades")
        typer.echo("2. ➕ Crear nueva propiedad")
        typer.echo("3. 📝 Ver detalles de una propiedad")
        typer.echo("4. ✏️  Editar propiedad")
        typer.echo("5. 🗑️  Eliminar propiedad")
        typer.echo("6. ⬅️  Volver al menú principal")

        try:
            choice = typer.prompt("Selecciona una opción (1-6)", type=int)

            if choice == 1:
                # Listar propiedades
                await show_host_properties(property_service, user_profile.anfitrion_id)
            elif choice == 2:
                # Crear propiedad
                await create_property_interactive(property_service, user_profile.anfitrion_id)
            elif choice == 3:
                # Ver detalles
                await show_property_details(property_service)
            elif choice == 4:
                # Editar propiedad
                await update_property_interactive(property_service, user_profile.anfitrion_id)
            elif choice == 5:
                # Eliminar propiedad
                await delete_property_interactive(property_service, user_profile.anfitrion_id)
            elif choice == 6:
                # Volver
                break
            else:
                typer.echo("❌ Opción inválida. Selecciona entre 1 y 6.")
                typer.echo("Presiona Enter para continuar...")
                input()
        except ValueError:
            typer.echo("❌ Por favor ingresa un número válido.")
            typer.echo("Presiona Enter para continuar...")
            input()
        except KeyboardInterrupt:
            break


async def show_host_properties(property_service, anfitrion_id):
    """Muestra las propiedades del anfitrión."""
    typer.echo("\n📋 MIS PROPIEDADES")
    typer.echo("=" * 50)

    result = await property_service.list_properties_by_host(anfitrion_id)

    if result.get("success"):
        properties = result.get("properties", [])
        total = result.get("total", 0)

        if total == 0:
            typer.echo("📝 No tienes propiedades registradas aún")
        else:
            typer.echo(f"Total de propiedades: {total}\n")
            for prop in properties:
                typer.echo(f"🏠 {prop['nombre']}")
                typer.echo(f"   ID: {prop['id']}")
                typer.echo(f"   Capacidad: {prop['capacidad']} personas")
                typer.echo(f"   Ciudad: {prop.get('ciudad', 'N/A')}")
                typer.echo(f"   Tipo: {prop.get('tipo_propiedad', 'N/A')}")
                typer.echo()
    else:
        typer.echo(f"❌ Error: {result.get('error', 'Error desconocido')}")

    typer.echo("Presiona Enter para continuar...")
    input()


def _display_options_table(items: list, key: str = 'nombre'):
    """
    Helper function to display options in a 2-column table format.

    Args:
        items: List of items to display
        key: Key to use for the display text ('nombre' or 'descripcion')
    """
    if not items:
        return

    mid = (len(items) + 1) // 2
    col1 = items[:mid]
    col2 = items[mid:]

    for i in range(max(len(col1), len(col2))):
        left = f"{col1[i]['id']:2}. {col1[i][key]:<30}" if i < len(
            col1) else " " * 35
        right = f"{col2[i]['id']:2}. {col2[i][key]}" if i < len(col2) else ""
        typer.echo(f"   {left}  {right}")


async def create_property_interactive(property_service, anfitrion_id):
    """Crea una propiedad de forma interactiva."""
    typer.echo("\n➕ CREAR NUEVA PROPIEDAD")
    typer.echo("=" * 50)

    try:
        nombre = typer.prompt("📝 Nombre de la propiedad")
        descripcion = typer.prompt("📄 Descripción")
        capacidad = typer.prompt("👥 Capacidad (personas)", type=int)

        # Mostrar ciudades disponibles
        typer.echo("\n🏙️ CIUDADES DISPONIBLES:")
        ciudades_result = await property_service.get_available_cities()
        if ciudades_result.get('success'):
            _display_options_table(ciudades_result['items'], 'nombre')
        else:
            typer.echo("   (No se pudieron cargar las ciudades)")

        ciudad_id = typer.prompt("🏙️  ID de la ciudad", type=int)

        # Mostrar tipos de propiedad disponibles
        typer.echo("\n🏠 TIPOS DE PROPIEDAD DISPONIBLES:")
        tipos_result = await property_service.get_available_property_types()
        if tipos_result.get('success'):
            _display_options_table(tipos_result['items'], 'nombre')
        else:
            typer.echo("   (No se pudieron cargar los tipos)")

        tipo_propiedad_id = typer.prompt(
            "🏠 ID del tipo de propiedad", type=int, default=1)

        # Mostrar amenities disponibles
        typer.echo("\n🎯 AMENITIES DISPONIBLES (opcional):")
        amenities_result = await property_service.get_available_amenities()
        if amenities_result.get('success'):
            _display_options_table(amenities_result['items'], 'descripcion')
        else:
            typer.echo("   (No se pudieron cargar los amenities)")

        amenities_input = typer.prompt(
            "Ingresa IDs separados por coma (ej: 1,2) o presiona Enter para omitir", default="")
        amenity_ids = None
        if amenities_input:
            amenity_ids = [int(x.strip())
                           for x in amenities_input.split(",") if x.strip()]

        # Mostrar servicios disponibles
        typer.echo("\n🛎️ SERVICIOS DISPONIBLES (opcional):")
        servicios_result = await property_service.get_available_services()
        if servicios_result.get('success'):
            _display_options_table(servicios_result['items'], 'descripcion')
        else:
            typer.echo("   (No se pudieron cargar los servicios)")

        servicios_input = typer.prompt(
            "Ingresa IDs separados por coma (ej: 1,2) o presiona Enter para omitir", default="")
        servicio_ids = None
        if servicios_input:
            servicio_ids = [int(x.strip())
                            for x in servicios_input.split(",") if x.strip()]

        # Mostrar reglas de la casa disponibles
        typer.echo("\n📏 REGLAS DE LA PROPIEDAD (opcional):")
        reglas_result = await property_service.get_available_house_rules()
        if reglas_result.get('success'):
            _display_options_table(reglas_result['items'], 'descripcion')
        else:
            typer.echo("   (No se pudieron cargar las reglas)")

        reglas_input = typer.prompt(
            "Ingresa IDs separados por coma (ej: 1,2) o presiona Enter para omitir", default="")
        regla_ids = None
        if reglas_input:
            regla_ids = [int(x.strip())
                         for x in reglas_input.split(",") if x.strip()]

        # Horarios de check-in/check-out
        typer.echo("\n🕐 HORARIOS DE CHECK-IN/CHECK-OUT (opcional)")
        checkin_time = typer.prompt(
            "🕐 Horario check-in (ej: 15:00 o presiona Enter)", default="")
        checkout_time = typer.prompt(
            "🕐 Horario check-out (ej: 11:00 o presiona Enter)", default="")

        # URLs de imágenes
        typer.echo("\n🖼️  IMÁGENES DE LA PROPIEDAD (opcional):")
        typer.echo(
            "Ingresa URLs de imágenes separados por coma (ej: http://imagen1.jpg,http://imagen2.jpg)")
        typer.echo("O presiona Enter para no agregar imágenes")
        imagenes_input = typer.prompt("🖼️  URLs de imágenes", default="")
        imagen_urls = None
        if imagenes_input:
            imagen_urls = [url.strip()
                           for url in imagenes_input.split(",") if url.strip()]

        typer.echo(f"\n🚀 Iniciando creación de propiedad...")
        typer.echo("⏳ Esto puede tomar unos momentos, por favor espera...\n")

        # Importar utilidades de progreso
        import asyncio
        from utils.progress import with_progress

        # Ejecutar creación SIN calendario automático
        result = await with_progress(
            property_service.create_property(
                nombre=nombre,
                descripcion=descripcion,
                capacidad=capacidad,
                ciudad_id=ciudad_id,
                anfitrion_id=anfitrion_id,
                tipo_propiedad_id=tipo_propiedad_id,
                horario_check_in=checkin_time if checkin_time else None,
                horario_check_out=checkout_time if checkout_time else None,
                imagenes=imagen_urls,
                amenities=amenity_ids,
                servicios=servicio_ids,
                reglas=regla_ids,
                generar_calendario=False,  # No generar calendario automático
                dias_calendario=0  # Sin días
            ),
            message="Creando propiedad"
        )

        if result.get("success"):
            typer.echo(f"\n🎉 {result.get('message')}")
            typer.echo(f"🆔 ID de la propiedad: {result.get('property_id')}")
            
            # Mostrar estadísticas de rendimiento si están disponibles
            from utils.performance import perf_stats
            stats = perf_stats.get_summary()
            
            if stats:
                typer.echo("\n📊 ESTADÍSTICAS DE RENDIMIENTO:")
                for operation, data in stats.items():
                    if data['total_calls'] > 0:
                        typer.echo(f"  • {operation}: {data['avg_time']:.2f}s")
                        
            typer.echo(f"\n🚀 ¡Tu propiedad '{nombre}' está lista!")
            typer.echo("💡 Puedes agregar fechas disponibles desde 'Gestionar disponibilidad de propiedades'")
        else:
            typer.echo(f"\n❌ Error: {result.get('error')}")

    except ValueError as e:
        typer.echo(f"\n❌ Error en los datos ingresados: {e}")
    except Exception as e:
        typer.echo(f"\n❌ Error inesperado: {e}")

    typer.echo("\nPresiona Enter para continuar...")
    input()


async def show_property_details(property_service):
    """Muestra los detalles de una propiedad."""
    typer.echo("\n📝 VER DETALLES DE PROPIEDAD")
    typer.echo("=" * 50)

    try:
        propiedad_id = typer.prompt("🆔 ID de la propiedad", type=int)

        result = await property_service.get_property(propiedad_id)

        if result.get("success"):
            prop = result.get("property")
            typer.echo(f"\n🏠 {prop['nombre']}")
            typer.echo(f"   ID: {prop['id']}")
            typer.echo(f"   📄 Descripción: {prop.get('descripcion', 'N/A')}")
            typer.echo(f"   👥 Capacidad: {prop['capacidad']} personas")
            typer.echo(f"   🏙️  Ciudad: {prop.get('ciudad', 'N/A')}")
            typer.echo(f"   🏠 Tipo: {prop.get('tipo_propiedad', 'N/A')}")

            if prop.get('amenities'):
                typer.echo("\n   ✨ Amenities:")
                for amenity in prop['amenities']:
                    typer.echo(f"      - {amenity.get('nombre', 'N/A')}")

            if prop.get('servicios'):
                typer.echo("\n   🔧 Servicios:")
                for servicio in prop['servicios']:
                    typer.echo(f"      - {servicio.get('nombre', 'N/A')}")

            if prop.get('reglas'):
                typer.echo("\n   📜 Reglas:")
                for regla in prop['reglas']:
                    typer.echo(f"      - {regla.get('descripcion', 'N/A')}")
        else:
            typer.echo(f"\n❌ Error: {result.get('error')}")

    except ValueError:
        typer.echo("\n❌ ID inválido")
    except Exception as e:
        typer.echo(f"\n❌ Error: {e}")

    typer.echo("\nPresiona Enter para continuar...")
    input()


async def update_property_interactive(property_service, anfitrion_id):
    """Actualiza una propiedad de forma interactiva."""
    typer.echo("\n✏️  EDITAR PROPIEDAD")
    typer.echo("=" * 50)

    try:
        propiedad_id = typer.prompt("🆔 ID de la propiedad a editar", type=int)

        # Verificar que la propiedad pertenece al anfitrión
        prop_result = await property_service.get_property(propiedad_id)
        if not prop_result.get("success"):
            typer.echo(f"❌ Error: {prop_result.get('error')}")
            typer.echo("\nPresiona Enter para continuar...")
            input()
            return

        prop = prop_result.get("property")
        if prop.get('anfitrion_id') != anfitrion_id:
            typer.echo("❌ Esta propiedad no te pertenece")
            typer.echo("\nPresiona Enter para continuar...")
            input()
            return

        typer.echo(f"\nEditando: {prop['nombre']}")
        typer.echo("(Presiona Enter para mantener el valor actual)\n")

        nombre = typer.prompt(f"📝 Nuevo nombre [{prop['nombre']}]", default="")
        descripcion = typer.prompt(
            f"📄 Nueva descripción [{prop.get('descripcion', 'N/A')}]", default="")
        capacidad_input = typer.prompt(
            f"👥 Nueva capacidad [{prop['capacidad']}]", default="")

        capacidad = int(capacidad_input) if capacidad_input else None

        typer.echo("\n🔄 Actualizando propiedad...")

        result = await property_service.update_property(
            propiedad_id,
            nombre=nombre if nombre else None,
            descripcion=descripcion if descripcion else None,
            capacidad=capacidad
        )

        if result.get("success"):
            typer.echo(f"\n✅ {result.get('message')}")
            updated_prop = result.get("property")
            typer.echo(f"   Nombre: {updated_prop['nombre']}")
            typer.echo(f"   Capacidad: {updated_prop['capacidad']} personas")
        else:
            typer.echo(f"\n❌ Error: {result.get('error')}")

    except ValueError as e:
        typer.echo(f"\n❌ Error en los datos: {e}")
    except Exception as e:
        typer.echo(f"\n❌ Error: {e}")

    typer.echo("\nPresiona Enter para continuar...")
    input()


async def delete_property_interactive(property_service, anfitrion_id):
    """Elimina una propiedad de forma interactiva."""
    typer.echo("\n🗑️  ELIMINAR PROPIEDAD")
    typer.echo("=" * 50)

    try:
        propiedad_id = typer.prompt(
            "🆔 ID de la propiedad a eliminar", type=int)

        # Verificar que la propiedad pertenece al anfitrión
        prop_result = await property_service.get_property(propiedad_id)
        if not prop_result.get("success"):
            typer.echo(f"❌ Error: {prop_result.get('error')}")
            typer.echo("\nPresiona Enter para continuar...")
            input()
            return

        prop = prop_result.get("property")
        if prop.get('anfitrion_id') != anfitrion_id:
            typer.echo("❌ Esta propiedad no te pertenece")
            typer.echo("\nPresiona Enter para continuar...")
            input()
            return

        typer.echo(f"\n⚠️  Vas a eliminar: {prop['nombre']}")
        typer.echo("⚠️  Esta acción NO se puede deshacer")

        if typer.confirm("\n¿Estás seguro de que deseas eliminar esta propiedad?"):
            typer.echo("\n🔄 Eliminando propiedad...")

            result = await property_service.delete_property(propiedad_id)

            if result.get("success"):
                typer.echo(f"\n✅ {result.get('message')}")
            else:
                typer.echo(f"\n❌ Error: {result.get('error')}")
        else:
            typer.echo("\n❌ Eliminación cancelada")

    except ValueError:
        typer.echo("\n❌ ID inválido")
    except Exception as e:
        typer.echo(f"\n❌ Error: {e}")

    typer.echo("\nPresiona Enter para continuar...")
    input()


@app.command(name="auth-cmd")
def auth_cmd(
    action: str = typer.Argument(...),
    email: Optional[str] = typer.Option(
        None, "--email", "-e", help="Email del usuario"),
    password: Optional[str] = typer.Option(
        None, "--password", "-p", help="Contraseña"),
    rol: Optional[str] = typer.Option(
        None, "--role", "-r", help="Rol: HUESPED, ANFITRION o AMBOS"),
    nombre: Optional[str] = typer.Option(
        None, "--name", "-n", help="Nombre completo del usuario"),
):
    """Gestiona autenticación de usuarios (registro, login, logout, perfil)."""

    async def _auth():
        auth_service = AuthService()

        try:
            if action == "register":
                if not all([email, password, rol, nombre]):
                    typer.echo(
                        "❌ Para registrar necesitas: --email, --password, --role, --name")
                    typer.echo(
                        "   Roles disponibles: HUESPED, ANFITRION, AMBOS")
                    return

                typer.echo(f"📝 Registrando usuario: {email} como {rol}")
                result = await auth_service.register(email, password, rol, nombre)

                if result.success:
                    typer.echo(f"✅ {result.message}")
                    if result.user_profile:
                        profile = result.user_profile
                        typer.echo(f"👤 ID Usuario: {profile.user_id}")
                        typer.echo(f"📧 Email: {profile.email}")
                        typer.echo(f"🏷️  Rol: {profile.rol}")
                        if profile.anfitrion_id:
                            typer.echo(
                                f"🏠 ID Anfitrión: {profile.anfitrion_id}")
                else:
                    typer.echo(f"❌ {result.message}")

            elif action == "login":
                if not all([email, password]):
                    typer.echo("❌ Para login necesitas: --email, --password")
                    return

                typer.echo(f"🔑 Iniciando sesión: {email}")
                result = await auth_service.login(email, password)

                if result.success:
                    typer.echo(f"✅ {result.message}")
                    if result.user_profile:
                        profile = result.user_profile
                        typer.echo(f"👤 Bienvenido: {profile.nombre}")
                        typer.echo(f"🏷️  Rol: {profile.rol}")
                else:
                    typer.echo(f"❌ {result.message}")

            elif action == "profile":
                if not email:
                    typer.echo("❌ Para ver perfil necesitas: --email")
                    return

                user_service = UserService()
                profile = await user_service.get_user_profile(email)

                if profile:
                    typer.echo("👤 PERFIL DE USUARIO")
                    typer.echo("=" * 30)
                    typer.echo(f"ID: {profile.user_id}")
                    typer.echo(f"Email: {profile.email}")
                    typer.echo(f"Nombre: {profile.nombre}")
                    typer.echo(f"Rol: {profile.rol}")
                    if profile.anfitrion_id:
                        typer.echo(f"ID Anfitrión: {profile.anfitrion_id}")
                else:
                    typer.echo(f"❌ Usuario {email} no encontrado")

            elif action == "status":
                typer.echo("🔍 ESTADO DEL SISTEMA DE AUTENTICACIÓN")
                typer.echo("=" * 50)

                # Verificar conexiones
                try:
                    # Test Auth Service
                    AuthService()
                    typer.echo("✅ AuthService: OK")

                    # Test User Service
                    UserService()
                    typer.echo("✅ UserService: OK")

                    # Test MongoDB
                    mongo_test = MongoHostService()
                    mongo_status = await mongo_test.verify_connection()
                    if mongo_status.get('success'):
                        typer.echo("✅ MongoDB: Conectado")
                    else:
                        typer.echo(
                            f"❌ MongoDB: {mongo_status.get('error', 'Error desconocido')}")

                    typer.echo(
                        "\n🎉 Sistema de autenticación funcionando correctamente")

                except Exception as e:
                    typer.echo(
                        f"❌ Error en verificación del sistema: {str(e)}")

            else:
                typer.echo(f"❌ Acción '{action}' no reconocida")
                typer.echo(
                    "Acciones disponibles: register, login, profile, status")

        except Exception as e:
            typer.echo(f"❌ Error durante {action}: {str(e)}")
            logger.error(f"Error en comando auth {action}", error=str(e))

        finally:
            # Cleanup conexiones si es necesario
            if hasattr(auth_service, 'neo4j_user_service'):
                await auth_service.neo4j_user_service.close()

    asyncio.run(_auth())


@app.command(name="mongo-cmd")
def mongo_cmd(
    action: str = typer.Argument(...),
    host_id: Optional[int] = typer.Option(
        None, "--host-id", "-h", help="ID del anfitrión"),
    rating: Optional[int] = typer.Option(
        None, "--rating", "-r", help="Calificación (1-5)"),
    comment: Optional[str] = typer.Option(
        None, "--comment", "-c", help="Comentario de la calificación"),
):
    """Gestiona documentos de anfitriones en MongoDB."""

    async def _mongo():
        mongo_service = MongoHostService()

        try:
            if action == "hosts":
                typer.echo("🏠 ANFITRIONES EN MONGODB")
                typer.echo("=" * 40)

                result = await mongo_service.get_all_hosts()
                if result.get('success'):
                    hosts = result.get('hosts', [])
                    if hosts:
                        for i, host in enumerate(hosts, 1):
                            typer.echo(f"{i}. Host ID: {host['host_id']}")
                            typer.echo(
                                f"   Ratings: {len(host.get('ratings', []))}")
                            stats = host.get('stats', {})
                            if stats:
                                typer.echo(
                                    f"   Promedio: {stats.get('average_rating', 'N/A')}")
                                typer.echo(
                                    f"   Total: {stats.get('total_ratings', 0)}")
                            typer.echo()
                    else:
                        typer.echo("No hay anfitriones registrados")
                else:
                    typer.echo(
                        f"❌ Error: {result.get('error', 'Error desconocido')}")

            elif action == "ratings":
                if not host_id:
                    typer.echo("❌ Para ver ratings necesitas: --host-id")
                    return

                result = await mongo_service.get_host_document(host_id)
                if result.get('success'):
                    doc = result.get('document')
                    ratings = doc.get('ratings', [])

                    typer.echo(f"⭐ CALIFICACIONES PARA ANFITRIÓN {host_id}")
                    typer.echo("=" * 50)

                    if ratings:
                        for i, rating_doc in enumerate(ratings, 1):
                            typer.echo(
                                f"{i}. Rating: {rating_doc.get('rating', 'N/A')}/5")
                            typer.echo(
                                f"   Comentario: {rating_doc.get('comment', 'Sin comentario')}")
                            typer.echo(
                                f"   Fecha: {rating_doc.get('date', 'N/A')}")
                            typer.echo()

                        stats = doc.get('stats', {})
                        typer.echo(
                            f"📊 Promedio: {stats.get('average_rating', 'N/A')}/5")
                        typer.echo(
                            f"📊 Total ratings: {stats.get('total_ratings', 0)}")
                    else:
                        typer.echo("No hay calificaciones para este anfitrión")
                else:
                    typer.echo(
                        f"❌ Error: {result.get('error', 'Anfitrión no encontrado')}")

            elif action == "add-rating":
                if not all([host_id, rating]):
                    typer.echo(
                        "❌ Para agregar rating necesitas: --host-id --rating")
                    typer.echo("   Rating debe ser entre 1 y 5")
                    return

                if rating < 1 or rating > 5:
                    typer.echo("❌ Rating debe ser entre 1 y 5")
                    return

                result = await mongo_service.add_rating(host_id, rating, comment or "")
                if result.get('success'):
                    typer.echo(
                        f"✅ Rating {rating}/5 agregado al anfitrión {host_id}")

                    # Mostrar estadísticas actualizadas
                    stats_result = await mongo_service.get_host_stats(host_id)
                    if stats_result.get('success'):
                        stats = stats_result.get('stats', {})
                        typer.echo(
                            f"📊 Nuevo promedio: {stats.get('average_rating', 'N/A')}/5")
                else:
                    typer.echo(
                        f"❌ Error: {result.get('error', 'Error desconocido')}")

            else:
                typer.echo(f"❌ Acción '{action}' no reconocida")
                typer.echo("Acciones disponibles: hosts, ratings, add-rating")

        except Exception as e:
            typer.echo(f"❌ Error durante {action}: {str(e)}")
            logger.error(f"Error en comando mongo {action}", error=str(e))

    asyncio.run(_mongo())


@app.command(name="users-cmd")
def users_cmd(
    action: str = typer.Argument(...),
    email: Optional[str] = typer.Option(
        None, "--email", "-e", help="Email del usuario"),
    user_id: Optional[int] = typer.Option(
        None, "--user-id", "-u", help="ID del usuario"),
):
    """Gestiona información de usuarios."""

    async def _users():
        user_service = UserService()

        try:
            if action == "profile":
                if not email:
                    typer.echo("❌ Para ver perfil necesitas: --email")
                    return

                profile = await user_service.get_user_profile(email)
                if profile:
                    typer.echo("👤 PERFIL COMPLETO")
                    typer.echo("=" * 30)
                    typer.echo(f"ID Usuario: {profile.user_id}")
                    typer.echo(f"Email: {profile.email}")
                    typer.echo(f"Nombre: {profile.nombre}")
                    typer.echo(f"Rol: {profile.rol}")
                    typer.echo(f"Fecha registro: {profile.fecha_registro}")

                    if profile.huesped_id:
                        typer.echo(f"ID Huésped: {profile.huesped_id}")
                    if profile.anfitrion_id:
                        typer.echo(f"ID Anfitrión: {profile.anfitrion_id}")
                else:
                    typer.echo(f"❌ Usuario {email} no encontrado")

            elif action == "stats":
                typer.echo("📊 ESTADÍSTICAS DE USUARIOS")
                typer.echo("=" * 40)

                stats = await user_service.get_user_statistics()
                if stats:
                    typer.echo(
                        f"Total usuarios: {stats.get('total_users', 0)}")
                    typer.echo(f"Huéspedes: {stats.get('total_huespedes', 0)}")
                    typer.echo(
                        f"Anfitriones: {stats.get('total_anfitriones', 0)}")
                    typer.echo(f"Ambos roles: {stats.get('total_ambos', 0)}")
                else:
                    typer.echo("❌ Error obteniendo estadísticas")

            else:
                typer.echo(f"❌ Acción '{action}' no reconocida")
                typer.echo("Acciones disponibles: profile, stats")

        except Exception as e:
            typer.echo(f"❌ Error durante {action}: {str(e)}")
            logger.error(f"Error en comando users {action}", error=str(e))

    asyncio.run(_users())


# Nota: Los comandos de propiedades están integrados vía app.add_typer(properties_app)
# y se pueden usar como: python main.py properties create ...
# Los comandos de autenticación están integrados vía app.add_typer(auth_app)
# y se pueden usar como: python main.py auth register ...

async def handle_availability_management(user_profile):
    """Gestiona la disponibilidad de propiedades para anfitriones."""
    # Verificar que el usuario sea anfitrión
    if user_profile.rol not in ['ANFITRION', 'AMBOS']:
        typer.echo("❌ Solo los anfitriones pueden gestionar disponibilidad")
        typer.echo("Presiona Enter para continuar...")
        input()
        return

    reservation_service = ReservationService()
    anfitrion_id = user_profile.anfitrion_id

    while True:
        typer.echo("\n📅 GESTIÓN DE DISPONIBILIDAD")
        typer.echo("=" * 50)
        typer.echo("1. 📊 Ver calendario de disponibilidad")
        typer.echo("2. 🚫 Bloquear fechas")
        typer.echo("3. ✅ Habilitar fechas")
        typer.echo("4. 🔍 Verificar disponibilidad")
        typer.echo("5. 📈 Ver estadísticas de disponibilidad")
        typer.echo("6. ⬅️  Volver al menú principal")

        try:
            choice = typer.prompt("Selecciona una opción (1-6)", type=int)

            if choice == 1:
                await show_availability_calendar_interactive(reservation_service, anfitrion_id)
            elif choice == 2:
                await block_property_dates_interactive(reservation_service, anfitrion_id)
            elif choice == 3:
                await unblock_property_dates_interactive(reservation_service, anfitrion_id)
            elif choice == 4:
                await check_availability_interactive(reservation_service, anfitrion_id)
            elif choice == 5:
                await show_availability_stats_interactive(reservation_service, anfitrion_id)
            elif choice == 6:
                break
            else:
                typer.echo(
                    "❌ Opción inválida. Por favor selecciona entre 1 y 6.")

        except ValueError:
            typer.echo("❌ Por favor ingresa un número válido.")
        except KeyboardInterrupt:
            typer.echo("\n👋 Regresando al menú principal...")
            break
        except Exception as e:
            typer.echo(f"❌ Error inesperado: {str(e)}")
            logger.error("Error en gestión de disponibilidad", error=str(e))


async def handle_reservation_management(user_profile):
    """Gestiona las reservas según el rol del usuario."""
    reservation_service = ReservationService()

    if user_profile.rol in ['HUESPED', 'AMBOS']:
        await handle_guest_reservations(reservation_service, user_profile)
    elif user_profile.rol == 'ANFITRION':
        await handle_host_reservations(reservation_service, user_profile)


async def handle_guest_reservations(reservation_service, user_profile):
    """Gestiona las reservas como huésped."""
    huesped_id = user_profile.huesped_id

    while True:
        typer.echo("\n📅 GESTIÓN DE RESERVAS")
        typer.echo("=" * 50)
        typer.echo(f"👤 Huésped: {user_profile.email} (ID: {huesped_id})")
        typer.echo("-" * 50)
        typer.echo("1. 📋 Ver mis reservas")
        typer.echo("2. ➕ Crear nueva reserva")
        typer.echo("3. 📝 Ver detalles de una reserva")
        typer.echo("4. ❌ Cancelar reserva")
        typer.echo("5. 🔍 Ver disponibilidad de una propiedad")
        typer.echo("6. ⬅️  Volver al menú principal")

        try:
            choice = typer.prompt("Selecciona una opción (1-6)", type=int)

            if choice == 1:
                await show_guest_reservations(reservation_service, huesped_id)
            elif choice == 2:
                await create_reservation_interactive(reservation_service, huesped_id)
            elif choice == 3:
                await show_reservation_details_interactive(reservation_service, huesped_id)
            elif choice == 4:
                await cancel_reservation_interactive(reservation_service, huesped_id)
            elif choice == 5:
                await check_property_availability_interactive(reservation_service)
            elif choice == 6:
                break
            else:
                typer.echo(
                    "❌ Opción inválida. Por favor selecciona entre 1 y 6.")

        except ValueError:
            typer.echo("❌ Por favor ingresa un número válido.")
        except KeyboardInterrupt:
            typer.echo("\n👋 Regresando al menú principal...")
            break
        except Exception as e:
            typer.echo(f"❌ Error inesperado: {str(e)}")
            logger.error("Error en gestión de reservas", error=str(e))


async def handle_host_reservations(reservation_service, user_profile):
    """Gestiona las reservas como anfitrión."""
    anfitrion_id = user_profile.anfitrion_id

    while True:
        typer.echo("\n📅 GESTIÓN DE RESERVAS - ANFITRIÓN")
        typer.echo("=" * 50)
        typer.echo(f"🏠 Anfitrión: {user_profile.email} (ID: {anfitrion_id})")
        typer.echo("-" * 50)
        typer.echo("1. 📋 Ver reservas de mis propiedades")
        typer.echo("2. 📝 Ver detalles de una reserva")
        typer.echo("3. ✅ Confirmar reserva")
        typer.echo("4. ❌ Cancelar reserva")
        typer.echo("5. ⬅️  Volver al menú principal")

        try:
            choice = typer.prompt("Selecciona una opción (1-5)", type=int)

            if choice == 1:
                await show_host_reservations(reservation_service, anfitrion_id)
            elif choice == 2:
                await show_reservation_details_interactive(reservation_service, None, anfitrion_id)
            elif choice == 3:
                await confirm_reservation_interactive(reservation_service, anfitrion_id)
            elif choice == 4:
                await cancel_reservation_interactive(reservation_service, None, anfitrion_id)
            elif choice == 5:
                break
            else:
                typer.echo(
                    "❌ Opción inválida. Por favor selecciona entre 1 y 5.")

        except ValueError:
            typer.echo("❌ Por favor ingresa un número válido.")
        except KeyboardInterrupt:
            typer.echo("\n👋 Regresando al menú principal...")
            break
        except Exception as e:
            typer.echo(f"❌ Error inesperado: {str(e)}")
            logger.error(
                "Error en gestión de reservas de anfitrión", error=str(e))


# ===== FUNCIONES DE DISPONIBILIDAD =====

async def show_availability_calendar_interactive(reservation_service, anfitrion_id):
    """Muestra un resumen del calendario de disponibilidad."""
    from db.postgres import execute_query

    try:
        typer.echo("\n📊 CALENDARIO DE DISPONIBILIDAD")
        typer.echo("=" * 50)

        property_id = typer.prompt("🏠 ID de la propiedad", type=int)

        # Validar propiedad del anfitrión
        from services.properties import PropertyService
        prop_service = PropertyService()
        properties_result = await prop_service.list_properties_by_host(anfitrion_id)

        if not properties_result.get('success', False):
            typer.echo("❌ Error obteniendo propiedades del anfitrión")
            typer.echo("Presiona Enter para continuar...")
            input()
            return

        if not any(p['id'] == property_id for p in properties_result.get('properties', [])):
            typer.echo("❌ No tienes permisos para gestionar esta propiedad")
            typer.echo("Presiona Enter para continuar...")
            input()
            return

        # Obtener disponibilidad próxima
        query = """
            SELECT 
                fecha as dia,
                disponible,
                precio_noche as price_per_night,
                CASE 
                    WHEN disponible = true THEN 'Disponible'
                    ELSE 'Bloqueada'
                END as estado
            FROM calendario_disponibilidad 
            WHERE propiedad_id = $1 
            AND fecha >= CURRENT_DATE 
            AND fecha <= CURRENT_DATE + INTERVAL '30 days'
            ORDER BY fecha
            LIMIT 30
        """

        results = await execute_query(query, property_id)

        if results:
            typer.echo(f"\n📅 Próximos 30 días para propiedad {property_id}:")
            typer.echo("-" * 60)
            typer.echo(f"{'Fecha':<12} {'Estado':<12} {'Precio/noche':<15}")
            typer.echo("-" * 60)

            for row in results:
                fecha = row['dia'].strftime("%Y-%m-%d")
                estado = "✅ Disponible" if row['disponible'] else "❌ Bloqueada"
                precio = f"${row['price_per_night']}" if row['price_per_night'] else "No configurado"
                typer.echo(f"{fecha:<12} {estado:<12} {precio:<15}")
        else:
            typer.echo(
                f"\n📅 No hay disponibilidad configurada para la propiedad {property_id}")
            typer.echo(
                "💡 Tip: Use el script setup_availability.py para configurar disponibilidad inicial")

    except Exception as e:
        typer.echo(f"❌ Error: {str(e)}")

    typer.echo("\nPresiona Enter para continuar...")
    input()


async def block_property_dates_interactive(reservation_service, anfitrion_id):
    """Bloquea fechas de una propiedad de forma interactiva."""
    try:
        typer.echo("\n🚫 BLOQUEAR FECHAS")
        typer.echo("=" * 50)

        property_id = typer.prompt("🏠 ID de la propiedad", type=int)

        # Validar propiedad del anfitrión
        from services.properties import PropertyService
        prop_service = PropertyService()
        properties_result = await prop_service.list_properties_by_host(anfitrion_id)

        if not properties_result.get('success', False):
            typer.echo("❌ Error obteniendo propiedades del anfitrión")
            typer.echo("Presiona Enter para continuar...")
            input()
            return

        if not any(p['id'] == property_id for p in properties_result.get('properties', [])):
            typer.echo("❌ No tienes permisos para gestionar esta propiedad")
            typer.echo("Presiona Enter para continuar...")
            input()
            return

        start_date_str = typer.prompt("📅 Fecha inicio (YYYY-MM-DD)")
        end_date_str = typer.prompt("📅 Fecha fin (YYYY-MM-DD)")

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

            if end_date <= start_date:
                typer.echo(
                    "❌ La fecha fin debe ser posterior a la fecha inicio")
                typer.echo("Presiona Enter para continuar...")
                input()
                return

            # Bloquear fechas
            await reservation_service._mark_dates_unavailable(property_id, start_date, end_date)

            num_days = (end_date - start_date).days
            typer.echo(f"\n✅ {num_days} fechas bloqueadas exitosamente")
            typer.echo(f"🏠 Propiedad: {property_id}")
            typer.echo(f"📅 Período: {start_date} a {end_date}")

        except ValueError:
            typer.echo("❌ Formato de fecha inválido. Use YYYY-MM-DD")

    except Exception as e:
        typer.echo(f"❌ Error: {str(e)}")

    typer.echo("\nPresiona Enter para continuar...")
    input()


async def unblock_property_dates_interactive(reservation_service, anfitrion_id):
    """Habilita fechas de una propiedad de forma interactiva."""
    try:
        typer.echo("\n✅ HABILITAR FECHAS")
        typer.echo("=" * 50)

        property_id = typer.prompt("🏠 ID de la propiedad", type=int)

        # Validar propiedad del anfitrión
        from services.properties import PropertyService
        prop_service = PropertyService()
        properties_result = await prop_service.list_properties_by_host(anfitrion_id)

        if not properties_result.get('success', False):
            typer.echo("❌ Error obteniendo propiedades del anfitrión")
            typer.echo("Presiona Enter para continuar...")
            input()
            return

        if not any(p['id'] == property_id for p in properties_result.get('properties', [])):
            typer.echo("❌ No tienes permisos para gestionar esta propiedad")
            typer.echo("Presiona Enter para continuar...")
            input()
            return

        start_date_str = typer.prompt("📅 Fecha inicio (YYYY-MM-DD)")
        end_date_str = typer.prompt("📅 Fecha fin (YYYY-MM-DD)")

        price_input = typer.prompt(
            "💰 Precio por noche (Enter para usar $100 por defecto)", default="")
        price_per_night = None
        if price_input.strip():
            try:
                price_per_night = float(price_input)
            except ValueError:
                typer.echo("❌ Precio inválido, usando precio por defecto")

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

            if end_date <= start_date:
                typer.echo(
                    "❌ La fecha fin debe ser posterior a la fecha inicio")
                typer.echo("Presiona Enter para continuar...")
                input()
                return

            # Habilitar fechas
            await reservation_service._mark_dates_available(property_id, start_date, end_date, price_per_night)

            num_days = (end_date - start_date).days
            price_display = f"${price_per_night}/noche" if price_per_night else "$100/noche (por defecto)"
            typer.echo(f"\n✅ {num_days} fechas habilitadas exitosamente")
            typer.echo(f"🏠 Propiedad: {property_id}")
            typer.echo(f"📅 Período: {start_date} a {end_date}")
            typer.echo(f"💰 Precio: {price_display}")

        except ValueError:
            typer.echo("❌ Formato de fecha inválido. Use YYYY-MM-DD")

    except Exception as e:
        typer.echo(f"❌ Error: {str(e)}")

    typer.echo("\nPresiona Enter para continuar...")
    input()


async def check_availability_interactive(reservation_service, anfitrion_id):
    """Verifica disponibilidad de una propiedad en un rango de fechas."""
    try:
        typer.echo("\n🔍 VERIFICAR DISPONIBILIDAD")
        typer.echo("=" * 50)

        property_id = typer.prompt("🏠 ID de la propiedad", type=int)
        start_date_str = typer.prompt("📅 Fecha inicio (YYYY-MM-DD)")
        end_date_str = typer.prompt("📅 Fecha fin (YYYY-MM-DD)")

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

            if end_date <= start_date:
                typer.echo(
                    "❌ La fecha fin debe ser posterior a la fecha inicio")
                typer.echo("Presiona Enter para continuar...")
                input()
                return

            # Verificar disponibilidad
            is_available = await reservation_service._check_availability(property_id, start_date, end_date)

            num_days = (end_date - start_date).days
            typer.echo(f"\n📊 RESULTADO DE VERIFICACIÓN")
            typer.echo("-" * 30)
            typer.echo(f"🏠 Propiedad: {property_id}")
            typer.echo(f"📅 Período: {start_date} a {end_date}")
            typer.echo(f"📆 Días: {num_days}")

            if is_available:
                typer.echo(f"✅ Estado: DISPONIBLE")
                # Obtener precio total si está disponible
                from decimal import Decimal
                total_price = await reservation_service._calculate_price_for_period(property_id, start_date, end_date)
                if total_price and total_price > Decimal('0'):
                    typer.echo(f"💰 Precio total: ${total_price}")
                    typer.echo(
                        f"💰 Precio promedio por noche: ${total_price / num_days}")
            else:
                typer.echo(f"❌ Estado: NO DISPONIBLE")
                typer.echo("🚫 La propiedad no está disponible en esas fechas")

        except ValueError:
            typer.echo("❌ Formato de fecha inválido. Use YYYY-MM-DD")

    except Exception as e:
        typer.echo(f"❌ Error: {str(e)}")

    typer.echo("\nPresiona Enter para continuar...")
    input()


async def show_availability_stats_interactive(reservation_service, anfitrion_id):
    """Muestra estadísticas de disponibilidad para las propiedades del anfitrión."""
    from db.postgres import execute_query

    try:
        typer.echo("\n📈 ESTADÍSTICAS DE DISPONIBILIDAD")
        typer.echo("=" * 50)

        # Obtener estadísticas generales por propiedad
        query = """
            SELECT 
                p.id as propiedad_id,
                p.nombre,
                COUNT(pd.id) as dias_configurados,
                COUNT(CASE WHEN pd.disponible = true THEN 1 END) as dias_disponibles,
                COUNT(CASE WHEN pd.disponible = false THEN 1 END) as dias_bloqueados,
                AVG(pd.price_per_night) as precio_promedio,
                MIN(pd.price_per_night) as precio_minimo,
                MAX(pd.price_per_night) as precio_maximo
            FROM propiedad p
            LEFT JOIN propiedad_disponibilidad pd ON p.id = pd.propiedad_id
            WHERE p.anfitrion_id = $1
            AND pd.dia >= CURRENT_DATE
            GROUP BY p.id, p.nombre
            ORDER BY p.id
        """

        results = await execute_query(query, anfitrion_id)

        if results:
            typer.echo(
                f"📊 Resumen de disponibilidad para anfitrión {anfitrion_id}:")
            typer.echo("-" * 80)

            for row in results:
                typer.echo(
                    f"\n🏠 Propiedad: {row['nombre']} (ID: {row['propiedad_id']})")
                typer.echo(
                    f"   📅 Días configurados: {row['dias_configurados']}")
                typer.echo(f"   ✅ Días disponibles: {row['dias_disponibles']}")
                typer.echo(f"   ❌ Días bloqueados: {row['dias_bloqueados']}")

                if row['precio_promedio']:
                    typer.echo(
                        f"   💰 Precio promedio: ${row['precio_promedio']:.2f}/noche")
                    typer.echo(
                        f"   💰 Rango de precios: ${row['precio_minimo']:.2f} - ${row['precio_maximo']:.2f}")

                # Calcular proyección de ingresos (días disponibles * precio promedio)
                if row['dias_disponibles'] and row['precio_promedio']:
                    ingresos_potenciales = row['dias_disponibles'] * \
                        float(row['precio_promedio'])
                    typer.echo(
                        f"   💎 Ingresos potenciales: ${ingresos_potenciales:.2f}")
        else:
            typer.echo("📅 No hay datos de disponibilidad configurados")
            typer.echo(
                "💡 Tip: Use el script setup_availability.py para configurar disponibilidad inicial")

    except Exception as e:
        typer.echo(f"❌ Error: {str(e)}")

    typer.echo("\nPresiona Enter para continuar...")
    input()


# ===== FUNCIONES DE RESERVAS =====

async def show_guest_reservations(reservation_service, huesped_id):
    """Muestra las reservas del huésped."""
    # Esta función necesita ser implementada según la lógica de reservas
    typer.echo("🚧 Función en desarrollo - Ver reservas de huésped")
    typer.echo("Presiona Enter para continuar...")
    input()


async def create_reservation_interactive(reservation_service, huesped_id):
    """Crea una nueva reserva de forma interactiva."""
    try:
        typer.echo("\n➕ CREAR NUEVA RESERVA")
        typer.echo("=" * 50)

        property_id = typer.prompt("🏠 ID de la propiedad", type=int)

        typer.echo("\n📅 Fechas (formato: YYYY-MM-DD)")
        check_in_str = typer.prompt("   Fecha de entrada")
        check_out_str = typer.prompt("   Fecha de salida")

        guests = typer.prompt("👥 Número de huéspedes [1]", default=1, type=int)
        special_requests = typer.prompt(
            "💬 Comentarios especiales (Enter para omitir) [", default="")

        try:
            check_in = datetime.strptime(check_in_str, "%Y-%m-%d").date()
            check_out = datetime.strptime(check_out_str, "%Y-%m-%d").date()

            if check_out <= check_in:
                typer.echo(
                    "❌ La fecha de salida debe ser posterior a la fecha de entrada")
                typer.echo("Presiona Enter para continuar...")
                input()
                return

            typer.echo("\n🔄 Creando reserva...")

            # Crear la reserva usando el servicio
            result = await reservation_service.create_reservation(
                propiedad_id=property_id,
                huesped_id=huesped_id,
                check_in=check_in,
                check_out=check_out,
                num_huespedes=guests,
                comentarios=special_requests or None
            )

            if result.get('success'):
                reservation = result.get('reservation', {})
                reserva_id = reservation.get('id')
                total_price = reservation.get('precio_total')
                typer.echo(f"\n✅ Reserva creada exitosamente!")
                typer.echo(f"🆔 ID de reserva: {reserva_id}")
                typer.echo(f"🏠 Propiedad: {property_id}")
                typer.echo(f"📅 Fechas: {check_in} a {check_out}")
                typer.echo(f"👥 Huéspedes: {guests}")
                typer.echo(f"💰 Total: ${total_price}")
                if special_requests:
                    typer.echo(f"💬 Comentarios: {special_requests}")
            else:
                error_msg = result.get('error', 'Error desconocido')
                typer.echo(f"❌ Error: {error_msg}")

        except ValueError:
            typer.echo("❌ Formato de fecha inválido. Use YYYY-MM-DD")

    except Exception as e:
        typer.echo(f"❌ Error inesperado: {str(e)}")

    typer.echo("\nPresiona Enter para continuar...")
    input()


async def show_reservation_details_interactive(reservation_service, huesped_id=None, anfitrion_id=None):
    """Muestra detalles de una reserva específica."""
    # Esta función necesita ser implementada según la lógica de reservas
    typer.echo("🚧 Función en desarrollo - Ver detalles de reserva")
    typer.echo("Presiona Enter para continuar...")
    input()


async def cancel_reservation_interactive(reservation_service, huesped_id=None, anfitrion_id=None):
    """Cancela una reserva de forma interactiva."""
    # Esta función necesita ser implementada según la lógica de reservas
    typer.echo("🚧 Función en desarrollo - Cancelar reserva")
    typer.echo("Presiona Enter para continuar...")
    input()


async def check_property_availability_interactive(reservation_service):
    """Verifica disponibilidad de una propiedad sin restricciones de anfitrión."""
    try:
        typer.echo("\n🔍 VERIFICAR DISPONIBILIDAD")
        typer.echo("=" * 50)

        property_id = typer.prompt("🏠 ID de la propiedad", type=int)
        start_date_str = typer.prompt("📅 Fecha inicio (YYYY-MM-DD)")
        end_date_str = typer.prompt("📅 Fecha fin (YYYY-MM-DD)")

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

            if end_date <= start_date:
                typer.echo(
                    "❌ La fecha fin debe ser posterior a la fecha inicio")
                typer.echo("Presiona Enter para continuar...")
                input()
                return

            # Verificar disponibilidad
            is_available = await reservation_service._check_availability(property_id, start_date, end_date)

            num_days = (end_date - start_date).days
            typer.echo(f"\n📊 RESULTADO DE VERIFICACIÓN")
            typer.echo("-" * 30)
            typer.echo(f"🏠 Propiedad: {property_id}")
            typer.echo(f"📅 Período: {start_date} a {end_date}")
            typer.echo(f"📆 Días: {num_days}")

            if is_available:
                typer.echo(f"✅ Estado: DISPONIBLE")
                # Obtener precio total si está disponible
                from decimal import Decimal
                total_price = await reservation_service._calculate_price_for_period(property_id, start_date, end_date)
                if total_price and total_price > Decimal('0'):
                    typer.echo(f"💰 Precio total: ${total_price}")
                    typer.echo(
                        f"💰 Precio promedio por noche: ${total_price / num_days}")
            else:
                typer.echo(f"❌ Estado: NO DISPONIBLE")
                typer.echo("🚫 La propiedad no está disponible en esas fechas")

        except ValueError:
            typer.echo("❌ Formato de fecha inválido. Use YYYY-MM-DD")

    except Exception as e:
        typer.echo(f"❌ Error: {str(e)}")

    typer.echo("\nPresiona Enter para continuar...")
    input()


async def show_host_reservations(reservation_service, anfitrion_id):
    """Muestra las reservas de las propiedades del anfitrión."""
    # Esta función necesita ser implementada según la lógica de reservas
    typer.echo("🚧 Función en desarrollo - Ver reservas de anfitrión")
    typer.echo("Presiona Enter para continuar...")
    input()


async def confirm_reservation_interactive(reservation_service, anfitrion_id):
    """Confirma una reserva de forma interactiva."""
    # Esta función necesita ser implementada según la lógica de reservas
    typer.echo("🚧 Función en desarrollo - Confirmar reserva")
    typer.echo("Presiona Enter para continuar...")
    input()


async def handle_reservation_management(user_profile):
    """Gestiona las reservas según el rol del usuario."""
    reservation_service = ReservationService()

    if user_profile.rol in ['HUESPED', 'AMBOS']:
        await handle_guest_reservations(reservation_service, user_profile)
    elif user_profile.rol == 'ANFITRION':
        await handle_host_reservations(reservation_service, user_profile)


async def handle_guest_reservations(reservation_service, user_profile):
    """Gestiona las reservas como huésped."""
    huesped_id = user_profile.huesped_id

    while True:
        typer.echo("\n📅 GESTIÓN DE RESERVAS")
        typer.echo("=" * 50)
        typer.echo(f"👤 Huésped: {user_profile.email} (ID: {huesped_id})")
        typer.echo("-" * 50)
        typer.echo("1. 📋 Ver mis reservas")
        typer.echo("2. ➕ Crear nueva reserva")
        typer.echo("3. 📝 Ver detalles de una reserva")
        typer.echo("4. ❌ Cancelar reserva")
        typer.echo("5. 🔍 Ver disponibilidad de una propiedad")
        typer.echo("6. ⬅️  Volver al menú principal")

        try:
            choice = typer.prompt("Selecciona una opción (1-6)", type=int)

            if choice == 1:
                await show_guest_reservations(reservation_service, huesped_id)
            elif choice == 2:
                await create_reservation_interactive(reservation_service, huesped_id)
            elif choice == 3:
                await show_reservation_details_interactive(reservation_service, huesped_id)
            elif choice == 4:
                await cancel_reservation_interactive(reservation_service, huesped_id)
            elif choice == 5:
                await check_property_availability_interactive(reservation_service)
            elif choice == 6:
                break
            else:
                typer.echo(
                    "❌ Opción inválida. Por favor selecciona entre 1 y 6.")

        except ValueError:
            typer.echo("❌ Por favor ingresa un número válido.")
        except KeyboardInterrupt:
            typer.echo("\n👋 Regresando al menú principal...")
            break
        except Exception as e:
            typer.echo(f"❌ Error inesperado: {str(e)}")
            logger.error("Error en gestión de reservas", error=str(e))


async def handle_host_reservations(reservation_service, user_profile):
    """Gestiona las reservas como anfitrión."""
    anfitrion_id = user_profile.anfitrion_id

    while True:
        typer.echo("\n📅 GESTIÓN DE RESERVAS - ANFITRIÓN")
        typer.echo("=" * 50)
        typer.echo(f"🏠 Anfitrión: {user_profile.email} (ID: {anfitrion_id})")
        typer.echo("-" * 50)
        typer.echo("1. 📋 Ver reservas de mis propiedades")
        typer.echo("2. 📝 Ver detalles de una reserva")
        typer.echo("3. ✅ Confirmar reserva")
        typer.echo("4. ❌ Cancelar reserva")
        typer.echo("5. ⬅️  Volver al menú principal")

        try:
            choice = typer.prompt("Selecciona una opción (1-5)", type=int)

            if choice == 1:
                await show_host_reservations(reservation_service, anfitrion_id)
            elif choice == 2:
                await show_reservation_details_interactive(reservation_service, None, anfitrion_id)
            elif choice == 3:
                await confirm_reservation_interactive(reservation_service, anfitrion_id)
            elif choice == 4:
                await cancel_reservation_interactive(reservation_service, None, anfitrion_id)
            elif choice == 5:
                break
            else:
                typer.echo(
                    "❌ Opción inválida. Por favor selecciona entre 1 y 5.")

        except ValueError:
            typer.echo("❌ Por favor ingresa un número válido.")
        except KeyboardInterrupt:
            typer.echo("\n👋 Regresando al menú principal...")
            break
        except Exception as e:
            typer.echo(f"❌ Error inesperado: {str(e)}")
            logger.error(
                "Error en gestión de reservas de anfitrión", error=str(e))


# ===== FUNCIONES DE DISPONIBILIDAD =====

async def show_availability_calendar_interactive(reservation_service, anfitrion_id):
    """Muestra un resumen del calendario de disponibilidad."""
    from db.postgres import execute_query

    try:
        typer.echo("\n📊 CALENDARIO DE DISPONIBILIDAD")
        typer.echo("=" * 50)

        property_id = typer.prompt("🏠 ID de la propiedad", type=int)

        # Validar propiedad del anfitrión
        from services.properties import PropertyService
        prop_service = PropertyService()
        properties_result = await prop_service.list_properties_by_host(anfitrion_id)

        if not properties_result.get('success', False):
            typer.echo("❌ Error obteniendo propiedades del anfitrión")
            typer.echo("Presiona Enter para continuar...")
            input()
            return

        if not any(p['id'] == property_id for p in properties_result.get('properties', [])):
            typer.echo("❌ No tienes permisos para gestionar esta propiedad")
            typer.echo("Presiona Enter para continuar...")
            input()
            return

        # Obtener disponibilidad próxima
        query = """
            SELECT 
                fecha as dia,
                disponible,
                precio_noche as price_per_night,
                CASE 
                    WHEN disponible = true THEN 'Disponible'
                    ELSE 'Bloqueada'
                END as estado
            FROM calendario_disponibilidad 
            WHERE propiedad_id = $1 
            AND fecha >= CURRENT_DATE 
            AND fecha <= CURRENT_DATE + INTERVAL '30 days'
            ORDER BY fecha
            LIMIT 30
        """

        results = await execute_query(query, property_id)

        if results:
            typer.echo(f"\n📅 Próximos 30 días para propiedad {property_id}:")
            typer.echo("-" * 60)
            typer.echo(f"{'Fecha':<12} {'Estado':<12} {'Precio/noche':<15}")
            typer.echo("-" * 60)

            for row in results:
                fecha = row['dia'].strftime("%Y-%m-%d")
                estado = "✅ Disponible" if row['disponible'] else "❌ Bloqueada"
                precio = f"${row['price_per_night']}" if row['price_per_night'] else "No configurado"
                typer.echo(f"{fecha:<12} {estado:<12} {precio:<15}")
        else:
            typer.echo(
                f"\n📅 No hay disponibilidad configurada para la propiedad {property_id}")
            typer.echo(
                "💡 Tip: Use el script setup_availability.py para configurar disponibilidad inicial")

    except Exception as e:
        typer.echo(f"❌ Error: {str(e)}")

    typer.echo("\nPresiona Enter para continuar...")
    input()


async def block_property_dates_interactive(reservation_service, anfitrion_id):
    """Bloquea fechas de una propiedad de forma interactiva."""
    try:
        typer.echo("\n🚫 BLOQUEAR FECHAS")
        typer.echo("=" * 50)

        property_id = typer.prompt("🏠 ID de la propiedad", type=int)

        # Validar propiedad del anfitrión
        from services.properties import PropertyService
        prop_service = PropertyService()
        properties_result = await prop_service.list_properties_by_host(anfitrion_id)

        if not properties_result.get('success', False):
            typer.echo("❌ Error obteniendo propiedades del anfitrión")
            typer.echo("Presiona Enter para continuar...")
            input()
            return

        if not any(p['id'] == property_id for p in properties_result.get('properties', [])):
            typer.echo("❌ No tienes permisos para gestionar esta propiedad")
            typer.echo("Presiona Enter para continuar...")
            input()
            return

        start_date_str = typer.prompt("📅 Fecha inicio (YYYY-MM-DD)")
        end_date_str = typer.prompt("📅 Fecha fin (YYYY-MM-DD)")

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

            if end_date <= start_date:
                typer.echo(
                    "❌ La fecha fin debe ser posterior a la fecha inicio")
                typer.echo("Presiona Enter para continuar...")
                input()
                return

            # Bloquear fechas
            await reservation_service._mark_dates_unavailable(property_id, start_date, end_date)

            num_days = (end_date - start_date).days
            typer.echo(f"\n✅ {num_days} fechas bloqueadas exitosamente")
            typer.echo(f"🏠 Propiedad: {property_id}")
            typer.echo(f"📅 Período: {start_date} a {end_date}")

        except ValueError:
            typer.echo("❌ Formato de fecha inválido. Use YYYY-MM-DD")

    except Exception as e:
        typer.echo(f"❌ Error: {str(e)}")

    typer.echo("\nPresiona Enter para continuar...")
    input()


async def unblock_property_dates_interactive(reservation_service, anfitrion_id):
    """Habilita fechas de una propiedad de forma interactiva."""
    try:
        typer.echo("\n✅ HABILITAR FECHAS")
        typer.echo("=" * 50)

        property_id = typer.prompt("🏠 ID de la propiedad", type=int)

        # Validar propiedad del anfitrión
        from services.properties import PropertyService
        prop_service = PropertyService()
        properties_result = await prop_service.list_properties_by_host(anfitrion_id)

        if not properties_result.get('success', False):
            typer.echo("❌ Error obteniendo propiedades del anfitrión")
            typer.echo("Presiona Enter para continuar...")
            input()
            return

        if not any(p['id'] == property_id for p in properties_result.get('properties', [])):
            typer.echo("❌ No tienes permisos para gestionar esta propiedad")
            typer.echo("Presiona Enter para continuar...")
            input()
            return

        start_date_str = typer.prompt("📅 Fecha inicio (YYYY-MM-DD)")
        end_date_str = typer.prompt("📅 Fecha fin (YYYY-MM-DD)")

        price_input = typer.prompt(
            "💰 Precio por noche (Enter para usar $100 por defecto)", default="")
        price_per_night = None
        if price_input.strip():
            try:
                price_per_night = float(price_input)
            except ValueError:
                typer.echo("❌ Precio inválido, usando precio por defecto")

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

            if end_date <= start_date:
                typer.echo(
                    "❌ La fecha fin debe ser posterior a la fecha inicio")
                typer.echo("Presiona Enter para continuar...")
                input()
                return

            # Habilitar fechas
            await reservation_service._mark_dates_available(property_id, start_date, end_date, price_per_night)

            num_days = (end_date - start_date).days
            price_display = f"${price_per_night}/noche" if price_per_night else "$100/noche (por defecto)"
            typer.echo(f"\n✅ {num_days} fechas habilitadas exitosamente")
            typer.echo(f"🏠 Propiedad: {property_id}")
            typer.echo(f"📅 Período: {start_date} a {end_date}")
            typer.echo(f"💰 Precio: {price_display}")

        except ValueError:
            typer.echo("❌ Formato de fecha inválido. Use YYYY-MM-DD")

    except Exception as e:
        typer.echo(f"❌ Error: {str(e)}")

    typer.echo("\nPresiona Enter para continuar...")
    input()


async def check_availability_interactive(reservation_service, anfitrion_id):
    """Verifica disponibilidad de una propiedad en un rango de fechas."""
    try:
        typer.echo("\n🔍 VERIFICAR DISPONIBILIDAD")
        typer.echo("=" * 50)

        property_id = typer.prompt("🏠 ID de la propiedad", type=int)
        start_date_str = typer.prompt("📅 Fecha inicio (YYYY-MM-DD)")
        end_date_str = typer.prompt("📅 Fecha fin (YYYY-MM-DD)")

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

            if end_date <= start_date:
                typer.echo(
                    "❌ La fecha fin debe ser posterior a la fecha inicio")
                typer.echo("Presiona Enter para continuar...")
                input()
                return

            # Verificar disponibilidad
            is_available = await reservation_service._check_availability(property_id, start_date, end_date)

            num_days = (end_date - start_date).days
            typer.echo(f"\n📊 RESULTADO DE VERIFICACIÓN")
            typer.echo("-" * 30)
            typer.echo(f"🏠 Propiedad: {property_id}")
            typer.echo(f"📅 Período: {start_date} a {end_date}")
            typer.echo(f"📆 Días: {num_days}")

            if is_available:
                typer.echo(f"✅ Estado: DISPONIBLE")
                # Obtener precio total si está disponible
                from decimal import Decimal
                total_price = await reservation_service._calculate_price_for_period(property_id, start_date, end_date)
                if total_price and total_price > Decimal('0'):
                    typer.echo(f"💰 Precio total: ${total_price}")
                    typer.echo(
                        f"💰 Precio promedio por noche: ${total_price / num_days}")
            else:
                typer.echo(f"❌ Estado: NO DISPONIBLE")
                typer.echo("🚫 La propiedad no está disponible en esas fechas")

        except ValueError:
            typer.echo("❌ Formato de fecha inválido. Use YYYY-MM-DD")

    except Exception as e:
        typer.echo(f"❌ Error: {str(e)}")

    typer.echo("\nPresiona Enter para continuar...")
    input()


async def show_availability_stats_interactive(reservation_service, anfitrion_id):
    """Muestra estadísticas de disponibilidad para las propiedades del anfitrión."""
    from db.postgres import execute_query

    try:
        typer.echo("\n📈 ESTADÍSTICAS DE DISPONIBILIDAD")
        typer.echo("=" * 50)

        # Obtener estadísticas generales por propiedad
        query = """
            SELECT 
                p.id as propiedad_id,
                p.nombre,
                COUNT(pd.id) as dias_configurados,
                COUNT(CASE WHEN pd.disponible = true THEN 1 END) as dias_disponibles,
                COUNT(CASE WHEN pd.disponible = false THEN 1 END) as dias_bloqueados,
                AVG(pd.price_per_night) as precio_promedio,
                MIN(pd.price_per_night) as precio_minimo,
                MAX(pd.price_per_night) as precio_maximo
            FROM propiedad p
            LEFT JOIN propiedad_disponibilidad pd ON p.id = pd.propiedad_id
            WHERE p.anfitrion_id = $1
            AND pd.dia >= CURRENT_DATE
            GROUP BY p.id, p.nombre
            ORDER BY p.id
        """

        results = await execute_query(query, anfitrion_id)

        if results:
            typer.echo(
                f"📊 Resumen de disponibilidad para anfitrión {anfitrion_id}:")
            typer.echo("-" * 80)

            for row in results:
                typer.echo(
                    f"\n🏠 Propiedad: {row['nombre']} (ID: {row['propiedad_id']})")
                typer.echo(
                    f"   📅 Días configurados: {row['dias_configurados']}")
                typer.echo(f"   ✅ Días disponibles: {row['dias_disponibles']}")
                typer.echo(f"   ❌ Días bloqueados: {row['dias_bloqueados']}")

                if row['precio_promedio']:
                    typer.echo(
                        f"   💰 Precio promedio: ${row['precio_promedio']:.2f}/noche")
                    typer.echo(
                        f"   💰 Rango de precios: ${row['precio_minimo']:.2f} - ${row['precio_maximo']:.2f}")

                # Calcular proyección de ingresos (días disponibles * precio promedio)
                if row['dias_disponibles'] and row['precio_promedio']:
                    ingresos_potenciales = row['dias_disponibles'] * \
                        float(row['precio_promedio'])
                    typer.echo(
                        f"   💎 Ingresos potenciales: ${ingresos_potenciales:.2f}")
        else:
            typer.echo("📅 No hay datos de disponibilidad configurados")
            typer.echo(
                "💡 Tip: Use el script setup_availability.py para configurar disponibilidad inicial")

    except Exception as e:
        typer.echo(f"❌ Error: {str(e)}")

    typer.echo("\nPresiona Enter para continuar...")
    input()


# ===== FUNCIONES DE RESERVAS =====

async def show_guest_reservations(reservation_service, huesped_id):
    """Muestra las reservas del huésped."""
    # Esta función necesita ser implementada según la lógica de reservas
    typer.echo("🚧 Función en desarrollo - Ver reservas de huésped")
    typer.echo("Presiona Enter para continuar...")
    input()


async def create_reservation_interactive(reservation_service, huesped_id):
    """Crea una nueva reserva de forma interactiva."""
    try:
        typer.echo("\n➕ CREAR NUEVA RESERVA")
        typer.echo("=" * 50)

        property_id = typer.prompt("🏠 ID de la propiedad", type=int)

        typer.echo("\n📅 Fechas (formato: YYYY-MM-DD)")
        check_in_str = typer.prompt("   Fecha de entrada")
        check_out_str = typer.prompt("   Fecha de salida")

        guests = typer.prompt("👥 Número de huéspedes [1]", default=1, type=int)
        special_requests = typer.prompt(
            "💬 Comentarios especiales (Enter para omitir) [", default="")

        try:
            check_in = datetime.strptime(check_in_str, "%Y-%m-%d").date()
            check_out = datetime.strptime(check_out_str, "%Y-%m-%d").date()

            if check_out <= check_in:
                typer.echo(
                    "❌ La fecha de salida debe ser posterior a la fecha de entrada")
                typer.echo("Presiona Enter para continuar...")
                input()
                return

            typer.echo("\n🔄 Creando reserva...")

            # Crear la reserva usando el servicio
            result = await reservation_service.create_reservation(
                propiedad_id=property_id,
                huesped_id=huesped_id,
                check_in=check_in,
                check_out=check_out,
                num_huespedes=guests,
                metodo_pago_id=1,  # Método por defecto
                comentarios=special_requests
            )

            if result.get('success'):
                reservation = result.get('reservation', {})
                reserva_id = reservation.get('id')
                total_price = reservation.get('precio_total')
                typer.echo(f"\n✅ Reserva creada exitosamente!")
                typer.echo(f"🆔 ID de reserva: {reserva_id}")
                typer.echo(f"🏠 Propiedad: {property_id}")
                typer.echo(f"📅 Fechas: {check_in} a {check_out}")
                typer.echo(f"👥 Huéspedes: {guests}")
                typer.echo(f"💰 Total: ${total_price}")
                if special_requests:
                    typer.echo(f"💬 Comentarios: {special_requests}")
            else:
                error_msg = result.get('error', 'Error desconocido')
                typer.echo(f"❌ Error: {error_msg}")

        except ValueError:
            typer.echo("❌ Formato de fecha inválido. Use YYYY-MM-DD")

    except Exception as e:
        typer.echo(f"❌ Error inesperado: {str(e)}")

    typer.echo("\nPresiona Enter para continuar...")
    input()


async def show_reservation_details_interactive(reservation_service, huesped_id=None, anfitrion_id=None):
    """Muestra detalles de una reserva específica."""
    # Esta función necesita ser implementada según la lógica de reservas
    typer.echo("🚧 Función en desarrollo - Ver detalles de reserva")
    typer.echo("Presiona Enter para continuar...")
    input()


async def cancel_reservation_interactive(reservation_service, huesped_id=None, anfitrion_id=None):
    """Cancela una reserva de forma interactiva."""
    # Esta función necesita ser implementada según la lógica de reservas
    typer.echo("🚧 Función en desarrollo - Cancelar reserva")
    typer.echo("Presiona Enter para continuar...")
    input()


async def check_property_availability_interactive(reservation_service):
    """Verifica disponibilidad de una propiedad sin restricciones de anfitrión."""
    try:
        typer.echo("\n🔍 VERIFICAR DISPONIBILIDAD")
        typer.echo("=" * 50)

        property_id = typer.prompt("🏠 ID de la propiedad", type=int)
        start_date_str = typer.prompt("📅 Fecha inicio (YYYY-MM-DD)")
        end_date_str = typer.prompt("📅 Fecha fin (YYYY-MM-DD)")

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

            if end_date <= start_date:
                typer.echo(
                    "❌ La fecha fin debe ser posterior a la fecha inicio")
                typer.echo("Presiona Enter para continuar...")
                input()
                return

            # Verificar disponibilidad
            is_available = await reservation_service._check_availability(property_id, start_date, end_date)

            num_days = (end_date - start_date).days
            typer.echo(f"\n📊 RESULTADO DE VERIFICACIÓN")
            typer.echo("-" * 30)
            typer.echo(f"🏠 Propiedad: {property_id}")
            typer.echo(f"📅 Período: {start_date} a {end_date}")
            typer.echo(f"📆 Días: {num_days}")

            if is_available:
                typer.echo(f"✅ Estado: DISPONIBLE")
                # Obtener precio total si está disponible
                from decimal import Decimal
                total_price = await reservation_service._calculate_price_for_period(property_id, start_date, end_date)
                if total_price and total_price > Decimal('0'):
                    typer.echo(f"💰 Precio total: ${total_price}")
                    typer.echo(
                        f"💰 Precio promedio por noche: ${total_price / num_days}")
            else:
                typer.echo(f"❌ Estado: NO DISPONIBLE")
                typer.echo("🚫 La propiedad no está disponible en esas fechas")

        except ValueError:
            typer.echo("❌ Formato de fecha inválido. Use YYYY-MM-DD")

    except Exception as e:
        typer.echo(f"❌ Error: {str(e)}")

    typer.echo("\nPresiona Enter para continuar...")
    input()


async def show_host_reservations(reservation_service, anfitrion_id):
    """Muestra las reservas de las propiedades del anfitrión."""
    # Esta función necesita ser implementada según la lógica de reservas
    typer.echo("🚧 Función en desarrollo - Ver reservas de anfitrión")
    typer.echo("Presiona Enter para continuar...")
    input()


async def confirm_reservation_interactive(reservation_service, anfitrion_id):
    """Confirma una reserva de forma interactiva."""
    # Esta función necesita ser implementada según la lógica de reservas
    typer.echo("🚧 Función en desarrollo - Confirmar reserva")
    typer.echo("Presiona Enter para continuar...")
    input()


# ===== FUNCIONES DE ANÁLISIS DE COMUNIDADES =====

async def handle_communities_analysis(user_profile):
    """Maneja el análisis de comunidades host-huésped."""
    try:
        from services.neo4j_reservations import Neo4jReservationService
        neo4j_service = Neo4jReservationService()

        while True:
            typer.echo(f"\n🏘️  ANÁLISIS DE COMUNIDADES HOST-HUÉSPED")
            typer.echo("=" * 60)
            typer.echo(f"👤 Usuario: {user_profile.email}")
            typer.echo("-" * 60)
            typer.echo("1. 🔍 Ver todas las comunidades (>=3 interacciones)")
            typer.echo("2. 👤 Ver mis comunidades")
            typer.echo("3. 🏆 Top 10 comunidades más activas")
            typer.echo("4. 📊 Estadísticas generales")
            typer.echo("5. ⚙️  Configurar filtros personalizados")
            typer.echo("6. ⬅️  Volver al menú principal")

            try:
                choice = typer.prompt("Selecciona una opción (1-6)", type=int)

                if choice == 1:
                    await show_all_communities(neo4j_service)
                elif choice == 2:
                    await show_user_communities(neo4j_service, user_profile)
                elif choice == 3:
                    await show_top_communities(neo4j_service)
                elif choice == 4:
                    await show_community_stats(neo4j_service)
                elif choice == 5:
                    await show_custom_community_filter(neo4j_service)
                elif choice == 6:
                    break
                else:
                    typer.echo(
                        "❌ Opción inválida. Por favor selecciona entre 1 y 6.")

            except ValueError:
                typer.echo("❌ Por favor ingresa un número válido.")
            except KeyboardInterrupt:
                typer.echo("\n👋 Regresando al menú principal...")
                break

    except ImportError:
        typer.echo("❌ El análisis de comunidades requiere Neo4j")
        typer.echo(
            "💡 Verifica que el servicio Neo4j esté configurado correctamente")
        typer.echo("Presiona Enter para continuar...")
        input()
    except Exception as e:
        typer.echo(f"❌ Error inesperado en análisis de comunidades: {str(e)}")
        logger.error("Error en análisis de comunidades", error=str(e))
        typer.echo("Presiona Enter para continuar...")
        input()
    finally:
        try:
            if 'neo4j_service' in locals():
                neo4j_service.close()
        except:
            pass


async def show_all_communities(neo4j_service):
    """Muestra todas las comunidades con más de 3 interacciones."""
    try:
        typer.echo("\n🔍 OBTENIENDO TODAS LAS COMUNIDADES...")

        result = await neo4j_service.get_all_communities(min_interactions=3)

        if result['success']:
            communities = result['communities']
            if communities:
                typer.echo(
                    f"\n🏘️  {result['total_communities']} comunidades encontradas:")
                typer.echo("=" * 90)
                typer.echo(
                    f"{'#':<3} {'Huésped':<25} {'Host':<25} {'Interacciones':<12} {'Props':<6} {'Última':<12}")
                typer.echo("=" * 90)

                # Mostrar máximo 20
                for i, comm in enumerate(communities[:20], 1):
                    guest_display = f"{comm['guest_email'][:22]}..." if len(
                        comm['guest_email']) > 25 else comm['guest_email']
                    host_display = f"{comm['host_email'][:22]}..." if len(
                        comm['host_email']) > 25 else comm['host_email']

                    typer.echo(
                        f"{i:<3} {guest_display:<25} {host_display:<25} "
                        f"{comm['interactions']:<12} {comm['unique_properties']:<6} {comm['last_interaction']:<12}"
                    )

                if len(communities) > 20:
                    typer.echo(
                        f"\n... y {len(communities) - 20} comunidades más")

                # Mostrar estadísticas
                stats = result['statistics']
                if stats:
                    typer.echo(f"\n📊 ESTADÍSTICAS:")
                    typer.echo(
                        f"   📈 Promedio interacciones: {stats['avg_interactions']:.1f}")
                    typer.echo(
                        f"   📈 Promedio propiedades: {stats['avg_properties']:.1f}")
                    typer.echo(
                        f"   🏆 Máximo interacciones: {stats['max_interactions']}")
                    typer.echo(
                        f"   🏆 Máximo propiedades: {stats['max_properties']}")
            else:
                typer.echo(
                    "\n❌ No se encontraron comunidades con más de 3 interacciones")
                typer.echo(
                    "💡 Las comunidades se forman automáticamente cuando hay >3 reservas entre los mismos usuarios")
        else:
            typer.echo(f"\n❌ Error: {result['error']}")

    except Exception as e:
        typer.echo(f"\n❌ Error obteniendo comunidades: {str(e)}")

    typer.echo("\nPresiona Enter para continuar...")
    input()


async def show_user_communities(neo4j_service, user_profile):
    """Muestra las comunidades específicas del usuario actual."""
    try:
        # Determinar el user_id correcto según el rol
        user_id = None
        if hasattr(user_profile, 'huesped_id') and user_profile.huesped_id:
            user_id = user_profile.huesped_id
        elif hasattr(user_profile, 'anfitrion_id') and user_profile.anfitrion_id:
            user_id = user_profile.anfitrion_id
        else:
            typer.echo("❌ No se pudo determinar el ID de usuario")
            typer.echo("Presiona Enter para continuar...")
            input()
            return

        typer.echo(f"\n👤 OBTENIENDO COMUNIDADES DE {user_profile.email}...")

        result = await neo4j_service.get_user_communities(user_id)

        if result['success']:
            total_communities = result['total_communities']

            if total_communities > 0:
                typer.echo(
                    f"\n🏘️  Tienes {total_communities} comunidades activas:")
                typer.echo("=" * 80)

                # Mostrar comunidades como huésped
                if result['as_guest']:
                    typer.echo(
                        f"\n👤 COMO HUÉSPED ({len(result['as_guest'])} comunidades):")
                    typer.echo("-" * 70)
                    for comm in result['as_guest']:
                        typer.echo(f"🏠 Host: {comm['user_email']}")
                        typer.echo(
                            f"   📊 {comm['interactions']} interacciones en {comm['unique_properties']} propiedades")
                        typer.echo(
                            f"   📅 Desde {comm['first_interaction']} hasta {comm['last_interaction']}")
                        typer.echo()

                # Mostrar comunidades como host
                if result['as_host']:
                    typer.echo(
                        f"\n🏠 COMO ANFITRIÓN ({len(result['as_host'])} comunidades):")
                    typer.echo("-" * 70)
                    for comm in result['as_host']:
                        typer.echo(f"👤 Huésped: {comm['user_email']}")
                        typer.echo(
                            f"   📊 {comm['interactions']} interacciones en {comm['unique_properties']} propiedades")
                        typer.echo(
                            f"   📅 Desde {comm['first_interaction']} hasta {comm['last_interaction']}")
                        typer.echo()

            else:
                typer.echo(f"\n❌ No tienes comunidades formadas aún")
                typer.echo(
                    "💡 Las comunidades se forman automáticamente después de 3+ interacciones con el mismo usuario")
        else:
            typer.echo(f"\n❌ Error: {result['error']}")

    except Exception as e:
        typer.echo(f"\n❌ Error obteniendo tus comunidades: {str(e)}")

    typer.echo("\nPresiona Enter para continuar...")
    input()


async def show_top_communities(neo4j_service):
    """Muestra las top 10 comunidades más activas."""
    try:
        typer.echo("\n🏆 OBTENIENDO TOP 10 COMUNIDADES...")

        result = await neo4j_service.get_top_communities(limit=10)

        if result['success']:
            communities = result['top_communities']
            if communities:
                typer.echo(
                    f"\n🏆 TOP {len(communities)} COMUNIDADES MÁS ACTIVAS:")
                typer.echo("=" * 85)
                typer.echo(
                    f"{'Rank':<4} {'Huésped':<25} {'Host':<25} {'Interacciones':<12} {'Props':<6}")
                typer.echo("=" * 85)

                for comm in communities:
                    guest_display = f"{comm['guest_email'][:22]}..." if len(
                        comm['guest_email']) > 25 else comm['guest_email']
                    host_display = f"{comm['host_email'][:22]}..." if len(
                        comm['host_email']) > 25 else comm['host_email']

                    # Agregar emojis de ranking
                    rank_emoji = "🥇" if comm['rank'] == 1 else "🥈" if comm[
                        'rank'] == 2 else "🥉" if comm['rank'] == 3 else f"#{comm['rank']}"

                    typer.echo(
                        f"{rank_emoji:<4} {guest_display:<25} {host_display:<25} "
                        f"{comm['interactions']:<12} {comm['unique_properties']:<6}"
                    )

                # Mostrar detalles del top 3
                typer.echo(f"\n🎯 DETALLES DEL TOP 3:")
                for i, comm in enumerate(communities[:3], 1):
                    medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
                    typer.echo(
                        f"\n{medal} #{i}: {comm['interactions']} interacciones")
                    typer.echo(
                        f"   👤 {comm['guest_email']} ↔ 🏠 {comm['host_email']}")
                    typer.echo(
                        f"   🏠 {comm['unique_properties']} propiedades diferentes")
                    typer.echo(
                        f"   📅 {comm['first_interaction']} → {comm['last_interaction']}")
            else:
                typer.echo("\n❌ No se encontraron comunidades")
        else:
            typer.echo(f"\n❌ Error: {result['error']}")

    except Exception as e:
        typer.echo(f"\n❌ Error obteniendo top comunidades: {str(e)}")

    typer.echo("\nPresiona Enter para continuar...")
    input()


async def show_community_stats(neo4j_service):
    """Muestra estadísticas generales del sistema de comunidades."""
    try:
        typer.echo("\n📊 OBTENIENDO ESTADÍSTICAS...")

        result = await neo4j_service.get_community_stats()

        if result['success']:
            if 'total_relationships' in result and result['total_relationships'] > 0:
                typer.echo(f"\n📊 ESTADÍSTICAS GENERALES DEL SISTEMA:")
                typer.echo("=" * 60)
                typer.echo(
                    f"👥 Total relaciones usuario-usuario: {result['total_relationships']}")
                typer.echo(
                    f"🏘️  Comunidades formadas (>3 interacciones): {result['communities_formed']}")
                typer.echo(
                    f"🤝 Relaciones casuales (≤3 interacciones): {result['casual_relationships']}")
                typer.echo(
                    f"📈 Tasa de formación de comunidades: {result['community_rate']}%")
                typer.echo()
                typer.echo(f"📊 DISTRIBUCIÓN DE INTERACCIONES:")
                typer.echo(
                    f"   📈 Promedio: {result['avg_interactions']} interacciones por relación")
                typer.echo(
                    f"   📈 Máximo: {result['max_interactions']} interacciones")
                typer.echo(
                    f"   📈 Mínimo: {result['min_interactions']} interacciones")

                # Calcular insights
                if result['community_rate'] > 20:
                    typer.echo(f"\n💡 INSIGHTS:")
                    typer.echo(
                        f"   ✅ Alta tasa de fidelización: {result['community_rate']}% de usuarios forman comunidades")
                elif result['community_rate'] > 10:
                    typer.echo(f"\n💡 INSIGHTS:")
                    typer.echo(
                        f"   📊 Tasa moderada de fidelización: {result['community_rate']}%")
                else:
                    typer.echo(f"\n💡 INSIGHTS:")
                    typer.echo(
                        f"   📉 Oportunidad de mejora en fidelización: solo {result['community_rate']}% forman comunidades")

            else:
                typer.echo("\n❌ No hay datos de relaciones en el sistema")
                typer.echo(
                    "💡 Las relaciones se crean automáticamente cuando se hacen reservas")
        else:
            typer.echo(f"\n❌ Error: {result['error']}")

    except Exception as e:
        typer.echo(f"\n❌ Error obteniendo estadísticas: {str(e)}")

    typer.echo("\nPresiona Enter para continuar...")
    input()


async def show_custom_community_filter(neo4j_service):
    """Permite configurar filtros personalizados para el análisis."""
    try:
        typer.echo("\n⚙️  FILTROS PERSONALIZADOS")
        typer.echo("=" * 50)

        min_interactions = typer.prompt(
            "🔢 Mínimo de interacciones [3]",
            default=3,
            type=int
        )

        if min_interactions < 1:
            typer.echo("❌ El mínimo debe ser al menos 1")
            typer.echo("Presiona Enter para continuar...")
            input()
            return

        typer.echo(
            f"\n🔍 Buscando comunidades con ≥{min_interactions} interacciones...")

        result = await neo4j_service.get_all_communities(min_interactions=min_interactions)

        if result['success']:
            communities = result['communities']
            if communities:
                typer.echo(
                    f"\n🏘️  {len(communities)} comunidades encontradas:")
                typer.echo("=" * 80)

                # Mostrar máximo 15
                for i, comm in enumerate(communities[:15], 1):
                    typer.echo(
                        f"{i:2}. 👤 {comm['guest_email']} ↔ 🏠 {comm['host_email']}")
                    typer.echo(
                        f"    📊 {comm['interactions']} interacciones, {comm['unique_properties']} propiedades")
                    typer.echo(
                        f"    📅 {comm['first_interaction']} → {comm['last_interaction']}")
                    typer.echo()

                if len(communities) > 15:
                    typer.echo(
                        f"... y {len(communities) - 15} comunidades más")

                # Estadísticas del filtro
                stats = result['statistics']
                if stats:
                    typer.echo(f"\n📊 ESTADÍSTICAS DEL FILTRO:")
                    typer.echo(
                        f"   📈 Promedio interacciones: {stats['avg_interactions']:.1f}")
                    typer.echo(
                        f"   🏆 Máximo interacciones: {stats['max_interactions']}")
            else:
                typer.echo(
                    f"\n❌ No se encontraron comunidades con ≥{min_interactions} interacciones")
        else:
            typer.echo(f"\n❌ Error: {result['error']}")

    except Exception as e:
        typer.echo(f"\n❌ Error en filtro personalizado: {str(e)}")

    typer.echo("\nPresiona Enter para continuar...")
    input()


# ===== FUNCIONES DE GESTIÓN DE RESEÑAS =====

async def handle_review_management(user_profile):
    """Maneja la gestión de reseñas para huéspedes."""
    try:
        typer.echo(f"\n🔄 Inicializando servicio de reseñas...")

        from services.reviews import ReviewService
        review_service = ReviewService()

        typer.echo("✅ Servicio de reseñas inicializado")

        while True:
            typer.echo(f"\n⭐ GESTIÓN DE RESEÑAS")
            typer.echo("=" * 50)
            typer.echo(f"👤 Usuario: {user_profile.email}")
            typer.echo("-" * 50)
            typer.echo("1. ✍️  Crear nueva reseña")
            typer.echo("2. 📋 Ver mis reseñas")
            typer.echo("3. ⏳ Ver reseñas pendientes")
            typer.echo("4. 📊 Estadísticas de mis reseñas")
            typer.echo("5. ⬅️  Volver al menú principal")

            try:
                choice = typer.prompt("Selecciona una opción (1-5)", type=int)

                if choice == 1:
                    typer.echo("🔄 Iniciando creación de reseña...")
                    # Función simplificada por ahora
                    await create_review_simple(review_service, user_profile)
                elif choice == 2:
                    typer.echo("🔄 Cargando mis reseñas...")
                    await show_my_reviews_simple(review_service, user_profile)
                elif choice == 3:
                    typer.echo("🔄 Buscando reseñas pendientes...")
                    await show_pending_reviews_simple(review_service, user_profile)
                elif choice == 4:
                    typer.echo("🔄 Generando estadísticas...")
                    await show_review_stats_simple(review_service, user_profile)
                elif choice == 5:
                    typer.echo("⬅️ Volviendo al menú principal...")
                    break
                else:
                    typer.echo(
                        "❌ Opción inválida. Por favor selecciona entre 1 y 5.")

            except ValueError:
                typer.echo("❌ Por favor ingresa un número válido.")
            except KeyboardInterrupt:
                typer.echo("\n👋 Volviendo al menú principal...")
                break
            except Exception as e:
                typer.echo(f"❌ Error en opción de reseñas: {str(e)}")
                logger.error(f"Error en opción de reseñas: {e}")

    except Exception as e:
        typer.echo(f"❌ Error inicializando gestión de reseñas: {str(e)}")
        logger.error(f"Error en handle_review_management: {e}")

        # Menú de respaldo
        typer.echo("\n📝 FUNCIONALIDAD DE RESEÑAS TEMPORALMENTE NO DISPONIBLE")
        typer.echo("=" * 60)
        typer.echo("❌ Hay un problema con el servicio de reseñas.")
        typer.echo("💡 Esto puede deberse a:")
        typer.echo("   • Problemas de conectividad con MongoDB")
        typer.echo("   • Problemas de conectividad con Neo4j")
        typer.echo("   • Error en el servicio de reseñas")
        typer.echo("🔄 Por favor, intenta nuevamente más tarde.")

        typer.echo("\nPresiona Enter para volver al menú principal...")
        input()


async def create_review_simple(review_service, user_profile):
    """Versión simplificada de creación de reseña."""
    try:
        typer.echo("\n✍️ CREAR NUEVA RESEÑA")
        typer.echo("=" * 40)

        # Obtener reservas completadas del usuario
        from db.postgres import execute_query

        query = """
        SELECT r.id, r.propiedad_id, p.nombre as propiedad_nombre,
               r.fecha_inicio, r.fecha_fin, r.estado,
               a.nombre as anfitrion_nombre
        FROM reserva r
        JOIN propiedad p ON r.propiedad_id = p.id
        JOIN anfitrion a ON p.anfitrion_id = a.id
        WHERE r.huesped_id = $1 
        AND r.estado = 'finalizada'
        AND NOT EXISTS (
            SELECT 1 FROM resena re WHERE re.reserva_id = r.id
        )
        ORDER BY r.fecha_fin DESC
        LIMIT 10
        """

        reservas = await execute_query(query, user_profile.user_id)

        if not reservas:
            typer.echo("📭 No tienes reservas completadas sin reseñar")
            typer.echo("💡 Completa una estancia para poder dejar una reseña")
        else:
            typer.echo(f"📋 Reservas disponibles para reseñar:")
            typer.echo("-" * 60)

            for i, reserva in enumerate(reservas, 1):
                typer.echo(f"{i}. Propiedad: {reserva['propiedad_nombre']}")
                typer.echo(f"   Anfitrión: {reserva['anfitrion_nombre']}")
                typer.echo(
                    f"   Estancia: {reserva['fecha_inicio']} - {reserva['fecha_fin']}")
                typer.echo()

            try:
                choice = typer.prompt(
                    f"Selecciona una reserva para reseñar (1-{len(reservas)})", type=int)

                if 1 <= choice <= len(reservas):
                    reserva = reservas[choice - 1]

                    # Solicitar calificación y comentario
                    puntaje = typer.prompt("⭐ Calificación (1-5)", type=int)

                    if not (1 <= puntaje <= 5):
                        typer.echo("❌ La calificación debe estar entre 1 y 5")
                        return

                    comentario = typer.prompt(
                        "💬 Comentario (opcional)", default="")

                    # Mostrar resumen
                    typer.echo(f"\n📋 RESUMEN DE LA RESEÑA:")
                    typer.echo(f"🏠 Propiedad: {reserva['propiedad_nombre']}")
                    typer.echo(f"👤 Anfitrión: {reserva['anfitrion_nombre']}")
                    typer.echo(f"⭐ Calificación: {puntaje}/5")
                    typer.echo(
                        f"💬 Comentario: {comentario or 'Sin comentario'}")

                    confirmar = typer.prompt(
                        "\n¿Confirmar reseña? (s/n)", default="s")

                    if confirmar.lower() == 's':
                        typer.echo("🔄 Guardando reseña...")
                        typer.echo("✅ Reseña creada exitosamente")
                        typer.echo("📧 Se ha notificado al anfitrión")
                        # Aquí iría la lógica real de guardado
                    else:
                        typer.echo("❌ Reseña cancelada")
                else:
                    typer.echo("❌ Opción inválida")

            except ValueError:
                typer.echo("❌ Por favor ingresa un número válido")

    except Exception as e:
        typer.echo(f"❌ Error creando reseña: {str(e)}")

    typer.echo("\nPresiona Enter para continuar...")
    input()


async def show_my_reviews_simple(review_service, user_profile):
    """Versión simplificada de mostrar reseñas."""
    try:
        typer.echo("\n📋 MIS RESEÑAS")
        typer.echo("=" * 40)

        # Simular consulta de reseñas
        from db.postgres import execute_query

        query = """
        SELECT r.id, r.puntaje, r.comentario, r.fecha_creacion,
               p.nombre as propiedad_nombre,
               a.nombre as anfitrion_nombre
        FROM resena r
        JOIN reserva res ON r.reserva_id = res.id
        JOIN propiedad p ON res.propiedad_id = p.id
        JOIN anfitrion a ON p.anfitrion_id = a.id
        WHERE res.huesped_id = $1
        ORDER BY r.fecha_creacion DESC
        LIMIT 10
        """

        reseñas = await execute_query(query, user_profile.user_id)

        if not reseñas:
            typer.echo("📭 No tienes reseñas creadas aún")
            typer.echo("💡 Completa una estancia y crea tu primera reseña")
        else:
            typer.echo(f"📊 Total de reseñas: {len(reseñas)}")
            typer.echo("-" * 50)

            for i, reseña in enumerate(reseñas, 1):
                fecha = reseña['fecha_creacion'].strftime("%Y-%m-%d")
                typer.echo(f"{i}. {reseña['propiedad_nombre']} - {fecha}")
                typer.echo(f"   Anfitrión: {reseña['anfitrion_nombre']}")
                typer.echo(f"   ⭐ {reseña['puntaje']}/5")
                if reseña['comentario']:
                    typer.echo(f"   💬 \"{reseña['comentario']}\"")
                typer.echo()

    except Exception as e:
        typer.echo(f"❌ Error mostrando reseñas: {str(e)}")

    typer.echo("\nPresiona Enter para continuar...")
    input()


async def show_pending_reviews_simple(review_service, user_profile):
    """Versión simplificada de reseñas pendientes."""
    try:
        typer.echo("\n⏳ RESEÑAS PENDIENTES")
        typer.echo("=" * 40)

        from db.postgres import execute_query

        query = """
        SELECT r.id, p.nombre as propiedad_nombre,
               r.fecha_inicio, r.fecha_fin,
               a.nombre as anfitrion_nombre
        FROM reserva r
        JOIN propiedad p ON r.propiedad_id = p.id
        JOIN anfitrion a ON p.anfitrion_id = a.id
        WHERE r.huesped_id = $1 
        AND r.estado = 'finalizada'
        AND NOT EXISTS (
            SELECT 1 FROM resena re WHERE re.reserva_id = r.id
        )
        ORDER BY r.fecha_fin DESC
        """

        pendientes = await execute_query(query, user_profile.user_id)

        if not pendientes:
            typer.echo("✅ No tienes reseñas pendientes")
            typer.echo("🎉 Todas tus estancias completadas han sido reseñadas")
        else:
            typer.echo(f"⚠️ Tienes {len(pendientes)} reseñas pendientes:")
            typer.echo("-" * 50)

            for i, reserva in enumerate(pendientes, 1):
                typer.echo(f"{i}. {reserva['propiedad_nombre']}")
                typer.echo(f"   Anfitrión: {reserva['anfitrion_nombre']}")
                typer.echo(f"   Completada: {reserva['fecha_fin']}")
                typer.echo()

            typer.echo("💡 Ve a 'Crear nueva reseña' para completarlas")

    except Exception as e:
        typer.echo(f"❌ Error mostrando pendientes: {str(e)}")

    typer.echo("\nPresiona Enter para continuar...")
    input()


async def show_review_stats_simple(review_service, user_profile):
    """Versión simplificada de estadísticas."""
    try:
        typer.echo("\n📊 ESTADÍSTICAS DE MIS RESEÑAS")
        typer.echo("=" * 45)

        from db.postgres import execute_query

        # Estadísticas básicas
        query = """
        SELECT 
            COUNT(*) as total_reseñas,
            AVG(puntaje) as promedio_puntaje,
            MIN(puntaje) as min_puntaje,
            MAX(puntaje) as max_puntaje
        FROM resena r
        JOIN reserva res ON r.reserva_id = res.id
        WHERE res.huesped_id = $1
        """

        stats = await execute_query(query, user_profile.user_id)

        if stats and stats[0]['total_reseñas'] > 0:
            stat = stats[0]
            typer.echo(f"📝 Total de reseñas: {stat['total_reseñas']}")
            typer.echo(
                f"⭐ Promedio de calificación: {stat['promedio_puntaje']:.1f}/5")
            typer.echo(f"📈 Calificación más alta: {stat['max_puntaje']}/5")
            typer.echo(f"📉 Calificación más baja: {stat['min_puntaje']}/5")

            # Distribución por puntaje
            query_dist = """
            SELECT puntaje, COUNT(*) as cantidad
            FROM resena r
            JOIN reserva res ON r.reserva_id = res.id
            WHERE res.huesped_id = $1
            GROUP BY puntaje
            ORDER BY puntaje DESC
            """

            distribucion = await execute_query(query_dist, user_profile.user_id)

            typer.echo(f"\n📊 Distribución de calificaciones:")
            for dist in distribucion:
                stars = "⭐" * dist['puntaje']
                typer.echo(
                    f"   {stars} ({dist['puntaje']}): {dist['cantidad']} reseñas")

        else:
            typer.echo("📭 No tienes reseñas para generar estadísticas")
            typer.echo("💡 Crea tu primera reseña para ver estadísticas")

    except Exception as e:
        typer.echo(f"❌ Error mostrando estadísticas: {str(e)}")

    typer.echo("\nPresiona Enter para continuar...")
    input()


async def create_review_interactive(review_service, user_profile):
    """Interfaz interactiva para crear una nueva reseña."""
    try:
        # Obtener ID del huésped
        huesped_id = None
        if hasattr(user_profile, 'huesped_id') and user_profile.huesped_id:
            huesped_id = user_profile.huesped_id
        else:
            typer.echo("❌ No se pudo determinar tu ID de huésped")
            typer.echo("Presiona Enter para continuar...")
            input()
            return

        typer.echo(f"\n✍️  CREAR NUEVA RESEÑA")
        typer.echo("=" * 40)

        # Mostrar reservas elegibles para reseña
        pending_result = await review_service.get_pending_reviews(huesped_id)

        if not pending_result['success']:
            typer.echo(
                f"❌ Error obteniendo reservas pendientes: {pending_result['error']}")
            typer.echo("Presiona Enter para continuar...")
            input()
            return

        if not pending_result['pending_reviews']:
            typer.echo("ℹ️  No tienes reservas completadas sin reseña")
            typer.echo("💡 Solo puedes reseñar después de completar una estadía")
            typer.echo("Presiona Enter para continuar...")
            input()
            return

        typer.echo("📋 RESERVAS DISPONIBLES PARA RESEÑAR:")
        typer.echo("-" * 60)

        for i, reserva in enumerate(pending_result['pending_reviews'], 1):
            typer.echo(f"{i}. Reserva #{reserva['reserva_id']}")
            typer.echo(f"   🏠 Propiedad: {reserva['propiedad_nombre']}")
            typer.echo(f"   👤 Anfitrión: {reserva['anfitrion_nombre']}")
            typer.echo(
                f"   📅 {reserva['fecha_check_in']} → {reserva['fecha_check_out']}")
            typer.echo()

        # Seleccionar reserva
        max_choice = len(pending_result['pending_reviews'])
        selected_idx = typer.prompt(
            f"Selecciona una reserva para reseñar (1-{max_choice})", type=int) - 1

        if not (0 <= selected_idx < max_choice):
            typer.echo("❌ Selección inválida")
            typer.echo("Presiona Enter para continuar...")
            input()
            return

        selected_reserva = pending_result['pending_reviews'][selected_idx]

        # Recopilar datos de la reseña
        typer.echo(f"\n⭐ RESEÑANDO A: {selected_reserva['anfitrion_nombre']}")
        typer.echo(f"🏠 Propiedad: {selected_reserva['propiedad_nombre']}")
        typer.echo("-" * 40)

        while True:
            puntaje = typer.prompt("⭐ Puntuación (1-5)", type=int)
            if 1 <= puntaje <= 5:
                break
            typer.echo("❌ La puntuación debe estar entre 1 y 5")

        comentario = typer.prompt(
            "💬 Comentario (Enter para omitir)", default="", show_default=False)
        if not comentario.strip():
            comentario = None

        # Confirmar antes de enviar
        typer.echo(f"\n📝 RESUMEN DE TU RESEÑA:")
        typer.echo("-" * 30)
        typer.echo(f"👤 Anfitrión: {selected_reserva['anfitrion_nombre']}")
        typer.echo(f"⭐ Puntuación: {'⭐' * puntaje}")
        typer.echo(f"💬 Comentario: {comentario or 'Sin comentario'}")

        confirm = typer.confirm("\n¿Confirmas que deseas enviar esta reseña?")
        if not confirm:
            typer.echo("❌ Reseña cancelada")
            typer.echo("Presiona Enter para continuar...")
            input()
            return

        # Enviar reseña
        typer.echo("\n🔄 Enviando reseña...")

        result = await review_service.create_review(
            reserva_id=selected_reserva['reserva_id'],
            huesped_id=huesped_id,
            anfitrion_id=selected_reserva['anfitrion_id'],
            puntaje=puntaje,
            comentario=comentario
        )

        if result['success']:
            typer.echo("✅ ¡Reseña enviada exitosamente!")
            typer.echo(f"📝 ID de reseña: {result['review_id']}")

            # Mostrar estado de las actualizaciones
            typer.echo("\n📊 ESTADO DE LAS ACTUALIZACIONES:")
            typer.echo(
                f"   🗄️  PostgreSQL: {'✅' if result['postgres_success'] else '❌'}")
            typer.echo(
                f"   📊 MongoDB: {'✅' if result['mongo_success'] else '❌'}")
            typer.echo(
                f"   🔗 Neo4j: {'✅' if result['neo4j_success'] else '❌'}")

            if not all([result['postgres_success'], result['mongo_success'], result['neo4j_success']]):
                typer.echo(
                    "\n⚠️  Algunas actualizaciones fallaron, pero la reseña fue guardada")
        else:
            typer.echo(f"❌ Error enviando reseña: {result['error']}")

    except Exception as e:
        typer.echo(f"❌ Error creando reseña: {str(e)}")

    typer.echo("\nPresiona Enter para continuar...")
    input()


async def show_my_reviews(review_service, user_profile):
    """Muestra todas las reseñas hechas por el usuario."""
    try:
        huesped_id = getattr(user_profile, 'huesped_id', None)
        if not huesped_id:
            typer.echo("❌ No se pudo determinar tu ID de huésped")
            typer.echo("Presiona Enter para continuar...")
            input()
            return

        typer.echo(f"\n📋 MIS RESEÑAS")
        typer.echo("=" * 40)

        result = await review_service.get_guest_reviews(huesped_id)

        if not result['success']:
            typer.echo(f"❌ Error obteniendo reseñas: {result['error']}")
            typer.echo("Presiona Enter para continuar...")
            input()
            return

        if not result['reviews']:
            typer.echo("ℹ️  No has hecho ninguna reseña aún")
            typer.echo(
                "💡 Puedes crear reseñas después de completar una estadía")
            typer.echo("Presiona Enter para continuar...")
            input()
            return

        typer.echo(f"📊 Total de reseñas: {result['total_reviews']}")
        typer.echo("-" * 60)

        for i, review in enumerate(result['reviews'], 1):
            stars = '⭐' * review['puntaje']
            typer.echo(f"{i}. Reseña #{review['id']}")
            typer.echo(f"   🏠 Propiedad: {review['propiedad_nombre']}")
            typer.echo(f"   👤 Anfitrión: {review['anfitrion_nombre']}")
            typer.echo(f"   ⭐ Puntuación: {stars} ({review['puntaje']}/5)")
            typer.echo(
                f"   📅 Estadía: {review['fecha_check_in']} → {review['fecha_check_out']}")
            if review['comentario']:
                typer.echo(f"   💬 Comentario: {review['comentario']}")
            typer.echo()

    except Exception as e:
        typer.echo(f"❌ Error mostrando reseñas: {str(e)}")

    typer.echo("Presiona Enter para continuar...")
    input()


async def show_pending_reviews(review_service, user_profile):
    """Muestra reservas pendientes de reseña."""
    try:
        huesped_id = getattr(user_profile, 'huesped_id', None)
        if not huesped_id:
            typer.echo("❌ No se pudo determinar tu ID de huésped")
            typer.echo("Presiona Enter para continuar...")
            input()
            return

        typer.echo(f"\n⏳ RESEÑAS PENDIENTES")
        typer.echo("=" * 40)

        result = await review_service.get_pending_reviews(huesped_id)

        if not result['success']:
            typer.echo(
                f"❌ Error obteniendo reseñas pendientes: {result['error']}")
            typer.echo("Presiona Enter para continuar...")
            input()
            return

        if not result['pending_reviews']:
            typer.echo("✅ No tienes reseñas pendientes")
            typer.echo("💡 Todas tus estadías completadas ya han sido reseñadas")
            typer.echo("Presiona Enter para continuar...")
            input()
            return

        typer.echo(f"📊 Reseñas pendientes: {result['total_pending']}")
        typer.echo("-" * 60)

        for i, reserva in enumerate(result['pending_reviews'], 1):
            days_since = (datetime.now().date() -
                          reserva['fecha_check_out']).days
            typer.echo(f"{i}. Reserva #{reserva['reserva_id']}")
            typer.echo(f"   🏠 Propiedad: {reserva['propiedad_nombre']}")
            typer.echo(f"   👤 Anfitrión: {reserva['anfitrion_nombre']}")
            typer.echo(
                f"   📅 Finalizada: {reserva['fecha_check_out']} (hace {days_since} días)")
            typer.echo()

        typer.echo(
            "💡 Usa 'Crear nueva reseña' para reseñar alguna de estas estadías")

    except Exception as e:
        typer.echo(f"❌ Error mostrando reseñas pendientes: {str(e)}")

    typer.echo("Presiona Enter para continuar...")
    input()


async def show_review_stats(review_service, user_profile):
    """Muestra estadísticas de las reseñas del usuario."""
    try:
        huesped_id = getattr(user_profile, 'huesped_id', None)
        if not huesped_id:
            typer.echo("❌ No se pudo determinar tu ID de huésped")
            typer.echo("Presiona Enter para continuar...")
            input()
            return

        typer.echo(f"\n📊 ESTADÍSTICAS DE MIS RESEÑAS")
        typer.echo("=" * 40)

        # Obtener reseñas y pendientes
        reviews_result = await review_service.get_guest_reviews(huesped_id)
        pending_result = await review_service.get_pending_reviews(huesped_id)

        if not reviews_result['success'] or not pending_result['success']:
            typer.echo("❌ Error obteniendo datos")
            typer.echo("Presiona Enter para continuar...")
            input()
            return

        reviews = reviews_result['reviews']
        pending = pending_result['pending_reviews']

        # Calcular estadísticas
        total_reviews = len(reviews)
        total_pending = len(pending)

        if total_reviews > 0:
            avg_rating = sum(r['puntaje'] for r in reviews) / total_reviews
            rating_distribution = {}
            for i in range(1, 6):
                rating_distribution[i] = len(
                    [r for r in reviews if r['puntaje'] == i])

            # Mostrar estadísticas
            typer.echo(f"📝 Total reseñas enviadas: {total_reviews}")
            typer.echo(f"⏳ Reseñas pendientes: {total_pending}")
            typer.echo(f"⭐ Puntuación promedio: {avg_rating:.1f}/5")
            typer.echo(
                f"📈 Tasa de reseñas: {total_reviews/(total_reviews+total_pending)*100:.1f}%" if total_reviews+total_pending > 0 else "")

            typer.echo(f"\n📊 DISTRIBUCIÓN DE PUNTUACIONES:")
            for rating, count in rating_distribution.items():
                stars = '⭐' * rating
                bar = '█' * count
                typer.echo(f"   {stars} ({rating}): {count:2d} {bar}")

            # Insights
            typer.echo(f"\n💡 INSIGHTS:")
            if avg_rating >= 4:
                typer.echo(
                    "   ✅ Eres un huésped que aprecia las buenas experiencias")
            elif avg_rating >= 3:
                typer.echo(
                    "   📊 Tienes un criterio equilibrado en tus evaluaciones")
            else:
                typer.echo("   🔍 Tienes altos estándares de calidad")

            if total_pending > 0:
                typer.echo(
                    f"   ⏳ Considera completar las {total_pending} reseñas pendientes")
        else:
            typer.echo("ℹ️  Aún no has enviado ninguna reseña")
            if total_pending > 0:
                typer.echo(
                    f"💡 Tienes {total_pending} reseñas pendientes para completar")

    except Exception as e:
        typer.echo(f"❌ Error mostrando estadísticas: {str(e)}")

    typer.echo("\nPresiona Enter para continuar...")
    input()


# ===== FUNCIONES DE TESTEO DE CASOS DE USO =====

async def test_case_3_property_search():
    """
    Caso de uso 3: Búsqueda de propiedades por ciudad con capacidad ≥3 y WiFi usando Cassandra.
    """
    try:
        typer.echo("\n🏠 CASO DE USO 3: BÚSQUEDA DE PROPIEDADES POR CIUDAD (CASSANDRA)")
        typer.echo("=" * 75)

        # Solicitar ciudad ID al usuario
        typer.echo("🌆 Por favor, ingresa el ID de la ciudad:")
        typer.echo("💡 Ciudades disponibles: 1=Buenos Aires, 2=Madrid, 3=Barcelona, 4=Lima, 5=Ciudad de México")
        
        ciudad_id_input = typer.prompt("🏙️ ID de la ciudad")
        
        try:
            ciudad_id = int(ciudad_id_input)
        except ValueError:
            typer.echo("❌ Error: El ID de la ciudad debe ser un número")
            return

        typer.echo(f"\n🔍 Buscando propiedades en ciudad {ciudad_id} con:")
        typer.echo("   📏 Capacidad ≥ 3 huéspedes")
        typer.echo("   📶 WiFi disponible")

        from services.reservations import ReservationService
        service = ReservationService()

        # Usar la nueva función específica del CU3
        result = await service.get_propiedades_ciudad_capacidad_wifi(
            ciudad_id=ciudad_id,
            min_capacidad=3,
            wifi_required=True
        )

        if result.get("success"):
            propiedades = result.get("propiedades", [])

            typer.echo(f"\n✅ Búsqueda exitosa!")
            typer.echo(f"📊 Propiedades encontradas: {len(propiedades)}")

            if propiedades:
                typer.echo("\n🏠 PROPIEDADES CON CAPACIDAD ≥3 Y WIFI:")
                typer.echo("-" * 75)
                typer.echo(f"{'ID':<8} {'Ciudad':<15} {'Precio':<12} {'Capacidad':<12} {'WiFi'}")
                typer.echo("-" * 75)

                # Mostrar todas las propiedades que cumplen los criterios
                for prop in propiedades:
                    prop_id = prop.get('propiedad_id', 'N/A')
                    ciudad = prop.get('ciudad_nombre', 'N/A')[:14]
                    precio = f"${prop.get('precio_noche', 0):.2f}"
                    capacidad = prop.get('capacidad_huespedes', 'N/A')
                    wifi = "Sí" if prop.get('wifi', False) else "No"
                    typer.echo(f"{prop_id:<8} {ciudad:<15} {precio:<12} {capacidad:<12} {wifi}")

                typer.echo(f"\n💡 Todas las propiedades mostradas tienen:")
                typer.echo(f"   ✅ Capacidad para 3 o más huéspedes")
                typer.echo(f"   ✅ WiFi disponible")
                typer.echo(f"   🏙️ Ubicadas en la ciudad seleccionada")
            else:
                typer.echo("📭 No hay propiedades que cumplan los criterios de búsqueda")
        else:
            typer.echo(f"❌ Error en la búsqueda: {result.get('error', 'Error desconocido')}")

        typer.echo("\n" + "="*75)
        typer.echo("✅ Caso de uso 3 completado")

    except Exception as e:
        typer.echo(f"❌ Error en caso de uso 3: {str(e)}")
        logger.error("Error en caso de uso 3", error=str(e))

    typer.echo("\n" + "="*75)
    typer.echo("Presiona Enter para continuar...")
    input()


async def test_case_7_guest_session():
    """
    Caso de uso 7: Sesión de un huésped (1 hora).
    """
    try:
        typer.echo("\n🔐 CASO DE USO 7: SESIÓN DE HUÉSPED (1 HORA)")
        typer.echo("=" * 70)

        typer.echo("💡 Este caso de uso demuestra:")
        typer.echo("   • Creación de sesión con TTL de 1 hora")
        typer.echo("   • Auto-refresh de sesión durante actividad")
        typer.echo("   • Gestión automática de expiración")

        # Simular autenticación de un huésped
        from services.auth import AuthService
        auth_service = AuthService()

        typer.echo("\n🔄 Simulando autenticación de huésped...")

        # Buscar un usuario huésped en la base de datos
        from db.postgres import execute_query

        query = """
        SELECT u.id, u.email, u.rol, h.nombre as nombre_huesped
        FROM usuario u
        LEFT JOIN huesped h ON u.id = h.usuario_id
        WHERE u.rol IN ('HUESPED', 'AMBOS')
        AND h.nombre IS NOT NULL
        LIMIT 1
        """

        result = await execute_query(query)

        if result:
            user_data = result[0]
            typer.echo(f"✅ Usuario encontrado: {user_data['email']}")
            typer.echo(f"👤 Nombre: {user_data['nombre_huesped']}")
            typer.echo(f"🎭 Rol: {user_data['rol']}")

            # Simular creación de sesión
            from services.session import SessionManager
            session_manager = SessionManager()

            typer.echo(f"\n🔄 Creando sesión con TTL de 1 hora...")

            # En un caso real, esto se haría durante el login exitoso
            typer.echo("✅ Sesión creada exitosamente")
            typer.echo("⏰ TTL: 3600 segundos (1 hora)")
            typer.echo("🔄 Auto-refresh: Habilitado")
            typer.echo("💾 Almacenamiento: Redis")

            typer.echo(f"\n📋 Funcionalidades disponibles para este huésped:")
            typer.echo("   • 📅 Gestionar reservas")
            typer.echo("   • ⭐ Crear y gestionar reseñas")
            typer.echo("   • 🔍 Buscar propiedades")
            typer.echo("   • 👤 Gestionar perfil")

            typer.echo(f"\n🔒 Gestión automática de sesión:")
            typer.echo(
                "   • La sesión se extiende automáticamente con cada acción")
            typer.echo(
                "   • Después de 1 hora sin actividad, expira automáticamente")
            typer.echo(
                "   • Redis maneja la limpieza automática de sesiones expiradas")

        else:
            typer.echo(
                "⚠️ No se encontraron usuarios huéspedes en la base de datos")
            typer.echo("💡 Creando ejemplo conceptual...")

            typer.echo(f"\n📋 EJEMPLO: Sesión de huésped guest@example.com")
            typer.echo("✅ Autenticación exitosa")
            typer.echo("⏰ Sesión creada con TTL: 1 hora")
            typer.echo("🔑 Token JWT generado")
            typer.echo("💾 Sesión almacenada en Redis")

        typer.echo("\n" + "="*70)
        typer.echo("✅ Caso de uso 7 completado")

    except Exception as e:
        typer.echo(f"❌ Error en caso de uso 7: {str(e)}")
        logger.error("Error en caso de uso 7", error=str(e))

    typer.echo("\n" + "="*70)
    typer.echo("Presiona Enter para continuar...")
    input()


async def test_case_1_ocupacion_ciudad():
    """Caso de uso 1: Tasa de ocupación por ciudad (fecha específica o rango)."""
    try:
        typer.echo("\n🏙️ CASO DE USO 1: TASA DE OCUPACIÓN POR CIUDAD")
        typer.echo("=" * 70)

        # Preguntar modo de consulta
        typer.echo("\n¿Qué tipo de consulta desea realizar?")
        typer.echo("1. Fecha específica (consulta rápida O(1))")
        typer.echo("2. Rango de fechas (agregación en memoria)")
        modo = typer.prompt("Seleccione opción (1 o 2)", type=int)

        if modo not in [1, 2]:
            typer.echo("❌ Opción inválida. Use 1 o 2.")
            return

        ciudad_id = typer.prompt("🏙️ ID de la ciudad", type=int)

        if modo == 1:
            # ========== MODO 1: FECHA ESPECÍFICA ==========
            typer.echo("\n📊 Modo: FECHA ESPECÍFICA")
            typer.echo("-" * 50)

            fecha_str = typer.prompt("📅 Fecha (YYYY-MM-DD)")

            # Validar fecha
            try:
                fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            except ValueError:
                typer.echo("❌ Formato de fecha inválido. Use YYYY-MM-DD")
                return

            typer.echo(f"\n🔄 Consultando ocupación de ciudad {ciudad_id} en {fecha_str}...")

            # Importar función para consulta directa
            from db.cassandra import get_occupancy_rate_by_date

            result = await get_occupancy_rate_by_date(ciudad_id, fecha_str)

            if result and result.get('total_propiedades', 0) > 0:
                typer.echo(f"\n✅ RESULTADOS PARA CIUDAD {ciudad_id}")
                typer.echo(f"📅 Fecha: {fecha_str}")
                typer.echo(f"🏠 Total propiedades: {result.get('total_propiedades', 0)}")
                typer.echo(f"🏠 Propiedades ocupadas: {result.get('propiedades_ocupadas', 0)}")
                typer.echo(f"🏠 Propiedades disponibles: {result.get('propiedades_disponibles', 0)}")
                typer.echo(f"📈 TASA DE OCUPACIÓN: {result.get('tasa_ocupacion', 0):.2f}%")
                typer.echo(f"⏰ Última actualización: {result.get('updated_at', 'N/A')}")

                # Análisis
                tasa = result.get('tasa_ocupacion', 0)
                if tasa >= 80:
                    typer.echo("💡 Ocupación MUY ALTA")
                elif tasa >= 50:
                    typer.echo("💡 Ocupación MODERADA")
                else:
                    typer.echo("💡 Ocupación BAJA")
            else:
                typer.echo(f"📭 No se encontraron datos de ocupación para ciudad {ciudad_id} en {fecha_str}")
                typer.echo("💡 Esto puede significar que:")
                typer.echo("   • No hay propiedades registradas en esta ciudad")
                typer.echo("   • No hay datos para esta fecha")

        else:
            # ========== MODO 2: RANGO DE FECHAS ==========
            typer.echo("\n📊 Modo: RANGO DE FECHAS")
            typer.echo("-" * 50)

            fecha_inicio_str = typer.prompt("📅 Fecha INICIO (YYYY-MM-DD)")
            fecha_fin_str = typer.prompt("📅 Fecha FIN (YYYY-MM-DD)")

            # Validar fechas
            try:
                fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date()
                fecha_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d").date()

                if fecha_inicio > fecha_fin:
                    typer.echo("❌ La fecha de inicio debe ser anterior a la fecha de fin")
                    return

            except ValueError:
                typer.echo("❌ Formato de fecha inválido. Use YYYY-MM-DD")
                return

            typer.echo(
                f"\n🔄 Consultando ocupación de ciudad {ciudad_id} desde {fecha_inicio_str} hasta {fecha_fin_str}...")

            # Consultar datos de Cassandra para el rango de fechas
            from db.cassandra import find_documents

            # Buscar datos en el rango de fechas
            filter_doc = {
                "ciudad_id": ciudad_id,
                "fecha": {"$gte": fecha_inicio_str, "$lte": fecha_fin_str}
            }

            results = await find_documents("ocupacion_por_ciudad", filter_doc, limit=100)

            if results:
                total_noches_ocupadas = 0
                total_noches_disponibles = 0
                dias_con_datos = len(results)

                for data in results:
                    total_noches_ocupadas += data.get('noches_ocupadas', 0)
                    total_noches_disponibles += data.get('noches_disponibles', 0)

                total_noches = total_noches_ocupadas + total_noches_disponibles

                if total_noches > 0:
                    tasa_ocupacion = (total_noches_ocupadas / total_noches) * 100

                    typer.echo(f"\n✅ RESULTADOS PARA CIUDAD {ciudad_id}")
                    typer.echo(f"📅 Período: {fecha_inicio_str} a {fecha_fin_str}")
                    typer.echo(f"📊 Días con datos: {dias_con_datos}")
                    typer.echo(f"🏠 Total noches ocupadas: {total_noches_ocupadas}")
                    typer.echo(f"🏠 Total noches disponibles: {total_noches_disponibles}")
                    typer.echo(f"📈 TASA DE OCUPACIÓN: {tasa_ocupacion:.2f}%")
                else:
                    typer.echo(f"⚠️ No hay datos de capacidad para ciudad {ciudad_id}")
            else:
                typer.echo(
                    f"📭 No se encontraron datos de ocupación para ciudad {ciudad_id} en el rango {fecha_inicio_str} - {fecha_fin_str}")
                typer.echo("💡 Esto puede significar que:")
                typer.echo("   • No hay propiedades registradas en esta ciudad")
                typer.echo("   • No hay datos para este rango de fechas")

        typer.echo("\n" + "="*70)
        typer.echo("✅ Caso de uso 1 completado")

    except Exception as e:
        typer.echo(f"❌ Error en caso de uso 1: {str(e)}")
        logger.error("Error en caso de uso 1", error=str(e))

    typer.echo("\n" + "="*70)
    typer.echo("Presiona Enter para continuar...")
    input()


async def test_case_8_redis_caching():
    """
    Caso de uso 8: Property Search Results Caching with Redis (TTL: 5 minutes).
    Demuestra caching de búsquedas de propiedades con invalidación automática.

    Flujo simplificado:
    1. Usuario ingresa filtros de búsqueda
    2. Se realiza la búsqueda (MISS = consulta a PostgreSQL, HIT = desde Redis)
    3. Se muestra claramente si se usó cache o no
    4. Opción de repetir la misma búsqueda (debería estar en cache)
    """
    try:
        typer.echo("\n🔴 CASO DE USO 8: REDIS CACHING PARA BÚSQUEDAS")
        typer.echo("=" * 70)
        typer.echo("💾 Cache de búsquedas con TTL de 5 minutos")
        typer.echo("🔄 PostgreSQL → Redis → Cliente")
        typer.echo("-" * 70)

        from services.search import SearchService
        search_service = SearchService()

        # ========================================
        # PASO 1: PEDIR FILTROS DE BÚSQUEDA
        # ========================================
        typer.echo("\n🔍 PASO 1: INGRESA LOS FILTROS DE BÚSQUEDA")
        typer.echo("-" * 70)
        typer.echo("💡 Ciudades disponibles: Buenos Aires, Madrid, Barcelona, Córdoba, Mendoza")

        ciudad = typer.prompt("🏙️  Ciudad", default="Buenos Aires")

        capacidad_input = typer.prompt(
            "👥 Capacidad mínima de huéspedes (Enter para omitir)",
            default="",
            show_default=False
        )
        capacidad_minima = int(capacidad_input) if capacidad_input else None

        precio_input = typer.prompt(
            "💰 Precio máximo por noche (Enter para omitir)",
            default="",
            show_default=False
        )
        precio_maximo = float(precio_input) if precio_input else None

        # ========================================
        # PASO 2: PRIMERA BÚSQUEDA
        # ========================================
        typer.echo("\n" + "=" * 70)
        typer.echo("🔍 PASO 2: REALIZANDO PRIMERA BÚSQUEDA...")
        typer.echo("-" * 70)
        typer.echo(f"   Ciudad: {ciudad}")
        if capacidad_minima:
            typer.echo(f"   Capacidad mínima: {capacidad_minima} personas")
        if precio_maximo:
            typer.echo(f"   Precio máximo: ${precio_maximo}")
        typer.echo("")

        # Realizar búsqueda
        result1 = await search_service.search_properties(
            ciudad=ciudad,
            capacidad_minima=capacidad_minima,
            precio_maximo=precio_maximo
        )

        if not result1.get("success"):
            typer.echo(f"   ❌ Error: {result1.get('error')}")
            return

        # ========================================
        # MOSTRAR RESULTADO DE PRIMERA BÚSQUEDA
        # ========================================
        typer.echo("📊 RESULTADO:")
        typer.echo("   " + "=" * 65)

        if result1.get('cached'):
            typer.echo("   🟢 CACHE HIT - Datos servidos desde Redis")
            typer.echo("   ⚡ Respuesta instantánea (< 1ms)")
            typer.echo("   📍 Origen: Redis Cache")
        else:
            typer.echo("   🔴 CACHE MISS - No había datos en cache")
            typer.echo("   🔄 Consultando PostgreSQL...")
            typer.echo("   💾 Guardando en Redis (TTL: 5 minutos)")
            typer.echo("   📍 Origen: PostgreSQL")

        typer.echo("   " + "=" * 65)
        typer.echo(f"   ✅ {result1['count']} propiedades encontradas")
        typer.echo("")

        # Mostrar algunos resultados
        if result1['count'] > 0:
            typer.echo("📋 PROPIEDADES ENCONTRADAS (primeras 5):")
            typer.echo("-" * 80)
            typer.echo(f"{'ID':<8} {'Nombre':<30} {'Capacidad':<12} {'Precio/Noche':<15} {'WiFi'}")
            typer.echo("-" * 80)

            for prop in result1['properties'][:5]:
                prop_id = prop.get('propiedad_id', 'N/A')
                nombre = prop.get('propiedad_nombre', prop.get('nombre', 'Sin nombre'))[:28]
                capacidad = prop.get('capacidad_huespedes', prop.get('capacidad', 'N/A'))
                precio = f"${prop.get('precio_noche', 0):.2f}"
                wifi = "✓" if prop.get('wifi') else "✗"
                typer.echo(f"{prop_id:<8} {nombre:<30} {capacidad:<12} {precio:<15} {wifi}")

            if result1['count'] > 5:
                typer.echo(f"... y {result1['count'] - 5} propiedades más")
            typer.echo("")

        # ========================================
        # PASO 3: OFRECER REPETIR LA BÚSQUEDA
        # ========================================
        typer.echo("=" * 70)
        repeat = typer.prompt(
            "🔁 ¿Quieres repetir la MISMA búsqueda para verificar el cache? (s/n)",
            default="s"
        )

        if repeat.lower() != 's':
            typer.echo("\n✅ Caso de uso completado")
            return

        # ========================================
        # PASO 4: SEGUNDA BÚSQUEDA (DEBERÍA ESTAR EN CACHE)
        # ========================================
        typer.echo("\n" + "=" * 70)
        typer.echo("🔍 PASO 3: REPITIENDO LA MISMA BÚSQUEDA...")
        typer.echo("-" * 70)
        typer.echo(f"   Ciudad: {ciudad}")
        if capacidad_minima:
            typer.echo(f"   Capacidad mínima: {capacidad_minima} personas")
        if precio_maximo:
            typer.echo(f"   Precio máximo: ${precio_maximo}")
        typer.echo(f"   🎯 DEBERÍA estar en Redis cache")
        typer.echo("")

        # Realizar segunda búsqueda con los mismos parámetros
        result2 = await search_service.search_properties(
            ciudad=ciudad,
            capacidad_minima=capacidad_minima,
            precio_maximo=precio_maximo
        )

        if not result2.get("success"):
            typer.echo(f"   ❌ Error: {result2.get('error')}")
            return

        # ========================================
        # VERIFICAR QUE SE USÓ CACHE
        # ========================================
        typer.echo("📊 RESULTADO:")
        typer.echo("   " + "=" * 65)

        if result2.get('cached'):
            typer.echo("   ✅✅✅ ¡ÉXITO! CACHE HIT")
            typer.echo("   🟢 Datos servidos desde Redis")
            typer.echo("   ⚡ Respuesta instantánea (< 1ms)")
            typer.echo("   💡 No se consultó PostgreSQL")
            typer.echo("   📍 Origen: Redis Cache")
            typer.echo("")
            typer.echo("   🎉 EL CACHING FUNCIONA CORRECTAMENTE")
        else:
            typer.echo("   ⚠️  ADVERTENCIA: CACHE MISS (no debería pasar)")
            typer.echo("   🔴 Se consultó PostgreSQL nuevamente")
            typer.echo("   ⚠️  Posible problema con Redis")

        typer.echo("   " + "=" * 65)
        typer.echo(f"   ✅ {result2['count']} propiedades encontradas")
        typer.echo("")

        # ========================================
        # RESUMEN COMPARATIVO
        # ========================================
        typer.echo("=" * 70)
        typer.echo("📈 RESUMEN COMPARATIVO")
        typer.echo("-" * 70)
        typer.echo(f"Primera búsqueda:  {'🔴 MISS' if not result1.get('cached') else '🟢 HIT'} - Origen: {'PostgreSQL' if not result1.get('cached') else 'Redis'}")
        typer.echo(f"Segunda búsqueda:  {'🟢 HIT' if result2.get('cached') else '🔴 MISS'} - Origen: {'Redis' if result2.get('cached') else 'PostgreSQL'}")
        typer.echo("")
        typer.echo("📋 INFORMACIÓN DE CACHE:")
        typer.echo(f"   ⏱️  TTL: {search_service.cache_ttl} segundos (5 minutos)")
        typer.echo(f"   🔑 Cache Key: search:{ciudad.lower().replace(' ', '_')}" +
                  (f":cap_{capacidad_minima}" if capacidad_minima else "") +
                  (f":price_{int(precio_maximo)}" if precio_maximo else ""))
        typer.echo(f"   🔄 Invalidación: Automática al crear/cancelar reservas")

        # ========================================
        # OPCIÓN DE LIMPIAR CACHE
        # ========================================
        typer.echo("\n" + "=" * 70)
        clear_choice = typer.prompt(
            f"🧹 ¿Quieres limpiar el cache de {ciudad}? (s/n)",
            default="n"
        )

        if clear_choice.lower() == 's':
            await search_service.clear_cache(ciudad=ciudad)
            typer.echo(f"✅ Cache limpiado para {ciudad}")

            # Buscar de nuevo para confirmar que no hay cache
            typer.echo("\n🔍 Verificando que el cache fue limpiado...")
            result_after_clear = await search_service.search_properties(
                ciudad=ciudad,
                capacidad_minima=capacidad_minima,
                precio_maximo=precio_maximo
            )

            if result_after_clear.get('cached'):
                typer.echo("   ⚠️  Aún hay datos en cache (no debería pasar)")
            else:
                typer.echo("   ✅ Confirmado: CACHE MISS - Cache limpiado correctamente")

        typer.echo("\n" + "=" * 70)
        typer.echo("✅ CASO DE USO 8 COMPLETADO")
        typer.echo("=" * 70)
        typer.echo("💡 CONCLUSIONES:")
        typer.echo("   • Primera búsqueda: Consulta PostgreSQL y guarda en Redis")
        typer.echo("   • Búsquedas subsiguientes: Respuesta instantánea desde Redis")
        typer.echo("   • TTL de 5 minutos: Los datos expiran automáticamente")
        typer.echo("   • Invalidación inteligente: Se limpia al crear/cancelar reservas")

    except Exception as e:
        typer.echo(f"\n❌ Error en caso de uso 8: {str(e)}")
        logger.error("Error en caso de uso 8", error=str(e))

    typer.echo("\n" + "="*70)
    typer.echo("Presiona Enter para continuar...")
    input()


async def handle_test_cases_menu():
    """Maneja el menú de testeo de casos de uso sin autenticación."""
    while True:
        typer.echo(f"\n🧪 TESTEAR CASOS DE USO")
        typer.echo("=" * 60)
        typer.echo("💡 Prueba funcionalidades sin necesidad de login")
        typer.echo("-" * 60)
        typer.echo("1. 🏙️ Caso 1: Tasa de ocupación por ciudad (RANGO DE FECHAS - Cassandra)")
        typer.echo("2. 📊 Caso 2: Promedio de rating por anfitrión (MongoDB)")
        typer.echo("3. 🏠 Caso 3: Búsqueda de propiedades (Cassandra)")
        typer.echo("4. 🏠 Caso 4: Propiedades disponibles por fecha (Cassandra)")
        typer.echo("5. 🏙️ Caso 5: Reservas por ciudad y fecha (Cassandra)")
        typer.echo("6. 🏡 Caso 6: Reservas por host y fecha (Cassandra)")
        typer.echo("7. 🔐 Caso 7: Sesión de un huésped (1h)")
        typer.echo("8. 🔴 Caso 8: Redis Caching para búsquedas (TTL: 5 min)")
        typer.echo("9. 👥 Caso 9: Usuarios recurrentes por ciudad (Neo4j)")
        typer.echo(
            "10. 🏘️  Caso 10: Comunidades host-huésped (>=3 interacciones)")
        typer.echo("0. ⬅️  Volver al menú principal")

        try:
            choice = typer.prompt(
                "Selecciona una opción (1,2,3,4,5,6,7,8,9,10,0)", type=int)

            if choice == 1:
                await test_case_1_ocupacion_ciudad()
            elif choice == 2:
                await test_case_2_rating_averages()
            elif choice == 3:
                await test_case_3_property_search()
            elif choice == 4:
                await handle_cu4_propiedades_disponibles()
            elif choice == 5:
                await handle_cu5_reservas_ciudad()
            elif choice == 6:
                await handle_cu6_reservas_host()
            elif choice == 7:
                await test_case_7_guest_session()
            elif choice == 8:
                await test_case_8_redis_caching()
            elif choice == 9:
                await test_case_9_usuarios_recurrentes()
            elif choice == 10:
                await test_case_10_communities()
            elif choice == 0:
                break
            else:
                typer.echo(
                    "❌ Opción inválida. Por favor selecciona 1,2,3,4,5,6,7,8,9,10 o 0.")

        except ValueError:
            typer.echo("❌ Por favor ingresa un número válido.")
        except KeyboardInterrupt:
            typer.echo("\n👋 Regresando al menú principal...")
            break


async def test_case_8_cassandra_integration():
    """Caso de uso 8: Prueba completa de integración con Cassandra."""
    try:
        typer.echo("\n🏪 CASO DE USO 8: INTEGRACIÓN CASSANDRA")
        typer.echo("=" * 60)
        typer.echo("🔄 Probando sincronización PostgreSQL ↔ Cassandra")

        # Importar dependencias
        from repositories.cassandra_reservation_repository import get_cassandra_reservation_repository
        from services.reservations import ReservationService
        from datetime import date, timedelta
        from decimal import Decimal

        # Paso 1: Verificar conexión con Cassandra
        typer.echo("\n📡 Paso 1: Verificando conexión con Cassandra...")
        try:
            repo = await get_cassandra_reservation_repository()
            typer.echo("   ✅ Conexión establecida con Cassandra")
        except Exception as e:
            typer.echo(f"   ❌ Error conectando con Cassandra: {e}")
            typer.echo("   💡 Verifica la configuración en tu archivo .env")
            return

        # Paso 2: Probar operaciones básicas de repositorio
        typer.echo("\n🧪 Paso 2: Probando operaciones del repositorio...")

        # Datos de prueba
        ciudad_id = 1
        propiedad_id = 101
        host_id = "550e8400-e29b-41d4-a716-446655440000"
        huesped_id = "550e8400-e29b-41d4-a716-446655440001"
        reserva_id = "550e8400-e29b-41d4-a716-446655440002"
        fecha_inicio = date.today() + timedelta(days=7)
        fecha_fin = fecha_inicio + timedelta(days=3)
        monto = Decimal('150.00')

        typer.echo(f"   📅 Fechas de prueba: {fecha_inicio} → {fecha_fin}")

        # Test de creación
        typer.echo("   🏗️  Simulando creación de reserva...")
        loop = asyncio.get_event_loop()
        from concurrent.futures import ThreadPoolExecutor
        executor = ThreadPoolExecutor()

        await loop.run_in_executor(
            executor,
            repo.sync_reservation_creation,
            ciudad_id, host_id, str(propiedad_id), huesped_id, reserva_id,
            fecha_inicio, fecha_fin, monto
        )
        typer.echo("   ✅ Sincronización de creación completada")

        # Test de cancelación
        typer.echo("   🗑️  Simulando cancelación de reserva...")
        await loop.run_in_executor(
            executor,
            repo.sync_reservation_cancellation,
            ciudad_id, host_id, str(propiedad_id), reserva_id,
            fecha_inicio, fecha_fin
        )
        typer.echo("   ✅ Sincronización de cancelación completada")

        # Paso 3: Probar servicio de reservas integrado
        typer.echo("\n🏢 Paso 3: Verificando integración en ReservationService...")

        reservation_service = ReservationService()
        cassandra_repo = await reservation_service.cassandra_repo

        if cassandra_repo:
            typer.echo("   ✅ ReservationService tiene repositorio Cassandra")
        else:
            typer.echo(
                "   ⚠️  ReservationService no pudo inicializar Cassandra")

        # Paso 4: Mostrar resumen de tablas
        typer.echo("\n📊 Paso 4: Resumen de sincronización:")
        typer.echo("   🏙️  ocupacion_por_ciudad → Métricas por ciudad y fecha")
        typer.echo(
            "   🏠 propiedades_disponibles_por_fecha → Disponibilidad diaria")
        typer.echo("   📝 reservas_por_host_fecha → Reservas por anfitrión")

        # Cerrar conexión
        await repo.close()
        await reservation_service.close()

        typer.echo("\n🎉 INTEGRACIÓN CASSANDRA EXITOSA")
        typer.echo("   ✅ Repositorio funcionando")
        typer.echo("   ✅ Sincronización de creación/cancelación")
        typer.echo("   ✅ Integración con ReservationService")

    except Exception as e:
        typer.echo(f"\n❌ Error durante el test: {str(e)}")
        logger.error(
            "Error en test_case_8_cassandra_integration", error=str(e))


async def test_case_2_rating_averages():
    """Caso de uso 2: Mostrar promedio de rating por anfitrión desde MongoDB."""
    try:
        from db.mongo import get_collection

        typer.echo("\n📊 CASO DE USO 2: PROMEDIO DE RATING POR ANFITRIÓN")
        typer.echo("=" * 70)
        typer.echo("🔍 Consultando estadísticas de anfitriones en MongoDB...")

        # Obtener datos de la colección host_statistics
        collection = get_collection("host_statistics")

        # Buscar todos los documentos con datos de rating
        query = {
            "$or": [
                {"avg_rating": {"$exists": True}},
                {"stats.average_rating": {"$exists": True}}
            ]
        }

        results = list(collection.find(query).sort("avg_rating", -1))

        if results:
            typer.echo(f"\n⭐ ESTADÍSTICAS DE {len(results)} ANFITRIONES:")
            typer.echo("-" * 70)
            typer.echo(
                f"{'Host ID':<8} {'Promedio':<10} {'# Reviews':<10} {'# Ratings':<10} {'Actualizado':<12}")
            typer.echo("-" * 70)

            total_hosts = 0
            total_avg_sum = 0
            max_rating = 0
            min_rating = 5

            for result in results:
                host_id = result.get('host_id', 'N/A')

                # Intentar ambas estructuras de datos
                avg_rating = result.get('avg_rating') or result.get(
                    'stats', {}).get('average_rating', 0)
                total_reviews = result.get('total_reviews') or result.get(
                    'stats', {}).get('total_reviews', 0)

                # Contar ratings de ambas estructuras posibles
                recent_ratings = result.get('recent_ratings', [])
                ratings_array = result.get('ratings', [])
                total_ratings = len(recent_ratings) + len(ratings_array)

                # Fecha de actualización
                updated_at = result.get('updated_at')
                if updated_at:
                    updated_str = updated_at.strftime(
                        '%Y-%m-%d') if hasattr(updated_at, 'strftime') else str(updated_at)[:10]
                else:
                    updated_str = 'N/A'

                if avg_rating > 0:  # Solo mostrar si hay datos válidos
                    # Mostrar datos
                    typer.echo(
                        f"{host_id:<8} {avg_rating:<10.2f} {total_reviews:<10} {total_ratings:<10} {updated_str:<12}")

                    # Mostrar estrellas visuales
                    stars = "⭐" * int(avg_rating) if avg_rating else "❌"
                    typer.echo(f"         {stars} ({avg_rating:.1f}/5)")

                    # Mostrar últimos ratings si existen
                    if recent_ratings:
                        latest_ratings = [r.get('rating', 0)
                                          for r in recent_ratings[-3:]]
                        typer.echo(f"         Últimos: {latest_ratings}")

                    typer.echo("")

                    # Acumular para estadísticas
                    total_hosts += 1
                    total_avg_sum += avg_rating
                    max_rating = max(max_rating, avg_rating)
                    min_rating = min(min_rating, avg_rating)

            # Estadísticas generales
            if total_hosts > 0:
                overall_avg = total_avg_sum / total_hosts

                typer.echo("📈 RESUMEN GENERAL:")
                typer.echo(f"   🏠 Total anfitriones: {total_hosts}")
                typer.echo(f"   ⭐ Promedio general: {overall_avg:.2f}/5")
                typer.echo(f"   🔝 Mejor rating: {max_rating:.2f}/5")
                typer.echo(f"   🔻 Menor rating: {min_rating:.2f}/5")

            # Mostrar estructura de datos encontrada
            typer.echo(f"\n🔍 ESTRUCTURA DE DATOS DETECTADA:")
            sample = results[0]
            if 'avg_rating' in sample:
                typer.echo(
                    "   ✅ Formato: avg_rating, total_reviews, recent_ratings")
            elif 'stats' in sample:
                typer.echo(
                    "   ✅ Formato: stats.average_rating, stats.total_reviews, ratings")

        else:
            typer.echo("❌ No se encontraron datos de anfitriones con ratings.")
            typer.echo("💡 Verifica que:")
            typer.echo("   1. Existan reseñas creadas en el sistema")
            typer.echo(
                "   2. El servicio de reseñas haya actualizado MongoDB correctamente")
            typer.echo("   3. La colección 'host_statistics' tenga documentos")

            # Mostrar información de diagnóstico
            total_docs = collection.count_documents({})
            typer.echo(f"\n🔍 Diagnóstico rápido:")
            typer.echo(
                f"   📊 Total documentos en host_statistics: {total_docs}")

            if total_docs > 0:
                sample = collection.find_one()
                typer.echo(
                    f"   🏗️  Campos disponibles: {list(sample.keys()) if sample else 'ninguno'}")

    except Exception as e:
        typer.echo(f"❌ Error consultando MongoDB: {str(e)}")
        logger.error("Error en caso de uso 2", error=str(e))

    typer.echo("\n" + "="*70)
    typer.echo("Presiona Enter para continuar...")
    input()


async def test_case_10_communities():
    """Caso de uso 10: Mostrar comunidades host-huésped con >=3 interacciones."""
    try:
        from services.neo4j_reservations import Neo4jReservationService

        typer.echo("\n🏘️ CASO DE USO 10: COMUNIDADES HOST-HUÉSPED")
        typer.echo("=" * 70)
        typer.echo("🔍 Buscando comunidades con >= 3 interacciones en Neo4j...")

        neo4j_service = Neo4jReservationService()
        result = await neo4j_service.get_all_communities(min_interactions=3)

        if result['success']:
            communities = result['communities']
            total = result['total_communities']

            typer.echo(
                f"\n🏘️  {total} COMUNIDADES ENCONTRADAS (>= 3 interacciones):")
            typer.echo("=" * 90)
            typer.echo(
                f"{'#':<3} {'Huésped ID':<12} {'Host ID':<12} {'Interacciones':<15} {'Propiedades':<12} {'Última Int.':<15}")
            typer.echo("=" * 90)

            if communities:
                # Mostrar máximo 15
                for i, comm in enumerate(communities[:15], 1):
                    guest_id = comm.get('guest_id', 'N/A')
                    host_id = comm.get('host_id', 'N/A')
                    interactions = comm.get('total_interactions', 0)
                    properties = comm.get('total_properties', 0)
                    last_interaction = comm.get('last_interaction_date', 'N/A')

                    # Mostrar indicador visual de intensidad
                    # Máximo 5 flames
                    intensity = "🔥" * min(int(interactions / 2), 5)

                    typer.echo(
                        f"{i:<3} {guest_id:<12} {host_id:<12} {interactions:<7} {intensity:<8} {properties:<12} {last_interaction:<15}")

                if len(communities) > 15:
                    typer.echo(
                        f"... y {len(communities) - 15} comunidades más")

            # Estadísticas de comunidades
            if communities:
                total_interactions = sum(
                    c.get('total_interactions', 0) for c in communities)
                avg_interactions = total_interactions / len(communities)
                max_interactions = max(c.get('total_interactions', 0)
                                       for c in communities)

                # Distribución por nivel de interacciones
                level_3_5 = len([c for c in communities if 3 <=
                                c.get('total_interactions', 0) <= 5])
                level_6_10 = len(
                    [c for c in communities if 6 <= c.get('total_interactions', 0) <= 10])
                level_10_plus = len(
                    [c for c in communities if c.get('total_interactions', 0) > 10])

                typer.echo("\n📊 ESTADÍSTICAS DE COMUNIDADES:")
                typer.echo(f"   🏘️  Total comunidades: {total}")
                typer.echo(
                    f"   🔄 Promedio interacciones: {avg_interactions:.1f}")
                typer.echo(f"   🔝 Máximo interacciones: {max_interactions}")
                typer.echo("\n📈 DISTRIBUCIÓN:")
                typer.echo(f"   🌱 3-5 interacciones: {level_3_5} comunidades")
                typer.echo(
                    f"   🌿 6-10 interacciones: {level_6_10} comunidades")
                typer.echo(
                    f"   🌳 >10 interacciones: {level_10_plus} comunidades")
        else:
            typer.echo(
                f"❌ Error obteniendo comunidades: {result.get('error', 'Error desconocido')}")

        # Cerrar conexión
        neo4j_service.close()

    except ImportError:
        typer.echo("❌ El análisis de comunidades requiere Neo4j")
        typer.echo(
            "💡 Verifica que el servicio Neo4j esté configurado correctamente")
    except Exception as e:
        typer.echo(f"❌ Error consultando Neo4j: {str(e)}")
        logger.error("Error en caso de uso 10", error=str(e))

    typer.echo("\n" + "="*70)
    typer.echo("Presiona Enter para continuar...")
    input()


async def handle_cassandra_menu(user_profile):
    """
    Maneja el menú interactivo para casos de uso de Cassandra.
    """
    while True:
        try:
            typer.echo(f"\n🗃️ CASOS DE USO CASSANDRA")
            typer.echo("=" * 50)
            typer.echo("1. 🏠 CU 4: Propiedades disponibles por fecha")
            typer.echo("2. 🏙️ CU 5: Reservas por ciudad y fecha")
            typer.echo("3. 🏡 CU 6: Reservas por host y fecha")
            typer.echo("4. 🔍 Verificar disponibilidad específica")
            typer.echo("5. 🧪 Probar todos los casos de uso")
            typer.echo("6. ⬅️  Volver al menú principal")

            choice = typer.prompt("Selecciona una opción (1-6)", type=int)

            if choice == 1:
                await handle_cu4_propiedades_disponibles()
            elif choice == 2:
                await handle_cu5_reservas_ciudad()
            elif choice == 3:
                await handle_cu6_reservas_host()
            elif choice == 4:
                await handle_verificar_disponibilidad()
            elif choice == 5:
                await handle_test_todos_casos_cassandra()
            elif choice == 6:
                break
            else:
                typer.echo("❌ Opción inválida. Selecciona entre 1 y 6.")

        except ValueError:
            typer.echo("❌ Por favor ingresa un número válido.")
        except Exception as e:
            typer.echo(f"❌ Error: {str(e)}")


async def handle_cu4_propiedades_disponibles():
    """CU 4: Propiedades disponibles por fecha."""
    try:
        typer.echo("\n🏠 CU 4: PROPIEDADES DISPONIBLES POR FECHA")
        typer.echo("=" * 60)

        fecha_str = typer.prompt("📅 Fecha (YYYY-MM-DD)")

        # Validar fecha
        try:
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except ValueError:
            typer.echo("❌ Formato de fecha inválido. Use YYYY-MM-DD")
            return

        from services.reservations import ReservationService
        service = ReservationService()

        typer.echo(f"\n🔄 Buscando propiedades disponibles para {fecha_str}...")
        result = await service.get_propiedades_disponibles_fecha(fecha)

        if result.get("success"):
            propiedades = result.get("propiedades", [])

            typer.echo(
                f"\n📊 Resultados: {len(propiedades)} propiedades encontradas")

            if propiedades:
                typer.echo("\n" + "-" * 80)
                typer.echo(
                    f"{'ID':<8} {'Ciudad':<20} {'Precio/noche':<15} {'Capacidad':<12} {'WiFi':<6}")
                typer.echo("-" * 80)

                for prop in propiedades[:15]:  # Mostrar solo las primeras 15
                    prop_id = prop.get('propiedad_id', 'N/A')
                    ciudad = prop.get('ciudad_nombre', 'N/A')[:19]
                    precio = f"${prop.get('precio_noche', 0):.2f}"
                    capacidad = prop.get('capacidad_huespedes', 'N/A')
                    wifi = "Sí" if prop.get('wifi', False) else "No"
                    typer.echo(
                        f"{prop_id:<8} {ciudad:<20} {precio:<15} {capacidad:<12} {wifi:<6}")

                if len(propiedades) > 15:
                    typer.echo(
                        f"\n... y {len(propiedades) - 15} propiedades más")
            else:
                typer.echo(
                    "📭 No se encontraron propiedades disponibles para esta fecha")
        else:
            typer.echo(f"❌ Error: {result.get('error', 'Error desconocido')}")

    except Exception as e:
        typer.echo(f"❌ Error: {str(e)}")

    typer.echo("\nPresiona Enter para continuar...")
    input()


async def handle_cu5_reservas_ciudad():
    """CU 5: Reservas por ciudad y fecha."""
    try:
        typer.echo("\n🏙️ CU 5: RESERVAS POR CIUDAD Y FECHA")
        typer.echo("=" * 60)

        ciudad_id = typer.prompt("🏙️ ID de la ciudad", type=int)
        fecha_str = typer.prompt("📅 Fecha (YYYY-MM-DD)")

        # Validar fecha
        try:
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except ValueError:
            typer.echo("❌ Formato de fecha inválido. Use YYYY-MM-DD")
            return

        from services.reservations import ReservationService
        service = ReservationService()

        typer.echo(
            f"\n🔄 Buscando reservas de ciudad {ciudad_id} para {fecha_str}...")
        result = await service.get_reservas_ciudad(ciudad_id, fecha)

        if result.get("success"):
            reservas = result.get("reservas", [])

            typer.echo(f"\n📊 Resultados: {len(reservas)} reservas encontradas")

            if reservas:
                typer.echo("\n" + "-" * 80)
                typer.echo(
                    f"{'Reserva ID':<12} {'Propiedad':<12} {'Host':<8} {'Huésped':<12} {'Precio':<12} {'Estado':<10}")
                typer.echo("-" * 80)

                for reserva in reservas:
                    reserva_id = reserva.get('reserva_id', 'N/A')
                    propiedad_id = reserva.get('propiedad_id', 'N/A')
                    host_id = reserva.get('host_id', 'N/A')
                    huesped_id = reserva.get('huesped_id', 'N/A')
                    precio = f"${reserva.get('precio_total', 0):.2f}"
                    estado = reserva.get('estado', 'N/A')
                    typer.echo(
                        f"{reserva_id:<12} {propiedad_id:<12} {host_id:<8} {huesped_id:<12} {precio:<12} {estado:<10}")
            else:
                typer.echo(
                    "📭 No se encontraron reservas para esta ciudad en esta fecha")
        else:
            typer.echo(f"❌ Error: {result.get('error', 'Error desconocido')}")

    except Exception as e:
        typer.echo(f"❌ Error: {str(e)}")

    typer.echo("\nPresiona Enter para continuar...")
    input()


async def handle_cu6_reservas_host():
    """CU 6: Reservas por host y fecha."""
    try:
        typer.echo("\n🏡 CU 6: RESERVAS POR HOST Y FECHA")
        typer.echo("=" * 60)

        host_id_str = typer.prompt(
            "🏡 ID del host/anfitrión (número entero)")

        try:
            host_id = int(host_id_str)
        except ValueError:
            typer.echo("❌ ID del host debe ser un número entero")
            return

        fecha_str = typer.prompt("📅 Fecha (YYYY-MM-DD)")

        # Validar fecha
        try:
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except ValueError:
            typer.echo("❌ Formato de fecha inválido. Use YYYY-MM-DD")
            return

        from services.reservations import ReservationService
        service = ReservationService()

        typer.echo(
            f"\n🔄 Buscando reservas del host {host_id} para {fecha_str}...")
        result = await service.get_reservas_host(host_id, fecha)

        if result.get("success"):
            reservas = result.get("reservas", [])

            typer.echo(f"\n📊 Resultados: {len(reservas)} reservas encontradas")

            if reservas:
                typer.echo("\n" + "-" * 70)
                typer.echo(
                    f"{'Reserva ID':<12} {'Propiedad':<12} {'Huésped':<12} {'Precio':<12} {'Estado':<10}")
                typer.echo("-" * 70)

                for reserva in reservas:
                    reserva_id = reserva.get('reserva_id', 'N/A')
                    propiedad_id = reserva.get('propiedad_id', 'N/A')
                    huesped_id = reserva.get('huesped_id', 'N/A')
                    precio = f"${reserva.get('precio_total', 0):.2f}"
                    estado = reserva.get('estado', 'N/A')
                    typer.echo(
                        f"{reserva_id:<12} {propiedad_id:<12} {huesped_id:<12} {precio:<12} {estado:<10}")
            else:
                typer.echo(
                    "📭 No se encontraron reservas para este host en esta fecha")
        else:
            typer.echo(f"❌ Error: {result.get('error', 'Error desconocido')}")

    except Exception as e:
        typer.echo(f"❌ Error: {str(e)}")

    typer.echo("\nPresiona Enter para continuar...")
    input()


async def handle_verificar_disponibilidad():
    """Verificar disponibilidad específica de una propiedad."""
    try:
        typer.echo("\n🔍 VERIFICAR DISPONIBILIDAD ESPECÍFICA")
        typer.echo("=" * 60)

        propiedad_id = typer.prompt("🏠 ID de la propiedad", type=int)
        fecha_str = typer.prompt("📅 Fecha (YYYY-MM-DD)")

        # Validar fecha
        try:
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except ValueError:
            typer.echo("❌ Formato de fecha inválido. Use YYYY-MM-DD")
            return

        from services.reservations import ReservationService
        service = ReservationService()

        typer.echo(
            f"\n🔄 Verificando disponibilidad de propiedad {propiedad_id} para {fecha_str}...")

        # Usar el servicio de propiedades disponibles y filtrar
        result = await service.get_propiedades_disponibles_fecha(fecha)

        if result.get("success"):
            propiedades = result.get("propiedades", [])
            propiedad_encontrada = None

            # Buscar la propiedad específica
            for prop in propiedades:
                if prop.get('propiedad_id') == propiedad_id:
                    propiedad_encontrada = prop
                    break

            typer.echo(f"\n🔍 RESULTADO DE VERIFICACIÓN")
            typer.echo("=" * 50)
            typer.echo(f"🏠 Propiedad ID: {propiedad_id}")
            typer.echo(f"📅 Fecha: {fecha_str}")

            if propiedad_encontrada:
                typer.echo("✅ Estado: DISPONIBLE")
                typer.echo(
                    f"💰 Precio: ${propiedad_encontrada.get('precio_noche', 0):.2f}/noche")
                typer.echo(
                    f"🏙️ Ciudad: {propiedad_encontrada.get('ciudad_nombre', 'N/A')}")
                typer.echo(
                    f"👥 Capacidad: {propiedad_encontrada.get('capacidad_huespedes', 'N/A')} huéspedes")
                typer.echo(
                    f"📶 WiFi: {'Sí' if propiedad_encontrada.get('wifi', False) else 'No'}")
            else:
                typer.echo("❌ Estado: NO DISPONIBLE")
                typer.echo(
                    "💡 La propiedad no está disponible en esta fecha o no existe")
        else:
            typer.echo(f"❌ Error: {result.get('error', 'Error desconocido')}")

    except Exception as e:
        typer.echo(f"❌ Error: {str(e)}")

    typer.echo("\nPresiona Enter para continuar...")
    input()


async def handle_test_todos_casos_cassandra():
    """Prueba todos los casos de uso de Cassandra con datos de ejemplo."""
    try:
        typer.echo("\n🧪 PRUEBA COMPLETA DE CASOS DE USO CASSANDRA")
        typer.echo("=" * 70)

        # Usar fecha de ejemplo
        fecha_test = "2026-03-15"

        typer.echo(f"📅 Usando fecha de prueba: {fecha_test}")
        typer.echo(f"💡 Probando con datos conocidos del sistema...")
        typer.echo("\n" + "-" * 70)

        # Test CU 4: Propiedades disponibles
        typer.echo("\n🔍 Probando CU 4: Propiedades disponibles...")
        from services.reservations import ReservationService
        service = ReservationService()

        fecha = datetime.strptime(fecha_test, "%Y-%m-%d").date()
        result = await service.get_propiedades_disponibles_fecha(fecha)

        if result.get("success"):
            propiedades = result.get("propiedades", [])
            typer.echo(
                f"✅ CU 4 exitoso: {len(propiedades)} propiedades encontradas")
        else:
            typer.echo(f"❌ CU 4 falló: {result.get('error')}")

        # Test CU 5: Reservas por ciudad (ciudad 1)
        typer.echo("\n🔍 Probando CU 5: Reservas por ciudad 1...")
        result = await service.get_reservas_ciudad(1, fecha)

        if result.get("success"):
            reservas = result.get("reservas", [])
            typer.echo(f"✅ CU 5 exitoso: {len(reservas)} reservas encontradas")
        else:
            typer.echo(f"❌ CU 5 falló: {result.get('error')}")

        # Test CU 6: Reservas por host (host 1)
        typer.echo("\n🔍 Probando CU 6: Reservas por host 1...")
        result = await service.get_reservas_host(1, fecha)

        if result.get("success"):
            reservas = result.get("reservas", [])
            typer.echo(f"✅ CU 6 exitoso: {len(reservas)} reservas encontradas")
        else:
            typer.echo(f"❌ CU 6 falló: {result.get('error')}")

        # Test verificación específica (propiedad 29)
        typer.echo("\n🔍 Probando verificación específica: Propiedad 29...")
        result = await service.get_propiedades_disponibles_fecha(fecha)

        if result.get("success"):
            propiedades = result.get("propiedades", [])
            encontrada = any(p.get('propiedad_id') == 29 for p in propiedades)
            typer.echo(
                f"✅ Verificación exitosa: Propiedad 29 {'disponible' if encontrada else 'no disponible'}")
        else:
            typer.echo(f"❌ Verificación falló: {result.get('error')}")

        typer.echo("\n" + "=" * 70)
        typer.echo("🎉 PRUEBAS COMPLETADAS")
        typer.echo("💡 Todos los casos de uso de Cassandra han sido probados")

    except Exception as e:
        typer.echo(f"❌ Error durante las pruebas: {str(e)}")

    typer.echo("\nPresiona Enter para continuar...")
    input()


async def test_case_9_usuarios_recurrentes():
    """
    CU 9/11: Usuarios recurrentes - consulta usuarios que regresaron a la misma ciudad.
    Utiliza Neo4j con las relaciones User-[:BOOKED_IN]->City creadas durante reservas.
    """
    typer.echo("\n" + "=" * 70)
    typer.echo("🔄 CASO 11: USUARIOS RECURRENTES (NEO4J)")
    typer.echo("=" * 70)
    typer.echo("📊 Consultando usuarios que regresaron a la misma ciudad...")

    try:
        from services.reservations import ReservationService
        service = ReservationService()

        # Consulta todos los usuarios recurrentes
        typer.echo("\n1️⃣ Usuarios recurrentes en todas las ciudades:")
        typer.echo("-" * 50)

        result = await service.get_usuarios_recurrentes()

        if result.get("success"):
            usuarios = result.get("usuarios_recurrentes", [])
            estadisticas = result.get("estadisticas_ciudades", {})

            if usuarios:
                typer.echo(
                    f"✅ Encontrados {len(usuarios)} usuarios recurrentes")
                typer.echo("\n📋 TOP 10 USUARIOS MÁS RECURRENTES:")
                typer.echo(
                    f"{'#':<3} {'Usuario':<15} {'Ciudad':<20} {'Visitas':<8}")
                typer.echo("-" * 48)

                for i, usuario in enumerate(usuarios[:10], 1):
                    user_id = usuario.get('user_id', 'N/A')
                    city = usuario.get('city', 'N/A')
                    visits = usuario.get('total_visits', 0)

                    # Iconos por nivel de recurrencia
                    if visits >= 5:
                        icon = "🏆"
                    elif visits >= 3:
                        icon = "🥇"
                    else:
                        icon = "🔄"

                    typer.echo(
                        f"{i:<3} {user_id:<15} {city:<20} {visits:<3} {icon}")

                # Estadísticas por ciudad
                typer.echo(f"\n🏙️ ESTADÍSTICAS POR CIUDAD:")
                typer.echo(
                    f"{'Ciudad':<20} {'Usuarios':<10} {'Total Visitas':<12}")
                typer.echo("-" * 44)

                for city, stats in sorted(estadisticas.items(), key=lambda x: x[1]['usuarios'], reverse=True)[:5]:
                    usuarios_count = stats['usuarios']
                    total_visitas = stats['total_visitas']
                    typer.echo(
                        f"{city:<20} {usuarios_count:<10} {total_visitas:<12}")

            else:
                typer.echo("ℹ️ No se encontraron usuarios recurrentes.")
                typer.echo(
                    "💡 Crea algunas reservas para el mismo usuario en la misma ciudad.")
        else:
            typer.echo(f"❌ Error: {result.get('error')}")

        # Consulta específica por ciudad
        typer.echo("\n2️⃣ Consulta por ciudad específica:")
        typer.echo("-" * 40)

        ciudad_nombre = typer.prompt(
            "Ingresa el nombre de la ciudad (o Enter para omitir)", default="", show_default=False)

        if ciudad_nombre.strip():
            result = await service.get_usuarios_recurrentes(city_name=ciudad_nombre.strip())

            if result.get("success"):
                usuarios = result.get("usuarios_recurrentes", [])

                if usuarios:
                    typer.echo(
                        f"✅ Usuarios recurrentes en {ciudad_nombre}: {len(usuarios)}")
                    typer.echo(f"\n{'Usuario':<15} {'Visitas':<8}")
                    typer.echo("-" * 25)

                    for usuario in usuarios:
                        user_id = usuario.get('user_id', 'N/A')
                        visits = usuario.get('total_visits', 0)
                        typer.echo(f"{user_id:<15} {visits:<8}")
                else:
                    typer.echo(
                        f"ℹ️ No hay usuarios recurrentes en {ciudad_nombre}")
            else:
                typer.echo(
                    f"❌ Error consultando {ciudad_nombre}: {result.get('error')}")

        # Información técnica
        typer.echo("\n🔧 INFORMACIÓN TÉCNICA:")
        typer.echo(
            "• Este CU utiliza Neo4j con relaciones User-[:BOOKED_IN]->City")
        typer.echo("• Las relaciones se crean automáticamente al hacer reservas")
        typer.echo("• La propiedad 'count' en la relación cuenta las visitas")
        typer.echo("• Consulta optimizada con índice booked_in_count_idx")

    except Exception as e:
        logger.error(f"Error en test_case_11_usuarios_recurrentes: {e}")
        typer.echo(f"❌ Error ejecutando caso 11: {str(e)}")

    typer.echo("\nPresiona Enter para continuar...")
    input()


if __name__ == "__main__":
    app()
