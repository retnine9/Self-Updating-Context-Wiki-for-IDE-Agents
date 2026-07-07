"""Pytest config + shared fixtures for context wiki tests."""
from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

FIXTURES = REPO_ROOT / "tests" / "fixtures" / "transcripts"


def _reload_paths():
    """Re-import lib.paths so module-level constants pick up current env vars."""
    import lib.paths
    importlib.reload(lib.paths)
    # Re-bind names that other modules captured at import time
    import scripts.extract_context as ex
    importlib.reload(ex)
    import scripts.update_wiki as uw
    importlib.reload(uw)
    import scripts.doctor as doc
    importlib.reload(doc)
    import lib.platform as plat
    plat.reset_platform_cache()
    return lib.paths


@pytest.fixture
def isolated_context(tmp_path, monkeypatch):
    """Point the wiki at a temp data dir + repo-root runtime, fresh platform cache."""
    monkeypatch.setenv("CONTEXT_WIKI_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("WIKI_HOME", str(REPO_ROOT))
    monkeypatch.delenv("WIKI_PLATFORM", raising=False)
    paths = _reload_paths()
    (tmp_path / "data" / "sessions").mkdir(parents=True, exist_ok=True)
    (tmp_path / "data" / "extracts").mkdir(parents=True, exist_ok=True)
    (tmp_path / "data" / "synthesis").mkdir(parents=True, exist_ok=True)
    return paths


@pytest.fixture
def isolated_home(tmp_path, monkeypatch):
    """Redirect Path.home() to a tmp dir (for install/doctor subprocess tests)."""
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("CONTEXT_WIKI_DIR", raising=False)
    monkeypatch.delenv("WIKI_HOME", raising=False)
    monkeypatch.delenv("WIKI_PLATFORM", raising=False)
    return tmp_path
