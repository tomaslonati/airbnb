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

# Importar módulos CLI de features
from cli.auth.commands import app as auth_app
from cli.properties.commands import app as properties_app
from cli.reservations.commands import app as reservations_app, handle_reservation_management

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
    get_session_token,
    has_active_session
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
app.add_typer(reservations_app, name="reservations", help="Gestión de reservas")


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
                    elif action == "properties":
                        await handle_property_management(current_user)
                    elif action == "reservations":
                        await handle_reservation_management(current_user)

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


# Nota: Los comandos de propiedades están integrados vía app.add_typer(properties_app)
# y se pueden usar como: python main.py properties create ...
# Los comandos de autenticación están integrados vía app.add_typer(auth_app)
# y se pueden usar como: python main.py auth register ...


if __name__ == "__main__":
    app()