"""
Session state management for CLI interactive mode.

This module manages global session state including the current session token
and user profile. It provides a clean interface for getting, setting, and
clearing session state.
"""

from typing import Optional
from services.auth import UserProfile


# Global session state
_current_session_token: Optional[str] = None
_current_user_session: Optional[UserProfile] = None


def get_session_token() -> Optional[str]:
    """
    Get the current session token.

    Returns:
        The current session token or None if no active session
    """
    return _current_session_token


def set_session_token(token: Optional[str]) -> None:
    """
    Set the current session token.

    Args:
        token: The session token to store, or None to clear
    """
    global _current_session_token
    _current_session_token = token


def get_current_user() -> Optional[UserProfile]:
    """
    Get the current user profile.

    Returns:
        The current user profile or None if no active session
    """
    return _current_user_session


def set_current_user(user: Optional[UserProfile]) -> None:
    """
    Set the current user profile.

    Args:
        user: The user profile to store, or None to clear
    """
    global _current_user_session
    _current_user_session = user


def clear_session() -> None:
    """
    Clear all session state (token and user profile).

    Call this on logout or session expiration.
    """
    global _current_session_token, _current_user_session
    _current_session_token = None
    _current_user_session = None


def has_active_session() -> bool:
    """
    Check if there's an active session.

    Returns:
        True if both session token and user profile exist, False otherwise
    """
    return _current_session_token is not None and _current_user_session is not None
