"""
Manual test script for Redis session management

This script demonstrates the complete session flow:
1. Login and get session token
2. Validate session
3. List active sessions
4. Wait for expiration
5. Check expired session
"""

import asyncio
from services.auth import AuthService


async def main():
    print("=" * 60)
    print("🧪 MANUAL SESSION MANAGEMENT TEST")
    print("=" * 60)

    auth_service = AuthService()

    # Step 1: Login
    print("\n📝 Step 1: Logging in as test@example.com...")
    result = await auth_service.login("test@example.com", "password")

    if not result.success:
        print(f"❌ Login failed: {result.message}")
        print("⚠️  Make sure test@example.com user exists in the database")
        return

    print(f"✅ {result.message}")
    print(f"🔑 Session Token: {result.session_token[:16]}...")
    print(f"👤 User: {result.user_profile.nombre} ({result.user_profile.email})")
    print(f"⏱️  Session TTL: 90 seconds with auto-refresh")

    # Step 2: Validate session
    print("\n📝 Step 2: Validating session...")
    is_valid = await auth_service.validate_session()
    if is_valid:
        print("✅ Session is valid")
    else:
        print("❌ Session is invalid")

    # Step 3: List active sessions
    print("\n📝 Step 3: Listing active sessions...")
    sessions = await auth_service.list_sessions()
    if sessions:
        print(f"✅ Found {len(sessions)} active session(s):")
        for i, session in enumerate(sessions, 1):
            print(f"   Session {i}:")
            print(f"   - Token: {session.get('token_preview')}")
            print(f"   - Created: {session.get('created_at')}")
            print(f"   - Last Activity: {session.get('last_activity')}")
    else:
        print("❌ No active sessions found")

    # Step 4: Test auto-refresh (sliding window)
    print("\n📝 Step 4: Testing auto-refresh (sliding window)...")
    print("⏳ Waiting 60 seconds and accessing session every 30 seconds...")

    for i in range(2):
        await asyncio.sleep(30)
        is_valid = await auth_service.validate_session()
        print(f"   After {(i+1)*30}s: Session {'valid ✅' if is_valid else 'expired ❌'}")
        if is_valid:
            print(f"   (TTL refreshed - session extended by 90s from now)")

    # Step 5: Wait for expiration
    print("\n📝 Step 5: Testing session expiration...")
    print("⏳ Waiting 100 seconds without activity (session should expire)...")
    await asyncio.sleep(100)

    is_valid = await auth_service.validate_session()
    if not is_valid:
        print("✅ Session expired as expected after 90s of inactivity")
    else:
        print("❌ Session still valid (unexpected)")

    # Step 6: Try to restore expired session
    print("\n📝 Step 6: Attempting to restore expired session...")
    restore_result = await auth_service.restore_session(result.session_token)
    if restore_result.success:
        print(f"❌ Restored expired session (unexpected)")
    else:
        print(f"✅ Cannot restore expired session: {restore_result.message}")

    # Cleanup
    print("\n📝 Cleanup: Logging out...")
    await auth_service.logout()
    print("✅ Logged out successfully")

    if hasattr(auth_service, 'neo4j_user_service'):
        await auth_service.neo4j_user_service.close()

    print("\n" + "=" * 60)
    print("✅ ALL MANUAL TESTS COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
