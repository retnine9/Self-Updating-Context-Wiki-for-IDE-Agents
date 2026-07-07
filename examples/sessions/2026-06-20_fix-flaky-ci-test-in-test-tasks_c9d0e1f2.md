---
session: c9d0e1f2
date: 2026-06-20
title: Fix flaky CI test in test_tasks
era: post-3.0
---

## User

CI fails intermittently on test_tasks::test_list_pagination. Passes locally.

## Assistant

The test assumes exactly 10 seed rows but parallel jobs share the test database. I'll isolate with a transaction rollback fixture and use factory-created rows instead of relying on seeds.

## User

Good. Make sure CI uses the same fixture.

## Assistant

Updated `conftest.py` with `db_isolation` fixture applied to integration tests. CI config unchanged — pytest picks up conftest automatically. Three consecutive CI runs green.
