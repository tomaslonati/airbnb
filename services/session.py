"""
Session Management Service using Redis

This module provides session management functionality using Redis as the session store.
Sessions have a configurable TTL and support auto-refresh on activity (sliding window).
"""

import secrets
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import asdict

import structlog

from db.redisdb import get_key, set_key, delete_key, get_client as get_redis_client
from services.auth import UserProfile

logger = structlog.get_logger()


class SessionManager:
    """
    Manages user sessions using Redis as the backend store.

    Features:
    - Secure token generation
    - TTL-based session expiration
    - Auto-refresh on activity (sliding window)
    - Multi-session support per user
    - Session listing and invalidation
    """

    def __init__(self, session_ttl: int = 90):
        """
        Initialize SessionManager

        Args:
            session_ttl: Session time-to-live in seconds (default: 90 seconds)
        """
        self.session_ttl = session_ttl
        logger.info("session_manager_initialized", ttl=session_ttl)

    def _generate_token(self) -> str:
        """
        Generate a cryptographically secure session token

        Returns:
            A URL-safe random token string
        """
        return secrets.token_urlsafe(32)

    def _session_key(self, token: str) -> str:
        """Generate Redis key for session data"""
        return f"session:{token}"

    def _user_sessions_key(self, user_id: int) -> str:
        """Generate Redis key for user's session set"""
        return f"user:{user_id}:sessions"

    async def create_session(self, user_profile: UserProfile) -> str:
        """
        Create a new session for a user

        Args:
            user_profile: The user profile to create a session for

        Returns:
            The session token
        """
        token = self._generate_token()

        # Prepare session data
        session_data = {
            "user_id": user_profile.id,
            "email": user_profile.email,
            "rol": user_profile.rol,
            "auth_user_id": user_profile.auth_user_id,
            "huesped_id": user_profile.huesped_id,
            "anfitrion_id": user_profile.anfitrion_id,
            "nombre": user_profile.nombre,
            "creado_en": user_profile.creado_en.isoformat() if user_profile.creado_en else None,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat()
        }

        # Store session in Redis with TTL
        session_key = self._session_key(token)
        await set_key(session_key, json.dumps(session_data), expire=self.session_ttl)

        # Add token to user's active sessions set
        user_sessions_key = self._user_sessions_key(user_profile.id)
        redis_client = await get_redis_client()
        await redis_client.sadd(user_sessions_key, token)

        # Set TTL on the user sessions set as well (cleanup)
        await redis_client.expire(user_sessions_key, self.session_ttl * 10)  # Keep set longer

        logger.info(
            "session_created",
            user_id=user_profile.id,
            email=user_profile.email,
            token_preview=token[:8] + "...",
            ttl=self.session_ttl
        )

        return token

    async def peek_session(self, token: str) -> Optional[UserProfile]:
        """
        Check if a session is valid WITHOUT refreshing its TTL

        Use this to check session validity without extending the session.
        Useful for validation before actions.

        Args:
            token: The session token to check

        Returns:
            UserProfile if session is valid, None if expired or invalid
        """
        session_key = self._session_key(token)
        session_data_str = await get_key(session_key)

        if not session_data_str:
            logger.debug("session_not_found", token_preview=token[:8] + "...")
            return None

        # Parse session data (but don't update or refresh)
        session_data = json.loads(session_data_str)

        logger.debug(
            "session_checked_without_refresh",
            user_id=session_data["user_id"],
            email=session_data["email"],
            token_preview=token[:8] + "..."
        )

        # Reconstruct UserProfile
        return UserProfile(
            id=session_data["user_id"],
            email=session_data["email"],
            rol=session_data["rol"],
            auth_user_id=session_data.get("auth_user_id"),
            huesped_id=session_data.get("huesped_id"),
            anfitrion_id=session_data.get("anfitrion_id"),
            nombre=session_data.get("nombre"),
            creado_en=datetime.fromisoformat(session_data["creado_en"]) if session_data.get("creado_en") else None
        )

    async def get_session(self, token: str) -> Optional[UserProfile]:
        """
        Retrieve and validate a session, refreshing its TTL

        This implements the sliding window pattern - each access refreshes the session.

        Args:
            token: The session token to validate

        Returns:
            UserProfile if session is valid, None if expired or invalid
        """
        session_key = self._session_key(token)
        session_data_str = await get_key(session_key)

        if not session_data_str:
            logger.debug("session_not_found", token_preview=token[:8] + "...")
            return None

        # Parse session data
        session_data = json.loads(session_data_str)

        # Update last activity timestamp
        session_data["last_activity"] = datetime.now().isoformat()

        # Refresh TTL (sliding window)
        await set_key(session_key, json.dumps(session_data), expire=self.session_ttl)

        logger.debug(
            "session_validated_and_refreshed",
            user_id=session_data["user_id"],
            email=session_data["email"],
            token_preview=token[:8] + "..."
        )

        # Reconstruct UserProfile
        return UserProfile(
            id=session_data["user_id"],
            email=session_data["email"],
            rol=session_data["rol"],
            auth_user_id=session_data.get("auth_user_id"),
            huesped_id=session_data.get("huesped_id"),
            anfitrion_id=session_data.get("anfitrion_id"),
            nombre=session_data.get("nombre"),
            creado_en=datetime.fromisoformat(session_data["creado_en"]) if session_data.get("creado_en") else None
        )

    async def invalidate_session(self, token: str) -> bool:
        """
        Invalidate (logout) a specific session

        Args:
            token: The session token to invalidate

        Returns:
            True if session was found and invalidated, False if not found
        """
        # First, get the session to find the user_id
        session_key = self._session_key(token)
        session_data_str = await get_key(session_key)

        if session_data_str:
            session_data = json.loads(session_data_str)
            user_id = session_data["user_id"]

            # Remove from user's sessions set
            user_sessions_key = self._user_sessions_key(user_id)
            redis_client = await get_redis_client()
            await redis_client.srem(user_sessions_key, token)

            logger.info(
                "session_invalidated",
                user_id=user_id,
                token_preview=token[:8] + "..."
            )

        # Delete the session
        deleted = await delete_key(session_key)
        return deleted > 0

    async def list_user_sessions(self, user_id: int) -> List[Dict[str, Any]]:
        """
        List all active sessions for a user

        Args:
            user_id: The user ID to list sessions for

        Returns:
            List of session information dictionaries
        """
        user_sessions_key = self._user_sessions_key(user_id)
        redis_client = await get_redis_client()

        # Get all session tokens for this user
        tokens = await redis_client.smembers(user_sessions_key)

        sessions = []
        tokens_to_remove = []

        for token_bytes in tokens:
            token = token_bytes.decode('utf-8') if isinstance(token_bytes, bytes) else token_bytes
            session_key = self._session_key(token)
            session_data_str = await get_key(session_key)

            if session_data_str:
                session_data = json.loads(session_data_str)
                sessions.append({
                    "token_preview": token[:8] + "...",
                    "created_at": session_data.get("created_at"),
                    "last_activity": session_data.get("last_activity"),
                    "email": session_data.get("email")
                })
            else:
                # Session expired but still in set - mark for cleanup
                tokens_to_remove.append(token)

        # Clean up expired tokens from the set
        if tokens_to_remove:
            for token in tokens_to_remove:
                await redis_client.srem(user_sessions_key, token)

            logger.debug(
                "cleaned_expired_sessions",
                user_id=user_id,
                count=len(tokens_to_remove)
            )

        logger.debug(
            "sessions_listed",
            user_id=user_id,
            active_count=len(sessions)
        )

        return sessions

    async def invalidate_all_user_sessions(self, user_id: int) -> int:
        """
        Invalidate all sessions for a user (logout from all devices)

        Args:
            user_id: The user ID to invalidate all sessions for

        Returns:
            Number of sessions invalidated
        """
        user_sessions_key = self._user_sessions_key(user_id)
        redis_client = await get_redis_client()

        # Get all session tokens
        tokens = await redis_client.smembers(user_sessions_key)

        count = 0
        for token_bytes in tokens:
            token = token_bytes.decode('utf-8') if isinstance(token_bytes, bytes) else token_bytes
            session_key = self._session_key(token)
            deleted = await delete_key(session_key)
            if deleted:
                count += 1

        # Clear the user sessions set
        await delete_key(user_sessions_key)

        logger.info(
            "all_sessions_invalidated",
            user_id=user_id,
            count=count
        )

        return count


# Global instance with default TTL (90 seconds)
session_manager = SessionManager(session_ttl=90)
