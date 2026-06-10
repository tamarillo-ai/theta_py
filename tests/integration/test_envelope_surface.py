from __future__ import annotations

from pathlib import Path

import pytest

from theta_py import (
    Theta,
    ThetaBinaryNotFoundError,
    ThetaCommandError,
    ThetaError,
    ThetaInvocationError,
    theta,
)
from theta_py._generated.outcomes import (
    CheckOutcome,
    InitOutcome,
    ListOutcome,
    LockOutcome,
    TreeOutcome,
)


def test_public_imports() -> None:
    from theta_py import cast_to, init, lock
    from theta_py._generated.verbs import Theta

    assert callable(init)
    assert callable(lock)
    assert callable(cast_to)
    assert callable(Theta)


def test_module_theta_is_lazy_singleton(workspace: Path) -> None:
    from theta_py import theta as t1
    from theta_py import theta as t2

    assert t1 is t2


def test_init_returns_init_outcome(workspace: Path) -> None:
    out = theta.init(name="env-test")
    assert isinstance(out, InitOutcome)
    assert out.agent_name == "env-test"
    assert out.source == "scaffold"


def test_init_writes_manifest_to_cwd(workspace: Path) -> None:
    theta.init(name="env-test")
    assert (workspace / "theta.toml").exists()


def test_check_returns_check_outcome(initialized: Path) -> None:
    out = theta.check()
    assert isinstance(out, CheckOutcome)
    assert isinstance(out.valid, bool)


def test_lock_then_lock_again(initialized: Path) -> None:
    first = theta.lock()
    assert isinstance(first, LockOutcome)
    assert first.wrote is True

    second = theta.lock()
    assert second.wrote is False


def test_tree_returns_tree_outcome(initialized: Path) -> None:
    out = theta.tree()
    assert isinstance(out, TreeOutcome)
    assert out.tree.name


def test_add_rule_then_list_then_rm(initialized: Path) -> None:
    added = theta.add.rule("safety")
    assert added.entity == "rule"
    assert added.name == "safety"

    listing = theta.list.rules()
    assert isinstance(listing, ListOutcome)
    assert listing.kind == "rules"

    removed = theta.rm.rule("safety", no_sync=True)
    assert removed.entity == "rule"
    assert removed.name == "safety"


def test_flat_function_writes_same_state_as_namespaced(workspace: Path) -> None:
    from theta_py import init as flat_init

    out = flat_init(name="flat-and-ns")
    assert isinstance(out, InitOutcome)
    assert out.agent_name == "flat-and-ns"
    assert (workspace / "theta.toml").exists()


def test_error_hierarchy() -> None:
    assert issubclass(ThetaError, ThetaInvocationError)
    assert issubclass(ThetaCommandError, ThetaInvocationError)


def test_init_twice_raises_theta_command_error(initialized: Path) -> None:
    with pytest.raises(ThetaCommandError) as exc:
        theta.init()

    err = exc.value
    assert err.verb == ["init"]
    assert err.diagnostics
    assert isinstance(err, ThetaInvocationError)


def test_per_call_cwd_overrides_process_cwd(workspace: Path, tmp_path_factory) -> None:
    other = tmp_path_factory.mktemp("other-workspace")
    t = Theta()
    out = t.init(name="explicit-cwd", cwd=other)
    assert isinstance(out, InitOutcome)
    assert (other / "theta.toml").exists()
    assert not (workspace / "theta.toml").exists()


def test_instance_cwd_pins_workspace(workspace: Path, tmp_path_factory) -> None:
    pinned = tmp_path_factory.mktemp("pinned-workspace")
    t = Theta(cwd=pinned)
    t.init(name="pinned")
    assert (pinned / "theta.toml").exists()
    assert not (workspace / "theta.toml").exists()


def test_binary_not_found_raises(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    from theta_py.runner import _resolve_binary

    monkeypatch.setenv("PATH", "/nonexistent")
    monkeypatch.setenv("THETA_BIN", "/definitely/not/here/theta")
    monkeypatch.setattr("theta_py.runner._scripts_dir", lambda: tmp_path / "empty")
    monkeypatch.setattr("theta_py.runner.shutil.which", lambda _name: None)
    with pytest.raises((ThetaBinaryNotFoundError, FileNotFoundError)):
        _resolve_binary(auto_install=False)
