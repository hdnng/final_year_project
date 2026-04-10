# Backend Architecture - Technical Design Document

## System Overview

Production-grade FastAPI application with JWT authentication, rate limiting, and comprehensive security hardening.

```
┌─────────────────┐
│   Frontend      │  (React/Vue with cookies/headers)
└────────┬────────┘
         │
         ├─ Cookies: access_token, refresh_token
         └─ Headers: Authorization: Bearer <token>
         │
         ▼
┌─────────────────────────────────┐
│  FastAPI Application (main.py)  │
│  - CORS Middleware              │
│  - Error Handlers               │
└────────┬────────────────────────┘
         │
         ├─ /users router
         │   ├─ register (public, rate limited)
         │   ├─ login (public, rate limited)
         │   ├─ profile (protected)
         │   ├─ update (protected)
         │   ├─ change-password (protected)
         │   ├─ logout (protected → blacklist token)
         │   └─ refresh (public, needs refresh_token)
         │
         ├─ /cameras router → Protected
         ├─ /history router → Protected
         └─ /statistics router → Protected
         │
         ▼
┌──────────────────────────────────────────┐
│         Authentication Layer             │
├──────────────────────────────────────────┤
│ Dependencies:                            │
│  - get_current_user()                    │
│    • Check cookies/headers               │
│    • Verify JWT signature                │
│    • Check token blacklist               │
│    • Extract user_id → 401 on fail       │
│                                          │
│  - get_client_ip()                       │
│    • Handle X-Forwarded-For              │
│    • Support proxy configurations        │
│                                          │
│ Middleware/Services:                     │
│  - RateLimiter (singleton)               │
│    • Track attempts by IP                │
│    • Max 5 per 15 min per endpoint       │
│    • Automatic expiry cleanup            │
│                                          │
│  - TokenBlacklist (singleton)            │
│    • In-memory currently                 │
│    • Redis for production                │
└──────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│  Core Security Modules                   │
├──────────────────────────────────────────┤
│ auth.py:                                 │
│  - create_access_token()                 │
│    → (token, expiration_datetime)        │
│    → Type: "access", Exp: 1 hour         │
│                                          │
│  - create_refresh_token()                │
│    → (token, expiration_datetime)        │
│    → Type: "refresh", Exp: 7 days        │
│                                          │
│  - verify_token(token, token_type)       │
│    → Decode JWT, validate type           │
│    → Return payload or None              │
│                                          │
│ security.py:                             │
│  - hash_password()  → Bcrypt hash        │
│  - verify_password()→ Compare hashes     │
│  - get_cookie_settings()                 │
│    → Dynamic based on ENVIRONMENT        │
│                                          │
│ rate_limiter.py:                         │
│  - is_rate_limited(ip)                   │
│  - record_attempt(ip)                    │
│  - get_remaining_attempts(ip)            │
│  - get_reset_time(ip)                    │
│                                          │
│ token_blacklist.py:                      │
│  - add(token, expiration)                │
│  - is_blacklisted(token)                 │
│  - clear_expired()                       │
└──────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│  Business Logic Layer (CRUD)             │
├──────────────────────────────────────────┤
│ crud/user_crud.py:                       │
│  - create_user()                         │
│  - get_user_by_id()                      │
│  - get_user_by_email()                   │
│  - update_user()                         │
│                                          │
│ crud/session_crud.py                     │
│ crud/frame_crud.py                       │
│ crud/ai_result_crud.py                   │
│ crud/statistics_crud.py                  │
│                                          │
│ service/camera_service.py:               │
│  - Start/stop camera                     │
│  - Manage sessions                       │
│  - Process frames                        │
│                                          │
│ Transaction Pattern:                     │
│  - Create objects → db.flush()           │
│  - Do all operations                     │
│  - Single db.commit() at end             │
│  - On error → db.rollback()              │
└──────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│  Data Persistence Layer                  │
├──────────────────────────────────────────┤
│ PostgreSQL Database:                     │
│  - User (user_id, email, password, ...)  │
│  - Session (session_id, user_id, ...)    │
│  - Frame (frame_id, session_id, ...)     │
│  - AIResult (result_id, frame_id, ...)   │
│  - Statistics (stat_id, session_id, ...)│
│                                          │
│ SQLAlchemy ORM:                          │
│  - Models with relationships             │
│  - Automatic SQL generation              │
│  - Prevents SQL injection                │
│  - Supports outer joins for N+1 fix      │
└──────────────────────────────────────────┘
```

## Request Flow - Authenticated Endpoint

```
1. Client Request
   POST /users/profile
   Cookie: access_token=eyJhbGc...

2. FastAPI Dependency Injection
   - get_current_user(request, credentials)
     • Check request.cookies["access_token"]
     • Or Authorization header Bearer token

3. JWT Verification
   - Decode token with SECRET_KEY
   - Validate signature
   - Check token type = "access"
   - Extract user_id from payload

4. Token Blacklist Check
   - Is token in blacklist?
   - If blacklisted → 401 (logged out)
   - If expired in blacklist → cleanup

5. Return user_id
   - Dependency returns: int(user_id)
   - Route handler receives user_id

6. Endpoint Logic
   - Query database for user
   - Return response

7. Success Response
   HTTP 200 OK
   Content: {...user data...}
```

## Request Flow - Login with Rate Limiting

```
1. Client Request
   POST /users/login
   Body: {email, password}

2. Get Client IP
   - Check X-Forwarded-For header
   - Or request.client.host

3. Check Rate Limit
   - RateLimiter.is_rate_limited(ip)?
   - If yes → 429 Too Many Requests
   - Clean old attempts (>15 min)

4. Validate Credentials
   - Query user by email
   - If no user → record attempt
   - Verify password hash
   - If wrong → record attempt

5. Token Generation
   - Create access_token (1 hour)
   - Create refresh_token (7 days)
   - Both signed with SECRET_KEY

6. Set Cookies
   - response.set_cookie("access_token", ...)
   - response.set_cookie("refresh_token", ...)
   - httponly=True (JS can't access)
   - secure=(production only)
   - samesite="lax" (CSRF protection)

7. Reset Rate Limit
   - RateLimiter.reset_for_ip(ip)

8. Success Response
   HTTP 200 OK
   {
     "access_token": "eyJhbGc...",
     "refresh_token": "eyJhbGc...",
     "user_id": 123
   }
   + Cookies set
```

## Request Flow - Token Refresh

```
1. Client Request
   POST /users/refresh
   Cookie: refresh_token=eyJhbGc...

2. Extract Refresh Token
   - From cookies or Authorization header
   - If missing → 401

3. Check Token Blacklist
   - Was token revoked?
   - If yes → 401

4. Verify Refresh Token
   - Decode JWT
   - Validate signature
   - Check token type = "refresh"
   - Extract user_id

5. Create New Access Token
   - new_access_token, expiration = create_access_token()
   - Type: "access", Exp: 1 hour from now

6. Set Cookie
   - response.set_cookie("access_token", new_token)

7. Success Response
   HTTP 200 OK
   {
     "access_token": "eyJhbGc...",
     "user_id": 123
   }
```

## Security Design Decisions

### Why Separate Access & Refresh Tokens?
- **Access Token**: Short-lived (1 hour), low security risk
- **Refresh Token**: Long-lived (7 days), high security
- Compromise: Attacker gets limited time window with short token

### Why Token Blacklist Instead of Database Check?
- **In-memory**: Fast (no DB queries), good for development
- **Issue**: Lost on app restart
- **Solution**: Redis for production (persistent with TTL)
- **Status**: Currently using in-memory, ready for Redis migration

### Why Rate Limiting on Both Login & Register?
- **Login**: Prevent brute force attacks (password guessing)
- **Register**: Prevent spam/DoS (account creation flood)
- **Tracking**: Per-IP, per-endpoint for flexibility

### Why Not Store Tokens in Database?
- **Performance**: Every request would query DB
- **Scalability**: Doesn't scale with distributed sessions
- **Design**: Stateless is better for APIs
- **Tradeoff**: Use Redis for blacklist, not full token storage

### Why CORS Dynamic Configuration?
- **Development**: Need `["*"]` for localhost:3000, localhost:5173
- **Production**: Restrict to specific domains for security
- **Environment**: Use `.env` to switch between modes

### Why Bcrypt for Passwords?
- **Slow by design**: Takes ~100ms per hash (slows brute force)
- **Salt included**: Different hash for same password
- **Industry standard**: Used by major platforms
- **Alternatives**: Argon2 (newer, even slower), scrypt

## Environment Variables

```env
# Required
DATABASE_URL=postgresql://user:pass@host/db
SECRET_KEY=<min 32 random chars>

# Optional (defaults)
ENVIRONMENT=development          # or production
ALLOWED_ORIGINS=http://localhost:3000    # comma-separated
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True
```

## Error Codes Used

| Code | Meaning | Endpoint | When |
|------|---------|----------|------|
| 200 | Success | All | Successful operations |
| 400 | Bad Request | Create/Update | Invalid data format |
| 401 | Unauthorized | Protected routes | No token, invalid token, expired token |
| 403 | Forbidden | Protected routes | Valid token but insufficient permissions (RBAC ready) |
| 404 | Not Found | Get | Resource doesn't exist |
| 409 | Conflict | Register | Email already exists |
| 429 | Too Many Requests | Login/Register | Rate limit exceeded |
| 500 | Server Error | All | Unexpected error in processing |

## Future Enhancement Areas

### RBAC (Role-Based Access Control)
```python
# Structure ready for:
user.role = "admin" | "teacher" | "student"

@router.get("/admin/only")
def admin_only(user: User = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(403, "Admin only")
```

### Redis Integration
```python
# Replace in-memory with Redis:
TokenBlacklist.redis_client = redis.Redis()
RateLimiter.redis_client = redis.Redis()
```

### API Versioning
```
/api/v1/users/login
/api/v1/cameras/start
/api/v2/users/login (future updates)
```

### Security Headers Middleware
```python
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["yourdomain.com"]
)
# Also add: X-Frame-Options, X-Content-Type-Options, CSP
```

## Performance Considerations

- **JWT**: Stateless validation (~1ms per request)
- **Rate Limiting**: O(1) lookup, periodic cleanup
- **DB Queries**: Single commit pattern prevents N+1
- **Caching**: Ready for Redis caching layer
- **Load**: Tested with concurrent users (deployment dependent)

## Testing Strategy

1. **Unit Tests**: Validate individual functions
2. **Integration Tests**: Test endpoints with DB
3. **Security Tests**: Rate limiting, authentication flows
4. **Load Tests**: Concurrent user simulation
5. **Security Audit**: Code review, OWASP compliance

See `backend/tests/test_security.py` for example suite.
