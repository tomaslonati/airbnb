"""
Session validation and management helpers.

This module provides utilities for validating sessions, checking expiration,
and refreshing session TTL (sliding window pattern).
"""

import typer
from services.auth import AuthService
from cli.sessions.state import clear_session


async def validate_session_or_expire(auth_service: AuthService) -> bool:
    """
    Validate the current session without refreshing its TTL.

    If the session has expired, clears the session state and displays
    an expiration message to the user.

    This uses check_session_validity() which does NOT refresh the TTL,
    allowing us to check if a session has truly expired before taking action.

    Args:
        auth_service: The AuthService instance to use for validation

    Returns:
        True if the session is still valid, False if expired
    """
    is_valid = await auth_service.check_session_validity()

    if not is_valid:
        typer.echo("\n⚠️  Tu sesión ha expirado (90 segundos de inactividad)")
        typer.echo("Por favor inicia sesión nuevamente\n")
        clear_session()
        return False

    return True


async def refresh_session_after_action(auth_service: AuthService) -> None:
    """
    Refresh the session TTL after a successful user action.

    This implements the sliding window pattern - when the user performs
    an action, we extend their session by another 90 seconds to reward
    active usage.

    This uses validate_session() which DOES refresh the TTL.

    Args:
        auth_service: The AuthService instance to use for refreshing
    """
    await auth_service.validate_session()


async def restore_previous_session(auth_service: AuthService) -> bool:
    """
    Attempt to restore a previous session on CLI startup.

    If a session token exists in state, tries to restore the session from Redis.
    If successful, updates the user profile in state.

    Args:
        auth_service: The AuthService instance to use for restoration

    Returns:
        True if session was restored successfully, False otherwise
    """
    from cli.sessions.state import get_session_token, set_current_user, clear_session

    token = get_session_token()
    if not token:
        return False

    typer.echo("\n🔄 Intentando restaurar sesión previa...")
    restore_result = await auth_service.restore_session(token)

    if restore_result.success:
        set_current_user(restore_result.user_profile)
        typer.echo(restore_result.message)
        return True
    else:
        typer.echo("⚠️  Sesión anterior expiró, por favor inicia sesión nuevamente")
        clear_session()
        return False
