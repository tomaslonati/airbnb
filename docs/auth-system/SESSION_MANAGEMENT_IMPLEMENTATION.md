# Redis Session Management Implementation

## Overview

Successfully implemented Redis-based session management for the Airbnb CLI authentication system. Sessions are now persistent, have automatic expiration, and support auto-refresh on activity (sliding window pattern).

## Implementation Summary

### 🎯 Requirements Met

- ✅ **Session TTL**: 90 seconds (1.5 minutes) as requested
- ✅ **Auto-refresh**: Sliding window - each activity extends session by 90s
- ✅ **Redis as source of truth**: All session validation checks Redis first
- ✅ **Token storage**: Global variable `current_session_token` in CLI
- ✅ **List active sessions**: CLI command to view all user sessions

## Files Created/Modified

### New Files

1. **`services/session.py`** (~250 lines)
   - `SessionManager` class with Redis integration
   - Secure token generation using `secrets.token_urlsafe(32)`
   - Session CRUD operations (create, get, invalidate, list)
   - Auto-refresh logic (sliding window TTL)
   - Support for multi-session tracking per user

2. **`tests/domain/auth-system/test_session_management.py`** (~280 lines)
   - Comprehensive test suite for session management
   - Tests for: creation, retrieval, expiration, auto-refresh, invalidation, listing
   - Integration tests with AuthService
   - Session restore tests

3. **`tests/domain/auth-system/test_session_manual.py`** (~100 lines)
   - Manual testing script for end-to-end session flow
   - Demonstrates all session features

4. **`docs/auth-system/SESSION_MANAGEMENT_IMPLEMENTATION.md`** (this file)
   - Implementation documentation

### Modified Files

1. **`services/auth.py`**
   - Added `current_session_token` attribute to `AuthService`
   - Added `session_token` field to `AuthResult` dataclass
   - Updated `login()` to create Redis session and return token
   - Updated `logout()` to invalidate Redis session
   - Added `restore_session(token)` method
   - Added `validate_session()` method (checks Redis and refreshes TTL)
   - Added `list_sessions()` method
   - Lazy-loaded SessionManager to avoid circular imports

2. **`cli/commands.py`**
   - Added global variable `current_session_token`
   - Updated `interactive_mode()` to attempt session restoration on startup
   - Added session validation before each command (auto-refresh)
   - Updated `handle_login()` to store session token
   - Updated `handle_logout()` to clear session token
   - Added "Ver sesiones activas" menu option
   - Added `show_active_sessions()` function

## Architecture

### Redis Key Schema

```
session:{token}              -> JSON session data (TTL: 90s)
user:{user_id}:sessions      -> SET of active session tokens
```

### Session Data Structure

```json
{
  "user_id": 1,
  "email": "user@example.com",
  "rol": "HUESPED",
  "auth_user_id": null,
  "huesped_id": 123,
  "anfitrion_id": null,
  "nombre": "User Name",
  "creado_en": "2025-11-16T15:00:00",
  "created_at": "2025-11-16T15:00:00",
  "last_activity": "2025-11-16T15:01:30"
}
```

### Session Flow

```
┌─────────────────────────────────────────────────────────────┐
│                      USER LOGIN                             │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  1. AuthService.login(email, password)                      │
│  2. Validate credentials (PostgreSQL)                       │
│  3. SessionManager.create_session(user_profile)             │
│     - Generate secure token (secrets.token_urlsafe)         │
│     - Store in Redis: session:{token} (TTL: 90s)            │
│     - Add to user session set: user:{id}:sessions           │
│  4. Return AuthResult with session_token                    │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  CLI stores token in current_session_token global var       │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              EVERY COMMAND EXECUTION                        │
│  1. AuthService.validate_session()                          │
│     - Check if current_session_token exists                 │
│     - SessionManager.get_session(token)                     │
│     - Redis GET session:{token}                             │
│     - If valid: Update last_activity & RESET TTL to 90s     │
│     - Return UserProfile or None                            │
│  2. If valid: Execute command                               │
│  3. If invalid: Prompt re-login                             │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              SESSION RESTORATION (CLI RESTART)              │
│  1. Check if current_session_token exists                   │
│  2. AuthService.restore_session(token)                      │
│     - Same as validate_session()                            │
│     - Refreshes TTL if valid                                │
│  3. If successful: User stays logged in                     │
│  4. If failed: Prompt login                                 │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    USER LOGOUT                              │
│  1. AuthService.logout()                                    │
│  2. SessionManager.invalidate_session(token)                │
│     - Redis DELETE session:{token}                          │
│     - Remove from user:{id}:sessions                        │
│  3. Clear current_session_token                             │
└─────────────────────────────────────────────────────────────┘
```

## Key Features

### 1. Auto-Refresh (Sliding Window)

Every time a session is accessed via `get_session()` or `validate_session()`:
- The `last_activity` timestamp is updated
- The Redis TTL is reset to 90 seconds
- This creates a sliding window: session stays alive with regular use
- 90 seconds of inactivity → automatic expiration

### 2. Multi-Session Support

Users can have multiple active sessions simultaneously:
- Each login creates a new session token
- Sessions are tracked in `user:{user_id}:sessions` Redis set
- List all active sessions via `auth_service.list_sessions()`
- Useful for multi-device scenarios (though CLI is single device)

### 3. Secure Token Generation

```python
token = secrets.token_urlsafe(32)  # Cryptographically secure
# Example: "3ruCWU73_4vX5yqZ8mN9kL2pQ1rT7sU6"
```

### 4. Session Validation Before Every Command

In `cli/commands.py`, before executing any command:
```python
is_valid = await auth_service.validate_session()
if not is_valid:
    # Session expired - prompt re-login
    current_session_token = None
    current_user_session = None
```

### 5. List Active Sessions

Users can view all their active sessions:
```
🔑 SESIONES ACTIVAS
==================================================
Total de sesiones activas: 2

Sesión 1:
   🔑 Token: 3ruCWU73...
   📧 Email: user@example.com
   ⏰ Creada: 2025-11-16T15:00:00
   🕒 Última actividad: 2025-11-16T15:01:30

Sesión 2:
   🔑 Token: Vlys-yjw...
   📧 Email: user@example.com
   ⏰ Creada: 2025-11-16T14:50:00
   🕒 Última actividad: 2025-11-16T14:51:00
```

## Testing

### Automated Tests

Run the test suite:
```bash
python3 -m pytest tests/domain/auth-system/test_session_management.py -v
```

Test coverage:
- ✅ `test_create_session` - Session creation
- ✅ `test_get_session` - Session retrieval
- ✅ `test_session_expiration` - TTL expiration
- ✅ `test_session_auto_refresh` - Sliding window refresh
- ✅ `test_invalidate_session` - Logout
- ✅ `test_list_user_sessions` - List all sessions
- ✅ `test_invalidate_all_user_sessions` - Logout all
- ✅ `test_auth_service_session_integration` - Full AuthService flow
- ✅ `test_session_restore` - Session restoration

### Manual Testing

Run the manual test script:
```bash
python3 tests/domain/auth-system/test_session_manual.py
```

This script demonstrates:
1. Login and session creation
2. Session validation
3. Listing active sessions
4. Auto-refresh (sliding window)
5. Session expiration after inactivity
6. Attempt to restore expired session

### Interactive CLI Testing

1. Start the CLI:
   ```bash
   python3 main.py
   ```

2. Login with credentials
   - Note the "Sesión creada (TTL: 90 segundos con auto-refresh)" message

3. Use the menu options within 90 seconds
   - Each action refreshes the session TTL

4. Select "Ver sesiones activas" to see active sessions

5. Wait 90+ seconds without activity
   - You'll see "Tu sesión ha expirado" message
   - You'll be prompted to login again

6. Login again to create a new session

## Configuration

### Session TTL

Configured in `services/session.py`:
```python
# Global instance with 90 second TTL
session_manager = SessionManager(session_ttl=90)
```

To change the TTL, modify this value. Common options:
- `90` - 1.5 minutes (current setting)
- `300` - 5 minutes
- `3600` - 1 hour
- `86400` - 24 hours

### Redis Configuration

Configured via environment variables in `.env`:
```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_USERNAME=default
REDIS_PASSWORD=your_password
REDIS_URL=redis://localhost:6379
```

## Security Considerations

1. **Token Security**
   - Uses `secrets.token_urlsafe(32)` for cryptographically secure tokens
   - 32 bytes = 256 bits of entropy
   - URL-safe encoding

2. **Session Expiration**
   - Automatic expiration after 90 seconds of inactivity
   - No manual cleanup needed (Redis TTL handles it)

3. **Token Storage**
   - Currently stored in global variable (CLI session)
   - For production: consider storing in secure file with restricted permissions
   - Future enhancement: encrypt tokens at rest

4. **No Password Storage**
   - Sessions only store user profile data, not passwords
   - Password verification happens only at login

5. **Session Invalidation**
   - Logout properly invalidates Redis session
   - Token becomes immediately unusable

## Performance

### Redis Operations

All session operations are O(1):
- `create_session`: 2 Redis commands (SET + SADD)
- `get_session`: 1 Redis command (GET)
- `invalidate_session`: 2 Redis commands (GET + DEL + SREM)
- `list_user_sessions`: O(n) where n = number of user sessions

### Memory Usage

Per session:
```
session:{token} key: ~300 bytes
user:{id}:sessions entry: ~50 bytes
Total: ~350 bytes per session
```

For 1000 concurrent sessions: ~350 KB

### Network Latency

All Redis operations are async and non-blocking:
- Typical Redis GET/SET: < 1ms on local network
- Acceptable for CLI use case

## Future Enhancements

Potential improvements for production:

1. **Persistent Token Storage**
   - Store session token in `~/.airbnb/session` file
   - Auto-restore on CLI restart without global variable

2. **Device/IP Tracking**
   - Track which device/IP each session belongs to
   - Show device info in session list

3. **Session Activity Log**
   - Store session activities in Cassandra for audit
   - Track what commands were executed in each session

4. **Rate Limiting**
   - Use Redis counters to prevent brute force login attempts
   - Limit login attempts per email/IP

5. **JWT Tokens**
   - Implement JWT tokens for stateless auth
   - Include refresh token mechanism

6. **2FA Support**
   - Require 2FA for sensitive operations
   - Store 2FA status in session

7. **Session Analytics**
   - Track session duration, command frequency
   - Store analytics in MongoDB

8. **Graceful Degradation**
   - Fallback to in-memory sessions if Redis is unavailable
   - Show warning to user about session limitations

## Troubleshooting

### "Session expired" immediately after login

Check Redis TTL:
```python
# In services/session.py
session_manager = SessionManager(session_ttl=90)  # Increase if needed
```

### Sessions not persisting across CLI restarts

Currently expected - sessions are stored in global variables. To persist:
1. Implement file-based token storage
2. Load token on CLI startup
3. Restore session from token

### Cannot connect to Redis

Check Redis configuration:
```bash
# Test Redis connection
redis-cli ping
# Should return: PONG

# Check environment variables
cat .env | grep REDIS
```

### Tests failing

Ensure Redis is running:
```bash
# Start Redis
redis-server

# Or if using Docker
docker run -d -p 6379:6379 redis
```

## Conclusion

Redis session management is now fully implemented and tested. The system provides:
- ✅ Persistent sessions in Redis
- ✅ 90-second TTL with auto-refresh
- ✅ Session validation before every command
- ✅ Multi-session support
- ✅ List active sessions
- ✅ Secure token generation
- ✅ Comprehensive test coverage

The implementation follows best practices and is ready for use in the CLI application.
