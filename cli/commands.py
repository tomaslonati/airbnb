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


@app.command(name="auth-cmd")
def auth_cmd(
    action: str = typer.Argument(
        ..., help="Acción: 'login', 'register', 'logout', 'profile', o 'status'"),
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
    action: str = typer.Argument(
        ..., help="Acción: 'hosts', 'ratings', 'add-rating', 'stats'"),
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
    action: str = typer.Argument(
        ..., help="Acción: 'list', 'profile', 'stats'"),
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
    nombre: str = typer.Argument(..., help="Nombre de la propiedad"),
    descripcion: str = typer.Argument(..., help="Descripción de la propiedad"),
    capacidad: int = typer.Argument(..., help="Capacidad de personas"),
    ciudad_id: int = typer.Option(..., "--ciudad-id", "-c", help="ID de la ciudad"),
    anfitrion_id: int = typer.Option(..., "--anfitrion-id", "-a", help="ID del anfitrión"),
    tipo_propiedad_id: int = typer.Option(..., "--tipo-id", "-t", help="ID del tipo de propiedad"),
):
    """Crea una nueva propiedad."""
    from services.properties import PropertyService
    
    async def _create():
        service = PropertyService()
        result = await service.create_property(
            nombre=nombre,
            descripcion=descripcion,
            capacidad=capacidad,
            ciudad_id=ciudad_id,
            anfitrion_id=anfitrion_id,
            tipo_propiedad_id=tipo_propiedad_id
        )
        
        if result["success"]:
            typer.echo(f"✅ {result['message']}")
            typer.echo(f"   ID de la propiedad: {result['property_id']}")
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
    propiedad_id: int = typer.Argument(..., help="ID de la propiedad"),
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
    propiedad_id: int = typer.Argument(..., help="ID de la propiedad"),
    nombre: Optional[str] = typer.Option(None, "--nombre", "-n", help="Nuevo nombre"),
    descripcion: Optional[str] = typer.Option(None, "--descripcion", "-d", help="Nueva descripción"),
    capacidad: Optional[int] = typer.Option(None, "--capacidad", "-c", help="Nueva capacidad"),
    tipo_propiedad_id: Optional[int] = typer.Option(None, "--tipo", "-t", help="Nuevo tipo de propiedad"),
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
    propiedad_id: int = typer.Argument(..., help="ID de la propiedad"),
    confirm: bool = typer.Option(False, "--confirm", "-y", help="Confirmar eliminación sin preguntar"),
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