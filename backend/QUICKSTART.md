# 🔐 Backend Security - Quick Reference

## What's Been Secured ✅

### Authentication Flow
```
1. User registers → Validated email/password → Bcrypt hash → Database
2. User login → Rate limited (5 tries/15min) → JWT tokens → Cookies
3. Access token (1 hour) → Refresh token (7 days) → Both in cookies
4. Protected routes → Validate JWT → Extract user_id → Allow/Deny
5. Logout → Add token to blacklist → Clear cookies
```

### Rate Limiting
```
Login: 5 attempts per 15 minutes per IP → 429 on excess
Register: 5 attempts per 15 minutes per IP → 429 on excess
Per-IP tracking with automatic expiry cleanup
```

### Protected Endpoints
```
✅ /users/profile                (GET)
✅ /users/update                 (PUT)
✅ /users/change-password        (PUT)
✅ /users/logout                 (POST)
✅ /users/refresh                (POST) - uses refresh_token
✅ /cameras/start                (POST)
✅ /cameras/stop                 (POST)
✅ /cameras/video_feed           (GET)
✅ /cameras/frames/{id}          (GET)
✅ /cameras/sessions             (GET)
✅ /history/sessions             (GET)
✅ /history/summary              (GET)
✅ /history/session/{id}         (GET)
✅ /statistics/daily             (GET)
✅ /statistics/by-date           (GET)
✅ /statistics/weekly            (GET)
✅ /statistics/summary           (GET)

❌ /users/register               (Public - rate limited)
❌ /users/login                  (Public - rate limited)
❌ /cameras/list                 (Public)
❌ /health                       (Public)
```

## Quick Start

### 1. Run Tests
```bash
cd backend
python tests/test_security.py
```

### 2. Start API
```bash
python -m uvicorn main:app --reload
```

### 3. Test Endpoints

**Register:**
```bash
curl -X POST http://localhost:8000/users/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Pass123","full_name":"Test"}'
```

**Login:**
```bash
curl -X POST http://localhost:8000/users/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Pass123"}' \
  -c cookies.txt
```

**Protected Route:**
```bash
curl -X GET http://localhost:8000/users/profile -b cookies.txt
```

**Refresh Token:**
```bash
curl -X POST http://localhost:8000/users/refresh -b cookies.txt
```

**Logout:**
```bash
curl -X POST http://localhost:8000/users/logout -b cookies.txt
```

## Production Checklist

- [ ] Update SECRET_KEY in .env to strong random string
- [ ] Set ENVIRONMENT=production
- [ ] Configure ALLOWED_ORIGINS for frontend domain(s)
- [ ] Test with HTTPS/SSL enabled
- [ ] Set up database backups
- [ ] Configure proper logging system
- [ ] Set up monitoring/alerting
- [ ] Run security test suite
- [ ] Plan for Redis token blacklist migration
- [ ] Document API for frontend team
- [ ] Load test with concurrent users
- [ ] Review all logs and errors

## Configuration Files

### .env
```
DATABASE_URL=postgresql://...
SECRET_KEY=your-secret-key
ENVIRONMENT=development (or production)
ALLOWED_ORIGINS=http://localhost:3000
```

### Logging
- Logs to: backend/logs/YYYYMMDD.log
- Console output with timestamps
- User ID/IP tracked in audit

## Key Files

| File | Purpose |
|------|---------|
| core/auth.py | JWT token creation/verification |
| core/security.py | Password hashing, cookie settings |
| core/rate_limiter.py | Rate limiting enforcement |
| core/dependencies.py | JWT validation, IP extraction |
| core/token_blacklist.py | Token revocation tracking |
| api/router/user_router.py | Auth endpoints (register/login/logout) |
| main.py | App setup, CORS, middleware |

## Monitoring Metrics

Track these for security:
- Failed login attempts per IP
- Rate limit blocks per time period
- Token refresh frequency by user
- Failed authentication errors
- Logout events
- Registration attempts

## Common Issues & Solutions

**Rate Limit Hit (429)?**
- Try again after 15 minutes
- Check IP address (may be proxied)
- Frontend should show user-friendly message

**Token Expired?**
- Call POST /users/refresh with valid refresh_token
- Will return new access_token

**Token Blacklisted After Logout?**
- This is expected - logout invalidates token
- User must login again

**Cookie Not Working?**
- Ensure frontend sends `credentials: 'include'` in fetch
- Check cookie domain matches
- Verify httponly not blocking JavaScript access

**CORS Error?**
- Development: Should allow `*` by default
- Production: Check ALLOWED_ORIGINS in .env
- Verify frontend domain matches exactly

## Next Steps

1. ✅ Current: Production-grade security complete
2. 📋 Optional: Add RBAC (Admin/Teacher/Student roles)
3. 📧 Optional: Password reset with email verification
4. 🔑 Optional: Redis for production token blacklist
5. 📱 Optional: 2FA support
