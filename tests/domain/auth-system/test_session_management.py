"""
Test suite for Redis session management system

Tests the SessionManager and AuthService session integration.
"""

import pytest
import asyncio
from datetime import datetime
from services.auth import AuthService, UserProfile
from services.session import SessionManager
from db.redisdb import get_client as get_redis_client, delete_key


@pytest.fixture
def session_manager():
    """Fixture to provide a session manager with 5 second TTL for testing"""
    manager = SessionManager(session_ttl=5)  # 5 seconds for faster testing
    return manager


@pytest.fixture
def auth_service():
    """Fixture to provide an auth service"""
    service = AuthService()
    return service


@pytest.fixture
def sample_user_profile():
    """Fixture to provide a sample user profile"""
    return UserProfile(
        id=999,
        email="test-session@example.com",
        rol="HUESPED",
        auth_user_id=None,
        creado_en=datetime.now(),
        huesped_id=888,
        anfitrion_id=None,
        nombre="Test User Session"
    )


@pytest.mark.asyncio
async def test_create_session(session_manager, sample_user_profile):
    """Test creating a new session"""
    token = await session_manager.create_session(sample_user_profile)

    assert token is not None
    assert len(token) > 0
    print(f"✅ Session created with token: {token[:8]}...")

    # Cleanup
    await session_manager.invalidate_session(token)


@pytest.mark.asyncio
async def test_get_session(session_manager, sample_user_profile):
    """Test retrieving a valid session"""
    # Create a session
    token = await session_manager.create_session(sample_user_profile)

    # Retrieve the session
    user_profile = await session_manager.get_session(token)

    assert user_profile is not None
    assert user_profile.id == sample_user_profile.id
    assert user_profile.email == sample_user_profile.email
    assert user_profile.rol == sample_user_profile.rol
    print(f"✅ Session retrieved for user: {user_profile.email}")

    # Cleanup
    await session_manager.invalidate_session(token)


@pytest.mark.asyncio
async def test_session_expiration(session_manager, sample_user_profile):
    """Test that sessions expire after TTL"""
    # Create a session with 5 second TTL
    token = await session_manager.create_session(sample_user_profile)

    # Verify session exists
    user_profile = await session_manager.get_session(token)
    assert user_profile is not None
    print(f"✅ Session exists initially")

    # Wait for expiration (5 seconds + 1 second buffer)
    print("⏳ Waiting 6 seconds for session to expire...")
    await asyncio.sleep(6)

    # Try to get expired session
    expired_user = await session_manager.get_session(token)
    assert expired_user is None
    print(f"✅ Session expired as expected")


@pytest.mark.asyncio
async def test_session_auto_refresh(session_manager, sample_user_profile):
    """Test that session TTL is refreshed on access (sliding window)"""
    # Create a session with 5 second TTL
    token = await session_manager.create_session(sample_user_profile)

    # Access the session after 3 seconds (before expiration)
    print("⏳ Waiting 3 seconds, then accessing session...")
    await asyncio.sleep(3)
    user_profile = await session_manager.get_session(token)
    assert user_profile is not None
    print(f"✅ Session still valid after 3 seconds")

    # Wait another 3 seconds (total 6 seconds from creation, but 3 from last access)
    print("⏳ Waiting another 3 seconds...")
    await asyncio.sleep(3)
    user_profile = await session_manager.get_session(token)
    assert user_profile is not None
    print(f"✅ Session still valid due to auto-refresh (sliding window)")

    # Cleanup
    await session_manager.invalidate_session(token)


@pytest.mark.asyncio
async def test_invalidate_session(session_manager, sample_user_profile):
    """Test invalidating (logging out) a session"""
    # Create a session
    token = await session_manager.create_session(sample_user_profile)

    # Verify it exists
    user_profile = await session_manager.get_session(token)
    assert user_profile is not None

    # Invalidate the session
    result = await session_manager.invalidate_session(token)
    assert result is True
    print(f"✅ Session invalidated successfully")

    # Verify it's gone
    user_profile = await session_manager.get_session(token)
    assert user_profile is None
    print(f"✅ Session no longer accessible after invalidation")


@pytest.mark.asyncio
async def test_list_user_sessions(session_manager, sample_user_profile):
    """Test listing all active sessions for a user"""
    # Create multiple sessions for the same user
    token1 = await session_manager.create_session(sample_user_profile)
    await asyncio.sleep(0.5)  # Small delay to differentiate timestamps
    token2 = await session_manager.create_session(sample_user_profile)

    # List sessions
    sessions = await session_manager.list_user_sessions(sample_user_profile.id)

    assert len(sessions) == 2
    assert any(s['token_preview'] == token1[:8] + "..." for s in sessions)
    assert any(s['token_preview'] == token2[:8] + "..." for s in sessions)
    print(f"✅ Found {len(sessions)} active sessions for user")

    # Cleanup
    await session_manager.invalidate_session(token1)
    await session_manager.invalidate_session(token2)


@pytest.mark.asyncio
async def test_invalidate_all_user_sessions(session_manager, sample_user_profile):
    """Test invalidating all sessions for a user"""
    # Create multiple sessions
    token1 = await session_manager.create_session(sample_user_profile)
    token2 = await session_manager.create_session(sample_user_profile)
    token3 = await session_manager.create_session(sample_user_profile)

    # Invalidate all
    count = await session_manager.invalidate_all_user_sessions(sample_user_profile.id)
    assert count == 3
    print(f"✅ Invalidated {count} sessions")

    # Verify all are gone
    user1 = await session_manager.get_session(token1)
    user2 = await session_manager.get_session(token2)
    user3 = await session_manager.get_session(token3)
    assert user1 is None
    assert user2 is None
    assert user3 is None
    print(f"✅ All sessions successfully invalidated")


@pytest.mark.asyncio
async def test_auth_service_session_integration(auth_service):
    """Test AuthService integration with session management"""
    # Test login creates a session
    result = await auth_service.login("test@example.com", "password")

    if result.success:
        assert result.session_token is not None
        assert len(result.session_token) > 0
        print(f"✅ Login created session token: {result.session_token[:8]}...")

        # Test session validation
        is_valid = await auth_service.validate_session()
        assert is_valid is True
        print(f"✅ Session validated successfully")

        # Test logout invalidates session
        logout_result = await auth_service.logout()
        assert logout_result.success is True
        print(f"✅ Logout successful")

        # Session should be invalid after logout
        is_valid_after = await auth_service.validate_session()
        assert is_valid_after is False
        print(f"✅ Session invalid after logout")
    else:
        print(f"⚠️  Login failed (user may not exist): {result.message}")
        pytest.skip("Test user does not exist in database")


@pytest.mark.asyncio
async def test_session_restore(auth_service):
    """Test restoring a session from a stored token"""
    # Login to get a session token
    result = await auth_service.login("test@example.com", "password")

    if result.success:
        token = result.session_token
        original_email = result.user_profile.email

        # Simulate CLI restart by creating a new auth service instance
        new_auth_service = AuthService()

        # Restore session from token
        restore_result = await new_auth_service.restore_session(token)

        assert restore_result.success is True
        assert restore_result.user_profile.email == original_email
        print(f"✅ Session restored for: {restore_result.user_profile.email}")

        # Cleanup
        await new_auth_service.logout()
        if hasattr(new_auth_service, 'neo4j_user_service'):
            await new_auth_service.neo4j_user_service.close()
    else:
        print(f"⚠️  Login failed (user may not exist): {result.message}")
        pytest.skip("Test user does not exist in database")


if __name__ == "__main__":
    print("🧪 Running Session Management Tests")
    print("=" * 50)
    pytest.main([__file__, "-v", "-s"])
