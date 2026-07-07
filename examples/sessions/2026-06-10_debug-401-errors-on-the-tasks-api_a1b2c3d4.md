---
session: a1b2c3d4
date: 2026-06-10
title: Debug 401 errors on the tasks API
era: post-3.0
---

## User

The GET /api/tasks endpoint returns 401 for all requests even with a valid token. Can you help debug?

## Assistant

I'll trace the auth middleware. The JWT validator is reading `Authorization` but the test client sends `X-Api-Token`. We should align on the `Authorization: Bearer` header per the OpenAPI spec.

## User

Fix it and add a regression test.

## Assistant

Updated `middleware/auth.py` to accept Bearer tokens. Added `tests/test_auth.py` with a happy-path and missing-header case. All 42 tests pass locally.
