# Error Reference

*Example wiki — fictional task-tracker API project*

---

## Auth

### 401 on all /api/tasks requests

**Signature:** Valid token present but every request returns 401.

**Root cause:** Header name mismatch (`X-Api-Token` vs `Authorization: Bearer`).

**Fix:** `middleware/auth.py` — read Bearer token. Session `a1b2c3d4`.

**Status:** RESOLVED

---

## CI / Tests

### Intermittent failure: test_list_pagination

**Signature:** CI fails on pagination count assertion; local pass.

**Root cause:** Shared database seeds across parallel jobs.

**Fix:** `conftest.py` `db_isolation` fixture. Session `c9d0e1f2`.

**Status:** RESOLVED (pending extract sync)
