"""
CLI Session Management Module

This module provides session management functionality for the CLI interactive mode.
It includes state management, validation helpers, and interactive handlers.

Submodules:
    - state: Global session state (token, user profile)
    - helpers: Validation and refresh utilities
    - interactive: Menu and handler functions
"""

# State management
from .state import (
    get_session_token,
    set_session_token,
    get_current_user,
    set_current_user,
    clear_session,
    has_active_session
)

# Validation and refresh helpers
from .helpers import (
    validate_session_or_expire,
    refresh_session_after_action,
    restore_previous_session
)

# Interactive handlers
from .interactive import (
    show_auth_menu,
    show_main_menu,
    handle_login,
    handle_register,
    handle_logout,
    show_user_profile,
    show_active_sessions
)

__all__ = [
    # State management
    "get_session_token",
    "set_session_token",
    "get_current_user",
    "set_current_user",
    "clear_session",
    "has_active_session",
    # Helpers
    "validate_session_or_expire",
    "refresh_session_after_action",
    "restore_previous_session",
    # Interactive
    "show_auth_menu",
    "show_main_menu",
    "handle_login",
    "handle_register",
    "handle_logout",
    "show_user_profile",
    "show_active_sessions",
]
