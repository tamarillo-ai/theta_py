from __future__ import annotations

import subprocess

import pytest

from theta_py.runner import ThetaError, _resolve_binary


def test_resolve_binary_raises_when_missing(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.delenv("THETA_BIN", raising=False)
    monkeypatch.setenv("PATH", str(tmp_path))
    monkeypatch.setattr("theta_py.runner._scripts_dir", lambda: tmp_path / "empty")
    with pytest.raises(FileNotFoundError):
        _resolve_binary(auto_install=False)


@pytest.mark.network
def test_resolve_binary_auto_installs_when_missing(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    install_target = tmp_path / "scripts"
    install_target.mkdir()
    monkeypatch.delenv("THETA_BIN", raising=False)
    monkeypatch.setattr("theta_py.runner._scripts_dir", lambda: install_target)
    monkeypatch.setattr("theta_py.runner.shutil.which", lambda _name: None)

    binary = _resolve_binary(auto_install=True)

    assert binary.exists(), f"installer did not place a binary at {binary}"
    assert binary.parent == install_target

    result = subprocess.run([str(binary), "--version"], capture_output=True, text=True, check=True)
    assert "theta" in result.stdout.lower()


def test_theta_error_carries_payload() -> None:
    err = ThetaError(args=["check"], returncode=2, stdout="", stderr="boom")
    assert err.returncode == 2
    assert err.stderr == "boom"
    assert err.args_passed == ["check"]
