"""
Comandos del CLI usando Typer - Versión Simplificada.
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
    help="Backend CLI para sistema tipo Airbnb - Sistema de Autenticación"
)


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


@app.command()
def mongo(
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


@app.command()
def users(
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


if __name__ == "__main__":
    app()