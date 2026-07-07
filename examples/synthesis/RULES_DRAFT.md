# Rules Draft

*Constraints discovered through failure — tag [DRAFT] or [INSTALLED]*

---

## R1 — API auth must use Authorization Bearer [DRAFT]

All `/api/*` routes require `Authorization: Bearer <jwt>`. Do not accept alternate header names.

> From session a1b2c3d4
