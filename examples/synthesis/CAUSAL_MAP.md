# Causal Map

*Example wiki — fictional task-tracker API project*

---

## 1. Wrong Auth Header → Universal 401 on /api/tasks

**Problem:** All API requests returned 401 despite valid tokens.

**First appearance:** `a1b2c3d4` (2026-06-10)

**Root cause:** Middleware expected `Authorization: Bearer` but clients sent `X-Api-Token`.

**Resolution:** Aligned middleware with OpenAPI Bearer scheme; added regression tests.

---

## 2. Shared Test DB → Flaky Pagination Test in CI

**Problem:** `test_list_pagination` failed intermittently in CI, passed locally.

**First appearance:** `c9d0e1f2` (2026-06-20) — pending extract

**Root cause:** Parallel CI jobs shared seed data; row counts were non-deterministic.

**Resolution:** `db_isolation` fixture in `conftest.py` with factory-created rows.
