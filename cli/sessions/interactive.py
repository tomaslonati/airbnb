"""
Interactive session management functions for CLI.

This module contains all the interactive menu handlers and user-facing
functions for session management in the CLI interactive mode.
"""

import typer
from services.auth import AuthService, UserProfile
from cli.sessions.state import set_session_token, clear_session


async def show_auth_menu() -> str:
    """
    Display the authentication menu and return the selected action.

    Returns:
        Action string: "login", "register", or "exit"
    """
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


async def show_main_menu(user_profile: UserProfile) -> str:
    """
    Display the main menu based on user role and return the selected action.

    Args:
        user_profile: The current user's profile

    Returns:
        Action string: "profile", "sessions", "logout", "mongo_stats",
                      "properties", "reservations", or "exit"
    """
    typer.echo(f"\n🏠 MENÚ PRINCIPAL - {user_profile.nombre}")
    typer.echo(f"👤 Rol: {user_profile.rol}")
    typer.echo("-" * 40)

    options = [
        "👤 Ver mi perfil",
        "🔑 Ver sesiones activas",
        "🚪 Cerrar sesión",
        "❌ Salir del sistema"
    ]

    # Add role-specific options
    if user_profile.rol in ['ANFITRION', 'AMBOS']:
        options.insert(-3, "📊 Ver estadísticas MongoDB")
        options.insert(-3, "🏠 Gestionar mis propiedades")
        options.insert(-3, "📅 Gestionar disponibilidad de propiedades")

    if user_profile.rol in ['HUESPED', 'AMBOS']:
        options.insert(-3, "📅 Gestionar mis reservas")

    for i, option in enumerate(options, 1):
        typer.echo(f"{i}. {option}")

    while True:
        try:
            choice = typer.prompt(f"Selecciona una opción (1-{len(options)})", type=int)
            if 1 <= choice <= len(options):
                if "perfil" in options[choice-1]:
                    return "profile"
                elif "sesiones activas" in options[choice-1]:
                    return "sessions"
                elif "Cerrar sesión" in options[choice-1]:
                    return "logout"
                elif "estadísticas MongoDB" in options[choice-1]:
                    return "mongo_stats"
                elif "Gestionar mis propiedades" in options[choice-1]:
                    return "properties"
                elif "disponibilidad de propiedades" in options[choice-1]:
                    return "availability"
                elif "Gestionar mis reservas" in options[choice-1]:
                    return "reservations"
                elif "Salir" in options[choice-1]:
                    return "exit"
            else:
                typer.echo(f"❌ Opción inválida. Selecciona entre 1 y {len(options)}.")
        except ValueError:
            typer.echo("❌ Por favor ingresa un número válido.")


async def handle_login(auth_service: AuthService) -> UserProfile:
    """
    Handle the interactive login process.

    Args:
        auth_service: The AuthService instance

    Returns:
        UserProfile if login successful, None otherwise
    """
    typer.echo("\n🔑 INICIAR SESIÓN")
    typer.echo("=" * 30)

    email = typer.prompt("📧 Email")
    password = typer.prompt("🔐 Contraseña", hide_input=True)

    typer.echo(f"\n🔄 Validando credenciales para {email}...")

    result = await auth_service.login(email, password)

    if result.success:
        typer.echo(f"✅ {result.message}")
        typer.echo(f"🎉 ¡Bienvenido/a {result.user_profile.nombre}!")

        # Store the session token
        set_session_token(result.session_token)
        typer.echo("🔑 Sesión creada (TTL: 1 hora con auto-refresh)")

        return result.user_profile
    else:
        typer.echo(f"❌ {result.message}")
        typer.echo("Presiona Enter para continuar...")
        input()
        return None


async def handle_register(auth_service: AuthService) -> UserProfile:
    """
    Handle the interactive registration process.

    Args:
        auth_service: The AuthService instance

    Returns:
        UserProfile if registration successful, None otherwise
    """
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


async def handle_logout(auth_service: AuthService) -> None:
    """
    Handle the logout process.

    Args:
        auth_service: The AuthService instance
    """
    typer.echo("\n🚪 Cerrando sesión...")
    result = await auth_service.logout()

    # Clear session state
    clear_session()

    typer.echo(f"✅ {result.message}")
    typer.echo("Presiona Enter para continuar...")
    input()


async def show_user_profile(user_profile: UserProfile) -> None:
    """
    Display the current user's profile information.

    Args:
        user_profile: The user profile to display
    """
    typer.echo("\n👤 MI PERFIL")
    typer.echo("=" * 30)
    typer.echo(f"📧 Email: {user_profile.email}")
    typer.echo(f"👤 Nombre: {user_profile.nombre}")
    typer.echo(f"🎭 Rol: {user_profile.rol}")
    typer.echo(f"🆔 ID Usuario: {user_profile.id}")

    if user_profile.huesped_id:
        typer.echo(f"🛏️  ID Huésped: {user_profile.huesped_id}")
    if user_profile.anfitrion_id:
        typer.echo(f"🏠 ID Anfitrión: {user_profile.anfitrion_id}")

    typer.echo(f"📅 Registro: {user_profile.creado_en}")

    typer.echo("\nPresiona Enter para continuar...")
    input()


async def show_active_sessions(auth_service: AuthService) -> None:
    """
    Display all active sessions for the current user.

    Args:
        auth_service: The AuthService instance
    """
    typer.echo("\n🔑 SESIONES ACTIVAS")
    typer.echo("=" * 50)

    sessions = await auth_service.list_sessions()

    if sessions is None:
        typer.echo("❌ No hay usuario autenticado")
    elif len(sessions) == 0:
        typer.echo("📝 No hay sesiones activas")
    else:
        typer.echo(f"Total de sesiones activas: {len(sessions)}\n")
        for i, session in enumerate(sessions, 1):
            typer.echo(f"Sesión {i}:")
            typer.echo(f"   🔑 Token: {session.get('token_preview', 'N/A')}")
            typer.echo(f"   📧 Email: {session.get('email', 'N/A')}")
            typer.echo(f"   ⏰ Creada: {session.get('created_at', 'N/A')}")
            typer.echo(f"   🕒 Última actividad: {session.get('last_activity', 'N/A')}")
            typer.echo()

    typer.echo("Presiona Enter para continuar...")
    input()
