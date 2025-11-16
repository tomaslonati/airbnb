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

# Importar funciones de manejo de sesión
from cli.sessions.state import (
    get_current_user, 
    set_current_user, 
    clear_session, 
    has_active_session,
    get_session_token, 
    set_session_token
)
from cli.sessions.interactive import (
    handle_login,
    handle_logout,
    handle_register,
    show_auth_menu,
    show_main_menu,
    show_user_profile,
    show_active_sessions
)

# Importar módulos CLI de features
# from cli.reservations.commands import handle_reservation_management

# Configurar logging al importar
configure_logging()
logger = get_logger(__name__)

app = typer.Typer(
    name="airbnb-backend",
    help="Backend CLI para sistema tipo Airbnb - Sistema de Autenticación Interactivo"
)

# Integrar sub-apps de features (comentado temporalmente - sistema usa menú interactivo)
# app.add_typer(auth_app, name="auth", help="Comandos de autenticación")
# app.add_typer(properties_app, name="properties", help="Gestión de propiedades")
# app.add_typer(reservations_app, name="reservations", help="Gestión de reservas")


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
                # Hay sesión activa - mostrar menú principal
                action = await show_main_menu(current_user)

                if action == "logout":
                    await handle_logout(auth_service)
                    clear_session()
                elif action == "profile":
                    await show_user_profile(current_user)
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
                elif action == "mongo_stats":
                    await show_mongo_stats(current_user)
                elif action == "exit":
                    typer.echo("👋 ¡Hasta luego!")
                    break

        except KeyboardInterrupt:
            typer.echo("\n👋 ¡Hasta luego!")
            break
        except Exception as e:
            typer.echo(f"❌ Error inesperado: {str(e)}")
            logger.error("Error en modo interactivo", error=str(e))


# async def show_auth_menu():
#     """Muestra el menú de autenticación y retorna la acción seleccionada."""
#     typer.echo("\n🔐 AUTENTICACIÓN")
#     typer.echo("-" * 20)
#     typer.echo("1. 🔑 Iniciar Sesión")
#     typer.echo("2. 📝 Registrarse")
#     typer.echo("3. 🧪 Testear casos de uso")
#     typer.echo("4. ❌ Salir")
#
#     while True:
#         try:
#             choice = typer.prompt("Selecciona una opción (1-4)", type=int)
#             if choice == 1:
#                 return "login"
#             elif choice == 2:
#                 return "register"
#             elif choice == 3:
#                 return "test_cases"
#             elif choice == 4:
#                 return "exit"
#             else:
#                 typer.echo("❌ Opción inválida. Selecciona 1, 2, 3 o 4.")
#         except ValueError:
#             typer.echo("❌ Por favor ingresa un número válido.")


# ===== FUNCIONES DE MENÚ Y AUTENTICACIÓN =====
# Las siguientes funciones están comentadas porque ahora se importan desde cli/sessions/
# para mantener consistencia con la gestión de sesiones

# async def show_main_menu(user_profile):
#     """Muestra el menú principal según el tipo de usuario."""
#     typer.echo(f"\n🏠 MENÚ PRINCIPAL - {user_profile.nombre}")
#     typer.echo(f"👤 Rol: {user_profile.rol}")
#     typer.echo("-" * 40)
#     
#     options = [
#         "👤 Ver mi perfil",
#         "🚪 Cerrar sesión",
#         "❌ Salir del sistema"
#     ]
#     
#     # Agregar opciones específicas por rol
#     if user_profile.rol in ['ANFITRION', 'AMBOS']:
#         options.insert(-2, "🏠 Gestionar mis propiedades")
#         options.insert(-2, "📅 Gestionar disponibilidad de propiedades")
#         options.insert(-2, "📊 Ver estadísticas MongoDB")
#     
#     if user_profile.rol in ['HUESPED', 'AMBOS']:
#         options.insert(-2, "📅 Gestionar mis reservas")
#         options.insert(-2, "⭐ Gestionar mis reseñas")
#     
#     # Opción de análisis de comunidades (para todos los usuarios)
#     options.insert(-2, "🏘️ Análisis de comunidades")
#     
#     for i, option in enumerate(options, 1):
#         typer.echo(f"{i}. {option}")
#     
#     while True:
#         try:
#             choice = typer.prompt(
#                 f"Selecciona una opción (1-{len(options)})", type=int)
#             if 1 <= choice <= len(options):
#                 if "perfil" in options[choice-1]:
#                     return "profile"
#                 elif "Cerrar sesión" in options[choice-1]:
#                     return "logout"
#                 elif "Gestionar mis propiedades" in options[choice-1]:
#                     return "properties"
#                 elif "disponibilidad de propiedades" in options[choice-1]:
#                     return "availability"
#                 elif "Gestionar mis reservas" in options[choice-1]:
#                     return "reservations"
#                 elif "Gestionar mis reseñas" in options[choice-1]:
#                     return "reviews"
#                 elif "estadísticas MongoDB" in options[choice-1]:
#                     return "mongo_stats"
#                 elif "Análisis de comunidades" in options[choice-1]:
#                     return "communities"
#                 elif "Salir" in options[choice-1]:
#                     return "exit"
#             else:
#                 typer.echo(
#                     f"❌ Opción inválida. Selecciona entre 1 y {len(options)}.")
#         except ValueError:
#             typer.echo("❌ Por favor ingresa un número válido.")

# async def handle_login(auth_service):
#     """Maneja el proceso de login interactivo."""
# ... (implementación comentada para usar la de cli/sessions/interactive.py)

# async def handle_register(auth_service):
#     """Maneja el proceso de registro interactivo."""
# ... (implementación comentada para usar la de cli/sessions/interactive.py)

# async def handle_logout(auth_service):
#     """Maneja el cierre de sesión."""
# ... (implementación comentada para usar la de cli/sessions/interactive.py)

# async def show_user_profile(user_profile):
#     """Muestra el perfil completo del usuario."""
# ... (implementación comentada para usar la de cli/sessions/interactive.py)
# ... (implementación comentada para usar la de cli/sessions/interactive.py)

# async def handle_register(auth_service):
#     """Maneja el proceso de registro interactivo."""
# ... (implementación comentada para usar la de cli/sessions/interactive.py)

# async def handle_logout(auth_service):
#     """Maneja el cierre de sesión."""
# ... (implementación comentada para usar la de cli/sessions/interactive.py)

# async def show_user_profile(user_profile):
#     """Muestra el perfil completo del usuario."""
# ... (implementación comentada para usar la de cli/sessions/interactive.py)


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
        typer.echo("6. ↩️  Volver al menú principal")

        try:
            choice = typer.prompt("Selecciona una opción (1-6)", type=int)

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
                break
            else:
                typer.echo("❌ Opción inválida. Selecciona entre 1 y 6.")

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


async def handle_property_management(user_profile):
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
        typer.echo(f"👤 Anfitrión: {user_profile.nombre} (ID: {user_profile.anfitrion_id})")
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


async def create_property_interactive(property_service, anfitrion_id):
    """Crea una propiedad de forma interactiva."""
    typer.echo("\n➕ CREAR NUEVA PROPIEDAD")
    typer.echo("=" * 50)
    
    try:
        nombre = typer.prompt("📝 Nombre de la propiedad")
        descripcion = typer.prompt("📄 Descripción")
        capacidad = typer.prompt("👥 Capacidad (personas)", type=int)
        ciudad_id = typer.prompt("🏙️  ID de la ciudad", type=int)
        tipo_propiedad_id = typer.prompt("🏠 ID del tipo de propiedad", type=int, default=1)
        
        # Amenities opcionales
        amenities_input = typer.prompt("✨ IDs de amenities (separados por coma, Enter para omitir)", default="")
        amenity_ids = None
        if amenities_input:
            amenity_ids = [int(x.strip()) for x in amenities_input.split(",") if x.strip()]
        
        # Servicios opcionales
        servicios_input = typer.prompt("🔧 IDs de servicios (separados por coma, Enter para omitir)", default="")
        servicio_ids = None
        if servicios_input:
            servicio_ids = [int(x.strip()) for x in servicios_input.split(",") if x.strip()]
        
        # Reglas opcionales
        reglas_input = typer.prompt("📜 IDs de reglas (separados por coma, Enter para omitir)", default="")
        regla_ids = None
        if reglas_input:
            regla_ids = [int(x.strip()) for x in reglas_input.split(",") if x.strip()]
        
        typer.echo("\n🔄 Creando propiedad...")
        
        result = await property_service.create_property(
            nombre=nombre,
            descripcion=descripcion,
            capacidad=capacidad,
            ciudad_id=ciudad_id,
            anfitrion_id=anfitrion_id,
            tipo_propiedad_id=tipo_propiedad_id,
            amenities=amenity_ids,
            servicios=servicio_ids,
            reglas=regla_ids,
            generar_calendario=True,
            dias_calendario=365
        )
        
        if result.get("success"):
            typer.echo(f"\n✅ {result.get('message')}")
            typer.echo(f"🆔 ID de la propiedad: {result.get('property_id')}")
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
        descripcion = typer.prompt(f"📄 Nueva descripción [{prop.get('descripcion', 'N/A')}]", default="")
        capacidad_input = typer.prompt(f"👥 Nueva capacidad [{prop['capacidad']}]", default="")
        
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
        propiedad_id = typer.prompt("🆔 ID de la propiedad a eliminar", type=int)
        
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


# ============ COMANDOS DE PROPIEDADES ============

@app.command()
def create_property(
    nombre: str = typer.Argument(...),
    descripcion: str = typer.Argument(...),
    capacidad: int = typer.Argument(...),
    ciudad_id: int = typer.Option(..., "--ciudad-id", "-c"),
    anfitrion_id: int = typer.Option(..., "--anfitrion-id", "-a"),
    tipo_propiedad_id: int = typer.Option(1, "--tipo-id", "-t"),
    amenities: Optional[str] = typer.Option(None, "--amenities", "-am"),
    servicios: Optional[str] = typer.Option(None, "--servicios", "-s"),
    reglas: Optional[str] = typer.Option(None, "--reglas", "-r"),
):
    """Crea una nueva propiedad con amenities, servicios y reglas."""
    from services.properties import PropertyService

    async def _create():
        service = PropertyService()

        # Parsear las listas de IDs
        amenity_ids = None
        if amenities:
            try:
                amenity_ids = [int(x.strip()) for x in amenities.split(",")]
            except ValueError:
                typer.echo(
                    "❌ Error: Amenities debe ser una lista de números separados por comas (ej: 1,2,3)")
                return

        servicio_ids = None
        if servicios:
            try:
                servicio_ids = [int(x.strip()) for x in servicios.split(",")]
            except ValueError:
                typer.echo(
                    "❌ Error: Servicios debe ser una lista de números separados por comas (ej: 1,2)")
                return

        regla_ids = None
        if reglas:
            try:
                regla_ids = [int(x.strip()) for x in reglas.split(",")]
            except ValueError:
                typer.echo(
                    "❌ Error: Reglas debe ser una lista de números separados por comas (ej: 1,2)")
                return

        result = await service.create_property(
            nombre=nombre,
            descripcion=descripcion,
            capacidad=capacidad,
            ciudad_id=ciudad_id,
            anfitrion_id=anfitrion_id,
            tipo_propiedad_id=tipo_propiedad_id,
            amenities=amenity_ids,
            servicios=servicio_ids,
            reglas=regla_ids,
            generar_calendario=True,
            dias_calendario=365
        )

        if result["success"]:
            typer.echo(f"✅ {result['message']}")
            typer.echo(f"   ID de la propiedad: {result['property_id']}")
            typer.echo(f"   Nombre: {result['property']['nombre']}")
            typer.echo(
                f"   Capacidad: {result['property']['capacidad']} personas")
        else:
            typer.echo(f"❌ Error: {result['error']}")

    asyncio.run(_create())


@app.command()
def list_properties(
    ciudad_id: Optional[int] = typer.Option(
        None, "--ciudad-id", "-c", help="Filtrar por ciudad"),
    anfitrion_id: Optional[int] = typer.Option(
        None, "--anfitrion-id", "-a", help="Filtrar por anfitrión"),
):
    """Lista propiedades disponibles."""
    from services.properties import PropertyService

    async def _list():
        service = PropertyService()

        if ciudad_id:
            result = await service.list_properties_by_city(ciudad_id)
        elif anfitrion_id:
            result = await service.list_properties_by_host(anfitrion_id)
        else:
            typer.echo("❌ Debes especificar --ciudad-id o --anfitrion-id")
            return

        if result["success"]:
            typer.echo(f"📍 Total de propiedades: {result['total']}")
            for prop in result["properties"]:
                typer.echo(f"\n  🏠 {prop['nombre']}")
                typer.echo(f"     ID: {prop['id']}")
                typer.echo(f"     Capacidad: {prop['capacidad']} personas")
                typer.echo(f"     Ciudad: {prop.get('ciudad', 'N/A')}")
                typer.echo(f"     Tipo: {prop.get('tipo_propiedad', 'N/A')}")
        else:
            typer.echo(f"❌ Error: {result['error']}")

    asyncio.run(_list())


@app.command()
def get_property(
    propiedad_id: int = typer.Argument(...),
):
    """Obtiene los detalles de una propiedad."""
    from services.properties import PropertyService

    async def _get():
        service = PropertyService()
        result = await service.get_property(propiedad_id)

        if result["success"]:
            prop = result["property"]
            typer.echo(f"🏠 {prop['nombre']}")
            typer.echo(f"   ID: {prop['id']}")
            typer.echo(f"   Descripción: {prop.get('descripcion', 'N/A')}")
            typer.echo(f"   Capacidad: {prop['capacidad']} personas")
            typer.echo(f"   Ciudad: {prop.get('ciudad', 'N/A')}")
            typer.echo(f"   Tipo: {prop.get('tipo_propiedad', 'N/A')}")
        else:
            typer.echo(f"❌ Error: {result['error']}")

    asyncio.run(_get())


@app.command()
def update_property(
    propiedad_id: int = typer.Argument(...),
    nombre: Optional[str] = typer.Option(None, "--nombre", "-n"),
    descripcion: Optional[str] = typer.Option(None, "--descripcion", "-d"),
    capacidad: Optional[int] = typer.Option(None, "--capacidad", "-c"),
    tipo_propiedad_id: Optional[int] = typer.Option(None, "--tipo", "-t"),
):
    """Actualiza los datos de una propiedad."""
    from services.properties import PropertyService

    async def _update():
        service = PropertyService()
        result = await service.update_property(
            propiedad_id,
            nombre=nombre,
            descripcion=descripcion,
            capacidad=capacidad,
            tipo_propiedad_id=tipo_propiedad_id
        )

        if result["success"]:
            typer.echo(f"✅ {result['message']}")
            prop = result["property"]
            typer.echo(f"   ID: {prop['id']}")
            typer.echo(f"   Nombre: {prop['nombre']}")
            typer.echo(f"   Capacidad: {prop['capacidad']} personas")
        else:
            typer.echo(f"❌ Error: {result['error']}")

    asyncio.run(_update())


@app.command()
def delete_property(
    propiedad_id: int = typer.Argument(...),
    confirm: bool = typer.Option(False, "--confirm", "-y"),
):
    """Elimina una propiedad y todas sus relaciones."""
    from services.properties import PropertyService

    async def _delete():
        if not confirm:
            typer.echo(
                f"⚠️  Esta acción eliminará la propiedad {propiedad_id} y todos sus datos asociados.")
            if not typer.confirm("¿Estás seguro de que quieres continuar?"):
                typer.echo("❌ Operación cancelada")
                return

        service = PropertyService()
        result = await service.delete_property(propiedad_id)

        if result["success"]:
            typer.echo(f"✅ {result['message']}")
        else:
            typer.echo(f"❌ Error: {result['error']}")

    asyncio.run(_delete())


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
                dia,
                disponible,
                price_per_night,
                CASE 
                    WHEN disponible = true THEN 'Disponible'
                    ELSE 'Bloqueada'
                END as estado
            FROM propiedad_disponibilidad 
            WHERE propiedad_id = $1 
            AND dia >= CURRENT_DATE 
            AND dia <= CURRENT_DATE + INTERVAL '30 days'
            ORDER BY dia
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
                reserva_id = result.get('reserva_id')
                total_price = result.get('total_price')
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
        from services.reviews import ReviewService
        review_service = ReviewService()

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
                    await create_review_interactive(review_service, user_profile)
                elif choice == 2:
                    await show_my_reviews(review_service, user_profile)
                elif choice == 3:
                    await show_pending_reviews(review_service, user_profile)
                elif choice == 4:
                    await show_review_stats(review_service, user_profile)
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

    except ImportError:
        typer.echo("❌ El sistema de reseñas no está disponible")
        typer.echo("Presiona Enter para continuar...")
        input()
    except Exception as e:
        typer.echo(f"❌ Error inesperado en gestión de reseñas: {str(e)}")
        logger.error("Error en gestión de reseñas", error=str(e))
        typer.echo("Presiona Enter para continuar...")
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

async def handle_test_cases_menu():
    """Maneja el menú de testeo de casos de uso sin autenticación."""
    while True:
        typer.echo(f"\n🧪 TESTEAR CASOS DE USO")
        typer.echo("=" * 60)
        typer.echo("💡 Prueba funcionalidades sin necesidad de login")
        typer.echo("-" * 60)
        typer.echo("2. 📊 Caso 2: Promedio de rating por anfitrión (MongoDB)")
        typer.echo("3. 🏠 Caso 3: Alojamientos en ciudad específica con capacidad >3 y wifi (Cassandra)")
        typer.echo("7. 🔐 Caso 7: Sesión de un huésped (1h) - Redis")
        typer.echo(
            "10. 🏘️  Caso 10: Comunidades host-huésped (>=3 interacciones)")
        typer.echo("0. ⬅️  Volver al menú principal")

        try:
            choice = typer.prompt("Selecciona una opción (2, 3, 7, 10, 0)", type=int)

            if choice == 2:
                await test_case_2_rating_averages()
            elif choice == 3:
                await test_case_3_property_search()
            elif choice == 7:
                await test_case_7_guest_session()
            elif choice == 10:
                await test_case_10_communities()
            elif choice == 0:
                break
            else:
                typer.echo(
                    "❌ Opción inválida. Por favor selecciona 2, 3, 7, 10 o 0.")

        except ValueError:
            typer.echo("❌ Por favor ingresa un número válido.")
        except KeyboardInterrupt:
            typer.echo("\n👋 Regresando al menú principal...")
            break


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


async def test_case_3_property_search():
    """Caso de uso 3: Búsqueda de alojamientos en ciudad específica con capacidad >3 y wifi usando Cassandra."""
    try:
        from db.cassandra import get_astra_client, create_collection, insert_document, find_documents
        from datetime import datetime
        import random

        typer.echo("\n🏠 CASO DE USO 3: BÚSQUEDA DE ALOJAMIENTOS")
        typer.echo("=" * 70)
        typer.echo("🔍 Cassandra: Ciudad específica, capacidad >3 y wifi")

        # Conectar a AstraDB/Cassandra
        typer.echo("\n🔗 CONECTANDO A ASTRADB (CASSANDRA)...")
        database = await get_astra_client()
        collection_name = "property_search"

        # Verificar/crear colección
        try:
            await create_collection(collection_name)
            typer.echo(f"✅ Colección '{collection_name}' lista")
        except Exception as e:
            if "already exists" in str(e).lower():
                typer.echo(f"ℹ️  Usando colección existente '{collection_name}'")
            else:
                typer.echo(f"⚠️  Error: {e}")

        # Generar datos de ejemplo si no existen
        typer.echo(f"\n📊 GENERANDO DATOS DE EJEMPLO...")
        
        ciudades = ["Barcelona", "Madrid", "Valencia", "Sevilla", "Bilbao", "Granada", "Zaragoza"]
        amenities_options = [
            ["wifi", "parking", "pool"],
            ["wifi", "gym", "balcony"], 
            ["wifi", "parking", "kitchen"],
            ["wifi", "air_conditioning", "pool"],
            ["parking", "gym"],  # Sin wifi
            ["wifi", "kitchen", "washer"],
            ["pool", "balcony"],  # Sin wifi
            ["wifi", "parking", "gym", "pool", "kitchen"]
        ]

        sample_properties = []
        for i in range(15):
            prop = {
                "property_id": f"prop_{i+1:03d}",
                "name": f"Apartamento {['Moderno', 'Acogedor', 'Luminoso', 'Espacioso', 'Céntrico'][i % 5]} {i+1}",
                "city": ciudades[i % len(ciudades)],
                "capacity": random.randint(1, 8),
                "price_per_night": random.randint(45, 180),
                "amenities": amenities_options[i % len(amenities_options)],
                "host_id": f"host_{random.randint(1, 5):03d}",
                "rating": round(random.uniform(3.5, 5.0), 1),
                "created_at": datetime.utcnow().isoformat(),
                "available": random.choice([True, True, False])  # 66% disponible
            }
            sample_properties.append(prop)

        # Insertar propiedades de ejemplo
        for prop in sample_properties:
            try:
                await insert_document(collection_name, prop)
            except Exception as e:
                # Puede fallar si ya existe, continuar
                pass

        typer.echo(f"   ✅ {len(sample_properties)} propiedades de ejemplo generadas")

        # Mostrar criterios de búsqueda
        typer.echo(f"\n🔍 CRITERIOS DE BÚSQUEDA:")
        typer.echo(f"   🏙️  Ciudad específica (seleccionable)")
        typer.echo(f"   👥 Capacidad > 3 personas")
        typer.echo(f"   📶 Amenity: wifi incluido")

        # Permitir al usuario elegir ciudad
        typer.echo(f"\n🏙️  CIUDADES DISPONIBLES:")
        for i, ciudad in enumerate(ciudades, 1):
            typer.echo(f"   {i}. {ciudad}")

        while True:
            try:
                ciudad_choice = typer.prompt(f"Selecciona ciudad (1-{len(ciudades)})", type=int)
                if 1 <= ciudad_choice <= len(ciudades):
                    ciudad_seleccionada = ciudades[ciudad_choice - 1]
                    break
                else:
                    typer.echo(f"❌ Selecciona entre 1 y {len(ciudades)}")
            except ValueError:
                typer.echo("❌ Por favor ingresa un número válido")

        typer.echo(f"\n🔍 BUSCANDO EN: {ciudad_seleccionada}")
        typer.echo("=" * 50)

        # Primero buscar por ciudad (ya que AstraDB no soporta operadores complejos como MongoDB)
        city_filter = {"city": ciudad_seleccionada}

        typer.echo(f"🔎 Ejecutando búsqueda en Cassandra...")
        all_city_results = await find_documents(collection_name, city_filter, limit=100)

        # Filtrar manualmente los resultados según nuestros criterios
        filtered_results = []
        for result in all_city_results:
            capacity = result.get('capacity', 0)
            amenities = result.get('amenities', [])
            available = result.get('available', False)
            
            # Aplicar filtros: capacidad >3, tiene wifi, está disponible
            if (capacity > 3 and 
                'wifi' in amenities and 
                available):
                filtered_results.append(result)

        typer.echo(f"   ✅ {len(all_city_results)} propiedades en {ciudad_seleccionada}")
        typer.echo(f"   🔍 {len(filtered_results)} cumplen criterios (capacidad >3, wifi, disponible)")

        # Mostrar resultados
        if filtered_results:
            typer.echo(f"\n🏠 {len(filtered_results)} ALOJAMIENTOS ENCONTRADOS:")
            typer.echo("=" * 70)
            typer.echo(f"{'ID':<8} {'Nombre':<25} {'Cap.':<4} {'Precio':<7} {'Rating':<7} {'Amenities'}")
            typer.echo("=" * 70)

            total_results = 0
            precio_total = 0
            rating_total = 0

            for result in filtered_results:
                prop_id = result.get('property_id', 'N/A')
                nombre = result.get('name', 'Sin nombre')[:24]
                capacidad = result.get('capacity', 0)
                precio = result.get('price_per_night', 0)
                rating = result.get('rating', 0)
                amenities = result.get('amenities', [])
                
                amenities_str = ", ".join(amenities[:3])  # Mostrar primeros 3
                if len(amenities) > 3:
                    amenities_str += "..."

                # Destacar wifi
                wifi_indicator = "📶"

                typer.echo(f"{prop_id:<8} {nombre:<25} {capacidad:<4} €{precio:<6} ⭐{rating:<6} {wifi_indicator} {amenities_str}")
                
                total_results += 1
                precio_total += precio
                rating_total += rating

            if total_results > 0:
                precio_promedio = precio_total / total_results
                rating_promedio = rating_total / total_results

                typer.echo("=" * 70)
                typer.echo(f"📈 ESTADÍSTICAS DE RESULTADOS:")
                typer.echo(f"   🏠 Total encontrados: {total_results}")
                typer.echo(f"   💰 Precio promedio: €{precio_promedio:.2f}/noche")
                typer.echo(f"   ⭐ Rating promedio: {rating_promedio:.1f}/5")
                typer.echo(f"   🏙️  Ciudad: {ciudad_seleccionada}")
                typer.echo(f"   ✅ Todos con wifi y capacidad >3")

                # Mostrar distribución por capacidad
                capacidades = {}
                for result in filtered_results:
                    cap = result.get('capacity', 0)
                    capacidades[cap] = capacidades.get(cap, 0) + 1

                if capacidades:
                    typer.echo(f"\n👥 DISTRIBUCIÓN POR CAPACIDAD:")
                    for cap in sorted(capacidades.keys()):
                        typer.echo(f"   {cap} personas: {capacidades[cap]} propiedades")

                # Mostrar algunos ejemplos de propiedades encontradas
                typer.echo(f"\n🏠 EJEMPLOS DE PROPIEDADES ENCONTRADAS:")
                for i, result in enumerate(filtered_results[:3], 1):
                    typer.echo(f"   {i}. {result.get('name')} - €{result.get('price_per_night')}/noche")
                    typer.echo(f"      Capacidad: {result.get('capacity')} personas")
                    typer.echo(f"      Amenities: {', '.join(result.get('amenities', []))}")
                    typer.echo(f"      Rating: ⭐{result.get('rating')}/5")
                    typer.echo("")
        else:
            typer.echo(f"❌ No se encontraron alojamientos con los criterios:")
            typer.echo(f"   🏙️  Ciudad: {ciudad_seleccionada}")
            typer.echo(f"   👥 Capacidad > 3")
            typer.echo(f"   📶 WiFi incluido")
            typer.echo(f"   ✅ Disponible")

        # Mostrar información técnica
        typer.echo(f"\n🔧 INFORMACIÓN TÉCNICA:")
        typer.echo(f"   🗄️  Base de datos: AstraDB (Cassandra)")
        typer.echo(f"   📁 Colección: {collection_name}")
        typer.echo(f"   🔍 Filtros aplicados:")
        typer.echo(f"      • city = '{ciudad_seleccionada}'")
        typer.echo(f"      • capacity > 3")
        typer.echo(f"      • amenities contiene 'wifi'")
        typer.echo(f"      • available = true")

        # Mostrar todas las ciudades con datos para referencia
        typer.echo(f"\n📊 RESUMEN POR CIUDADES:")
        for ciudad in ciudades:
            ciudad_filter = {"city": ciudad}
            ciudad_docs = await find_documents(collection_name, ciudad_filter, limit=100)
            con_wifi = len([d for d in ciudad_docs if 'wifi' in d.get('amenities', [])])
            con_capacidad = len([d for d in ciudad_docs if d.get('capacity', 0) > 3])
            disponibles = len([d for d in ciudad_docs if d.get('available', False)])
            
            typer.echo(f"   {ciudad:<12}: {len(ciudad_docs):2d} total, {con_wifi:2d} wifi, {con_capacidad:2d} cap>3, {disponibles:2d} disp.")

    except Exception as e:
        typer.echo(f"❌ Error en búsqueda con Cassandra: {str(e)}")
        logger.error("Error en caso de uso 3", error=str(e))

    typer.echo("\n" + "="*70)
    typer.echo("Presiona Enter para continuar...")
    input()


async def test_case_7_guest_session():
    """Caso de uso 7: Mostrar estado de sesión de un huésped (1h TTL en Redis)."""
    try:
        from services.session import session_manager
        from services.auth import AuthService, UserProfile
        from datetime import datetime, timedelta
        from db.redisdb import get_client as get_redis_client
        import json

        typer.echo("\n🔐 CASO DE USO 7: SESIÓN DE UN HUÉSPED (1H)")
        typer.echo("=" * 70)
        typer.echo("🔍 Demostrando gestión de sesiones con Redis...")

        auth_service = AuthService()

        # Crear un huésped temporal para la demo
        test_user_profile = UserProfile(
            id=99999,
            email="test_guest@demo.com",
            rol="huesped",
            auth_user_id=99999,
            huesped_id=1001,
            anfitrion_id=None,
            nombre="Juan Demo Huésped",
            creado_en=datetime.now()
        )

        typer.echo(f"\n👤 USUARIO DE PRUEBA:")
        typer.echo(f"   📧 Email: {test_user_profile.email}")
        typer.echo(f"   🎭 Rol: {test_user_profile.rol}")
        typer.echo(f"   🆔 ID: {test_user_profile.id}")
        typer.echo(f"   🏠 Huésped ID: {test_user_profile.huesped_id}")

        # Crear nueva sesión
        typer.echo(f"\n🔄 CREANDO NUEVA SESIÓN...")
        token = await session_manager.create_session(test_user_profile)
        
        typer.echo(f"✅ Sesión creada exitosamente!")
        typer.echo(f"   🎟️  Token: {token[:16]}... (total: {len(token)} chars)")
        typer.echo(f"   ⏰ TTL: {session_manager.session_ttl} segundos (1 hora)")
        typer.echo(f"   🕐 Creada: {datetime.now().strftime('%H:%M:%S')}")

        # Mostrar datos en Redis
        typer.echo(f"\n🔍 ESTADO EN REDIS:")
        session_key = f"session:{token}"
        user_sessions_key = f"user:{test_user_profile.id}:sessions"
        
        redis_client = await get_redis_client()
        
        # Obtener datos de sesión
        session_data = await redis_client.get(session_key)
        if session_data:
            session_dict = json.loads(session_data)
            created_at = datetime.fromisoformat(session_dict['created_at'])
            last_activity = datetime.fromisoformat(session_dict['last_activity'])
            
            typer.echo(f"   📊 Clave: {session_key}")
            typer.echo(f"   ✅ Estado: ACTIVA")
            typer.echo(f"   👤 Usuario: {session_dict['email']}")
            typer.echo(f"   🕐 Creada: {created_at.strftime('%H:%M:%S')}")
            typer.echo(f"   🔄 Última actividad: {last_activity.strftime('%H:%M:%S')}")
            
            # Obtener TTL restante
            ttl = await redis_client.ttl(session_key)
            if ttl > 0:
                hours = ttl // 3600
                minutes = (ttl % 3600) // 60
                seconds = ttl % 60
                typer.echo(f"   ⏳ Expira en: {hours:02d}h {minutes:02d}m {seconds:02d}s")
        
        # Mostrar sesiones del usuario
        sessions_count = await redis_client.scard(user_sessions_key)
        typer.echo(f"\n📋 SESIONES DEL USUARIO:")
        typer.echo(f"   🔢 Total sesiones activas: {sessions_count}")
        
        user_sessions = await session_manager.list_user_sessions(test_user_profile.id)
        for i, session in enumerate(user_sessions, 1):
            typer.echo(f"   {i}. Token: {session['token_preview']}")
            typer.echo(f"      📧 Email: {session['email']}")
            if session.get('last_activity'):
                activity = datetime.fromisoformat(session['last_activity'])
                typer.echo(f"      🔄 Última: {activity.strftime('%H:%M:%S')}")

        # Probar validación de sesión
        typer.echo(f"\n🔍 VALIDANDO SESIÓN (peek - sin refresh):")
        validated_user = await session_manager.peek_session(token)
        if validated_user:
            typer.echo(f"   ✅ Sesión válida para: {validated_user.email}")
            typer.echo(f"   🎭 Rol: {validated_user.rol}")
        else:
            typer.echo(f"   ❌ Sesión no válida o expirada")

        # Mostrar estructura de datos completa
        typer.echo(f"\n📋 ESTRUCTURA DE DATOS EN REDIS:")
        if session_data:
            session_dict = json.loads(session_data)
            typer.echo(f"   🔑 Campos almacenados:")
            for key, value in session_dict.items():
                if isinstance(value, str) and len(value) > 50:
                    display_value = value[:47] + "..."
                else:
                    display_value = value
                typer.echo(f"      • {key}: {display_value}")

        # Simular actividad (refresh)
        typer.echo(f"\n🔄 SIMULANDO ACTIVIDAD (refresh automático):")
        refreshed_user = await session_manager.get_session(token)
        if refreshed_user:
            typer.echo(f"   ✅ Sesión refrescada exitosamente")
            typer.echo(f"   ⏰ TTL renovado a: {session_manager.session_ttl} segundos")
            
            # Mostrar nuevo TTL
            ttl_after = await redis_client.ttl(session_key)
            if ttl_after > 0:
                hours = ttl_after // 3600
                minutes = (ttl_after % 3600) // 60
                seconds = ttl_after % 60
                typer.echo(f"   ⏳ Nuevo tiempo restante: {hours:02d}h {minutes:02d}m {seconds:02d}s")

        typer.echo(f"\n🧹 LIMPIEZA: ¿Eliminar sesión de prueba? (s/n)")
        cleanup = input().lower().strip()
        
        if cleanup in ['s', 'si', 'sí', 'y', 'yes']:
            invalidated = await session_manager.invalidate_session(token)
            if invalidated:
                typer.echo(f"✅ Sesión eliminada correctamente")
            else:
                typer.echo(f"⚠️  Sesión ya había expirado")
        else:
            typer.echo(f"ℹ️  Sesión dejada activa (expirará automáticamente)")

        typer.echo(f"\n📈 RESUMEN DEL CASO DE USO:")
        typer.echo(f"   ✅ Creación de sesión en Redis")
        typer.echo(f"   ✅ TTL de 1 hora configurado")
        typer.echo(f"   ✅ Validación sin refresh (peek)")
        typer.echo(f"   ✅ Validación con refresh (sliding window)")
        typer.echo(f"   ✅ Listado de sesiones del usuario")
        typer.echo(f"   ✅ Gestión de expiración automática")

    except Exception as e:
        typer.echo(f"❌ Error en demostración de sesiones: {str(e)}")
        logger.error("Error en caso de uso 7", error=str(e))

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


if __name__ == "__main__":
    app()
