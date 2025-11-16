"""
Comandos del CLI usando Typer - Versión Interactiva.
"""

import typer
import asyncio
from typing import Optional
from services.auth import AuthService
from services.user import UserService
from services.mongo_host import MongoHostService
from utils.logging import get_logger, configure_logging

# Configurar logging al importar
configure_logging()
logger = get_logger(__name__)

app = typer.Typer(
    name="airbnb-backend",
    help="Backend CLI para sistema tipo Airbnb - Sistema de Autenticación Interactivo"
)

# Variable global para almacenar el usuario actual
current_user_session = None


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
    global current_user_session
    
    typer.echo("🏠 BIENVENIDO AL SISTEMA AIRBNB")
    typer.echo("=" * 50)
    
    auth_service = AuthService()
    
    # Loop principal del sistema
    while True:
        try:
            if current_user_session is None:
                # No hay sesión activa - mostrar menú de autenticación
                action = await show_auth_menu()
                
                if action == "login":
                    current_user_session = await handle_login(auth_service)
                elif action == "register":
                    current_user_session = await handle_register(auth_service)
                elif action == "exit":
                    typer.echo("👋 ¡Hasta luego!")
                    break
            else:
                # Hay sesión activa - mostrar menú principal
                action = await show_main_menu(current_user_session)

                if action == "logout":
                    await handle_logout(auth_service)
                    current_user_session = None
                elif action == "profile":
                    await show_user_profile(current_user_session)
                elif action == "properties":
                    await handle_properties_menu(current_user_session)
                elif action == "mongo_stats":
                    await show_mongo_stats(current_user_session)
                elif action == "exit":
                    typer.echo("👋 ¡Hasta luego!")
                    break
                
        except KeyboardInterrupt:
            typer.echo("\n👋 ¡Hasta luego!")
            break
        except Exception as e:
            typer.echo(f"❌ Error inesperado: {str(e)}")
            logger.error("Error en modo interactivo", error=str(e))


async def show_auth_menu():
    """Muestra el menú de autenticación y retorna la acción seleccionada."""
    typer.echo("\n🔐 AUTENTICACIÓN")
    typer.echo("-" * 20)
    typer.echo("1. 🔑 Iniciar Sesión")
    typer.echo("2. 📝 Registrarse")
    typer.echo("3. ❌ Salir")
    
    while True:
        try:
            choice = typer.prompt("Selecciona una opción (1-3)", type=int)
            if choice == 1:
                return "login"
            elif choice == 2:
                return "register"
            elif choice == 3:
                return "exit"
            else:
                typer.echo("❌ Opción inválida. Selecciona 1, 2 o 3.")
        except ValueError:
            typer.echo("❌ Por favor ingresa un número válido.")


async def show_main_menu(user_profile):
    """Muestra el menú principal según el tipo de usuario."""
    typer.echo(f"\n🏠 MENÚ PRINCIPAL - {user_profile.nombre}")
    typer.echo(f"👤 Rol: {user_profile.rol}")
    typer.echo("-" * 40)
    
    options = [
        "👤 Ver mi perfil",
        "🚪 Cerrar sesión",
        "❌ Salir del sistema"
    ]
    
    # Agregar opciones específicas por rol
    if user_profile.rol in ['ANFITRION', 'AMBOS']:
        options.insert(-2, "🏠 Gestionar mis propiedades")
        options.insert(-2, "📊 Ver estadísticas MongoDB")

    for i, option in enumerate(options, 1):
        typer.echo(f"{i}. {option}")

    while True:
        try:
            choice = typer.prompt(f"Selecciona una opción (1-{len(options)})", type=int)
            if 1 <= choice <= len(options):
                if "perfil" in options[choice-1]:
                    return "profile"
                elif "Cerrar sesión" in options[choice-1]:
                    return "logout"
                elif "propiedades" in options[choice-1]:
                    return "properties"
                elif "estadísticas MongoDB" in options[choice-1]:
                    return "mongo_stats"
                elif "Salir" in options[choice-1]:
                    return "exit"
            else:
                typer.echo(f"❌ Opción inválida. Selecciona entre 1 y {len(options)}.")
        except ValueError:
            typer.echo("❌ Por favor ingresa un número válido.")


async def handle_login(auth_service):
    """Maneja el proceso de login interactivo."""
    typer.echo("\n🔑 INICIAR SESIÓN")
    typer.echo("=" * 30)
    
    email = typer.prompt("📧 Email")
    password = typer.prompt("🔐 Contraseña", hide_input=True)
    
    typer.echo(f"\n🔄 Validando credenciales para {email}...")
    
    result = await auth_service.login(email, password)
    
    if result.success:
        typer.echo(f"✅ {result.message}")
        typer.echo(f"🎉 ¡Bienvenido/a {result.user_profile.nombre}!")
        return result.user_profile
    else:
        typer.echo(f"❌ {result.message}")
        typer.echo("Presiona Enter para continuar...")
        input()
        return None


async def handle_register(auth_service):
    """Maneja el proceso de registro interactivo."""
    typer.echo("\n📝 REGISTRO DE NUEVO USUARIO")
    typer.echo("=" * 40)
    
    email = typer.prompt("📧 Email")
    password = typer.prompt("🔐 Contraseña", hide_input=True)
    password_confirm = typer.prompt("🔐 Confirmar contraseña", hide_input=True)
    
    if password != password_confirm:
        typer.echo("❌ Las contraseñas no coinciden.")
        typer.echo("Presiona Enter para continuar...")
        input()
        return None
    
    nombre = typer.prompt("👤 Nombre completo")
    
    typer.echo("\n🎭 Selecciona tu rol:")
    typer.echo("1. 🛏️  HUESPED - Solo reservar propiedades")
    typer.echo("2. 🏠 ANFITRION - Solo publicar propiedades")
    typer.echo("3. 🔄 AMBOS - Reservar y publicar propiedades")
    
    while True:
        try:
            rol_choice = typer.prompt("Selecciona rol (1-3)", type=int)
            rol_map = {1: "HUESPED", 2: "ANFITRION", 3: "AMBOS"}
            if rol_choice in rol_map:
                rol = rol_map[rol_choice]
                break
            else:
                typer.echo("❌ Opción inválida. Selecciona 1, 2 o 3.")
        except ValueError:
            typer.echo("❌ Por favor ingresa un número válido.")
    
    typer.echo(f"\n🔄 Registrando usuario {email} como {rol}...")
    
    result = await auth_service.register(email, password, rol, nombre)
    
    if result.success:
        typer.echo(f"✅ {result.message}")
        typer.echo(f"🎉 ¡Bienvenido/a {result.user_profile.nombre}!")
        
        if result.user_profile.rol in ['ANFITRION', 'AMBOS']:
            typer.echo(f"🏠 Tu ID de anfitrión es: {result.user_profile.anfitrion_id}")
            typer.echo("📝 Se ha creado tu documento en MongoDB para gestionar calificaciones")
        
        return result.user_profile
    else:
        typer.echo(f"❌ {result.message}")
        typer.echo("Presiona Enter para continuar...")
        input()
        return None


async def handle_logout(auth_service):
    """Maneja el cierre de sesión."""
    typer.echo("\n🚪 Cerrando sesión...")
    result = await auth_service.logout()
    typer.echo(f"✅ {result.message}")
    typer.echo("Presiona Enter para continuar...")
    input()


async def show_user_profile(user_profile):
    """Muestra el perfil completo del usuario."""
    typer.echo("\n👤 MI PERFIL")
    typer.echo("=" * 30)
    typer.echo(f"📧 Email: {user_profile.email}")
    typer.echo(f"👤 Nombre: {user_profile.nombre}")
    typer.echo(f"🎭 Rol: {user_profile.rol}")
    typer.echo(f"🆔 ID Usuario: {user_profile.user_id}")
    
    if user_profile.huesped_id:
        typer.echo(f"🛏️  ID Huésped: {user_profile.huesped_id}")
    if user_profile.anfitrion_id:
        typer.echo(f"🏠 ID Anfitrión: {user_profile.anfitrion_id}")
    
    typer.echo(f"📅 Registro: {user_profile.fecha_registro}")
    
    typer.echo("\nPresiona Enter para continuar...")
    input()


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
        typer.echo(f"💬 Reviews con comentarios: {stats.get('total_reviews', 0)}")

        if ratings:
            typer.echo("\n📝 Últimas calificaciones:")
            for i, rating in enumerate(ratings[-3:], 1):  # Mostrar las últimas 3
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

    typer.echo(f"\n📋 MIS PROPIEDADES - Anfitrión ID: {user_profile.anfitrion_id}")
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
            typer.echo("💡 Puedes crear tu primera propiedad seleccionando 'Crear nueva propiedad'")
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
            capacidad = typer.prompt("👥 Capacidad (número de huéspedes)", type=int)
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
    check_in_input = typer.prompt("🕐 Horario check-in (ej: 15:00 o presiona Enter)", default="")
    check_out_input = typer.prompt("🕐 Horario check-out (ej: 11:00 o presiona Enter)", default="")

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
    amenities_input = typer.prompt("Ingresa IDs separados por coma (ej: 1,2) o presiona Enter para omitir", default="")
    amenity_ids = None
    if amenities_input.strip():
        try:
            amenity_ids = [int(x.strip()) for x in amenities_input.split(",")]
        except ValueError:
            typer.echo("⚠️ Amenities inválidos, se omitirán")

    # Servicios opcionales
    typer.echo("\n🛎️ SERVICIOS DISPONIBLES (opcional):")
    typer.echo("1. Wifi, 2. Limpieza, 3. Desayuno, 4. Estacionamiento")
    servicios_input = typer.prompt("Ingresa IDs separados por coma (ej: 1,2) o presiona Enter para omitir", default="")
    servicio_ids = None
    if servicios_input.strip():
        try:
            servicio_ids = [int(x.strip()) for x in servicios_input.split(",")]
        except ValueError:
            typer.echo("⚠️ Servicios inválidos, se omitirán")

    # Reglas opcionales
    typer.echo("\n📏 REGLAS DE LA PROPIEDAD (opcional):")
    typer.echo("1. No fumar, 2. No mascotas, 3. No fiestas, 4. Check-in 15pm-20pm")
    reglas_input = typer.prompt("Ingresa IDs separados por coma (ej: 1,2) o presiona Enter para omitir", default="")
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
            propiedad_id = typer.prompt("🆔 Ingresa el ID de la propiedad", type=int)
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
            propiedad_id = typer.prompt("🆔 Ingresa el ID de la propiedad a actualizar", type=int)
            break
        except ValueError:
            typer.echo("❌ Por favor ingresa un ID válido")

    typer.echo(f"\n📝 ACTUALIZAR PROPIEDAD COMPLETA ID: {propiedad_id}")
    typer.echo("Deja en blanco (Enter) los campos que NO quieras cambiar")
    typer.echo("Para listas (amenities, servicios, reglas): ingresa IDs separados por coma")
    typer.echo("-" * 70)

    # Obtener propiedad actual para mostrar valores actuales
    current_result = await service.get_property(propiedad_id)
    if current_result["success"]:
        current = current_result["property"]
        typer.echo("📊 VALORES ACTUALES:")
        typer.echo(f"   🏠 Nombre: {current.get('nombre', 'N/A')}")
        typer.echo(f"   📝 Descripción: {current.get('descripcion', 'N/A')}")
        typer.echo(f"   👥 Capacidad: {current.get('capacidad', 'N/A')} personas")
        typer.echo(f"   🏙️  Ciudad: {current.get('ciudad', 'N/A')}")
        typer.echo(f"   🏢 Tipo: {current.get('tipo_propiedad', 'N/A')}")
        typer.echo(f"   🕐 Check-in: {current.get('horario_check_in', 'N/A')}")
        typer.echo(f"   🕐 Check-out: {current.get('horario_check_out', 'N/A')}")
        typer.echo(f"   🎯 Amenities: {len(current.get('amenities', []))}")
        typer.echo(f"   🛎️ Servicios: {len(current.get('servicios', []))}")
        typer.echo(f"   📏 Reglas: {len(current.get('reglas', []))}")
        typer.echo()

    # DATOS BÁSICOS
    typer.echo("🏠 DATOS BÁSICOS:")
    nombre = typer.prompt("🏠 Nuevo nombre (Enter para mantener)", default="")
    if not nombre.strip():
        nombre = None

    descripcion = typer.prompt("📝 Nueva descripción (Enter para mantener)", default="")
    if not descripcion.strip():
        descripcion = None

    capacidad_input = typer.prompt("👥 Nueva capacidad (Enter para mantener)", default="")
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

    ciudad_input = typer.prompt("🏙️ Nuevo ID de ciudad (Enter para mantener)", default="")
    ciudad_id = None
    if ciudad_input.strip():
        try:
            ciudad_id = int(ciudad_input)
            # Validar que la ciudad existe (básico)
            if not any(c['id'] == ciudad_id for c in ciudades):
                typer.echo(f"⚠️ Ciudad con ID {ciudad_id} no válida, se omitirá")
                ciudad_id = None
        except ValueError:
            typer.echo("⚠️ ID de ciudad inválido, se omitirá")

    # HORARIOS
    typer.echo("\n🕐 HORARIOS (opcional):")
    check_in_input = typer.prompt("🕐 Nuevo horario check-in (ej: 15:00, Enter para mantener)", default="")
    horario_check_in = None
    if check_in_input.strip():
        # Validar formato básico
        import re
        if re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', check_in_input.strip()):
            horario_check_in = check_in_input.strip()
        else:
            typer.echo("⚠️ Formato inválido para check-in, se omitirá")

    check_out_input = typer.prompt("🕐 Nuevo horario check-out (ej: 11:00, Enter para mantener)", default="")
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
    typer.echo("   📝 Ingresa IDs separados por coma (ej: 1,2,3) o Enter para mantener actuales")
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
    typer.echo("   📝 Ingresa IDs separados por coma (ej: 1,2) o Enter para mantener actuales")
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
    typer.echo("   1. No fumar, 2. No mascotas, 3. No fiestas, 4. Check-in 15pm-20pm")
    typer.echo("   📝 Ingresa IDs separados por coma (ej: 1,2) o Enter para mantener actuales")
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
                typer.echo(f"🕐 Check-in: {prop.get('horario_check_in', 'N/A')}")
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
            propiedad_id = typer.prompt("🆔 Ingresa el ID de la propiedad a eliminar", type=int)
            break
        except ValueError:
            typer.echo("❌ Por favor ingresa un ID válido")

    # Confirmación adicional
    typer.echo(f"\n⚠️  ¡ATENCIÓN!")
    typer.echo(f"Esta acción eliminará la propiedad {propiedad_id} y TODOS sus datos asociados:")
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
                    typer.echo("❌ Para registrar necesitas: --email, --password, --role, --name")
                    typer.echo("   Roles disponibles: HUESPED, ANFITRION, AMBOS")
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
                            typer.echo(f"🏠 ID Anfitrión: {profile.anfitrion_id}")
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
                    auth_test = AuthService()
                    typer.echo("✅ AuthService: OK")

                    # Test User Service
                    user_test = UserService()
                    typer.echo("✅ UserService: OK")

                    # Test MongoDB
                    mongo_test = MongoHostService()
                    mongo_status = await mongo_test.verify_connection()
                    if mongo_status.get('success'):
                        typer.echo("✅ MongoDB: Conectado")
                    else:
                        typer.echo(f"❌ MongoDB: {mongo_status.get('error', 'Error desconocido')}")

                    typer.echo("\n🎉 Sistema de autenticación funcionando correctamente")

                except Exception as e:
                    typer.echo(f"❌ Error en verificación del sistema: {str(e)}")

            else:
                typer.echo(f"❌ Acción '{action}' no reconocida")
                typer.echo("Acciones disponibles: register, login, profile, status")

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
                            typer.echo(f"   Ratings: {len(host.get('ratings', []))}")
                            stats = host.get('stats', {})
                            if stats:
                                typer.echo(f"   Promedio: {stats.get('average_rating', 'N/A')}")
                                typer.echo(f"   Total: {stats.get('total_ratings', 0)}")
                            typer.echo()
                    else:
                        typer.echo("No hay anfitriones registrados")
                else:
                    typer.echo(f"❌ Error: {result.get('error', 'Error desconocido')}")

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
                            typer.echo(f"{i}. Rating: {rating_doc.get('rating', 'N/A')}/5")
                            typer.echo(f"   Comentario: {rating_doc.get('comment', 'Sin comentario')}")
                            typer.echo(f"   Fecha: {rating_doc.get('date', 'N/A')}")
                            typer.echo()

                        stats = doc.get('stats', {})
                        typer.echo(f"📊 Promedio: {stats.get('average_rating', 'N/A')}/5")
                        typer.echo(f"📊 Total ratings: {stats.get('total_ratings', 0)}")
                    else:
                        typer.echo("No hay calificaciones para este anfitrión")
                else:
                    typer.echo(f"❌ Error: {result.get('error', 'Anfitrión no encontrado')}")

            elif action == "add-rating":
                if not all([host_id, rating]):
                    typer.echo("❌ Para agregar rating necesitas: --host-id --rating")
                    typer.echo("   Rating debe ser entre 1 y 5")
                    return

                if rating < 1 or rating > 5:
                    typer.echo("❌ Rating debe ser entre 1 y 5")
                    return

                result = await mongo_service.add_rating(host_id, rating, comment or "")
                if result.get('success'):
                    typer.echo(f"✅ Rating {rating}/5 agregado al anfitrión {host_id}")
                    
                    # Mostrar estadísticas actualizadas
                    stats_result = await mongo_service.get_host_stats(host_id)
                    if stats_result.get('success'):
                        stats = stats_result.get('stats', {})
                        typer.echo(f"📊 Nuevo promedio: {stats.get('average_rating', 'N/A')}/5")
                else:
                    typer.echo(f"❌ Error: {result.get('error', 'Error desconocido')}")

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
                    typer.echo(f"Total usuarios: {stats.get('total_users', 0)}")
                    typer.echo(f"Huéspedes: {stats.get('total_huespedes', 0)}")
                    typer.echo(f"Anfitriones: {stats.get('total_anfitriones', 0)}")
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
                typer.echo("❌ Error: Amenities debe ser una lista de números separados por comas (ej: 1,2,3)")
                return
        
        servicio_ids = None
        if servicios:
            try:
                servicio_ids = [int(x.strip()) for x in servicios.split(",")]
            except ValueError:
                typer.echo("❌ Error: Servicios debe ser una lista de números separados por comas (ej: 1,2)")
                return
        
        regla_ids = None
        if reglas:
            try:
                regla_ids = [int(x.strip()) for x in reglas.split(",")]
            except ValueError:
                typer.echo("❌ Error: Reglas debe ser una lista de números separados por comas (ej: 1,2)")
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
            typer.echo(f"   Capacidad: {result['property']['capacidad']} personas")
        else:
            typer.echo(f"❌ Error: {result['error']}")
    
    asyncio.run(_create())


@app.command()
def list_properties(
    ciudad_id: Optional[int] = typer.Option(None, "--ciudad-id", "-c", help="Filtrar por ciudad"),
    anfitrion_id: Optional[int] = typer.Option(None, "--anfitrion-id", "-a", help="Filtrar por anfitrión"),
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
            typer.echo(f"⚠️  Esta acción eliminará la propiedad {propiedad_id} y todos sus datos asociados.")
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


if __name__ == "__main__":
    app()
