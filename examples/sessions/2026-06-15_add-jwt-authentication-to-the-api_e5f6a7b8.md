---
session: e5f6a7b8
date: 2026-06-15
title: Add JWT authentication to the API
era: post-3.0
---

## User

We need JWT auth on all /api/* routes. Use HS256 and load the secret from env.

## Assistant

I'll add `auth/jwt.py` with encode/decode helpers, wire middleware, and document `JWT_SECRET` in README. Refresh tokens are out of scope for now.

## User

Ship it without refresh tokens. Update the OpenAPI spec too.

## Assistant

Done. Middleware rejects expired tokens with 401 and malformed tokens with 403. OpenAPI documents the Bearer scheme.
