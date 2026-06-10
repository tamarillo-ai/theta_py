from __future__ import annotations

import shutil
from pathlib import Path

import pytest


def _binary_available() -> bool:
    from theta_py.runner import ThetaBinaryNotFoundError, _resolve_binary

    try:
        _resolve_binary(auto_install=False)
        return True
    except (ThetaBinaryNotFoundError, FileNotFoundError):
        return shutil.which("theta") is not None


pytestmark = pytest.mark.skipif(
    not _binary_available(),
    reason="theta binary not resolvable",
)


@pytest.fixture
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("THETA_DATA_DIR", str(data_dir))
    monkeypatch.delenv("THETA_CONFIG_DIR", raising=False)

    from theta_py._generated import verbs

    verbs._theta = None
    yield tmp_path
    verbs._theta = None


@pytest.fixture
def initialized(workspace: Path) -> Path:
    from theta_py import theta

    theta.init(name="test-agent")
    return workspace
