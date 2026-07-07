# Development History

*Major architectural decisions — chronological*

---

## 2026-06-10 — Standardize Bearer auth

Aligned JWT middleware with OpenAPI. Session `a1b2c3d4`.

## 2026-06-15 — JWT on all /api routes

Added `auth/jwt.py`, HS256, env-based secret. Refresh tokens deferred. Session `e5f6a7b8`.

## 2026-06-20 — CI test isolation

Introduced `db_isolation` fixture for integration tests. Session `c9d0e1f2`.
