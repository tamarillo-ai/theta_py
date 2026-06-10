from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import sysconfig
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from theta_py._version import THETA_VERSION
from theta_py.errors import ThetaBinaryNotFoundError, ThetaCommandError, ThetaError


def _scripts_dir() -> Path:
    """Resolve the active interpreter's scripts/bin directory.

    Uses sysconfig so it stays correct under venv, `pip install --user`,
    Conda, and Windows (where it's `Scripts/` instead of `bin/`). This is the
    same approach ruff's _find_ruff.py uses.
    """
    return Path(sysconfig.get_path("scripts"))


def _bin_name() -> str:
    return "theta.exe" if os.name == "nt" else "theta"


def _candidate_paths() -> list[Path]:
    """Resolution order: $THETA_BIN → active interpreter scripts dir → $PATH.

    The "active interpreter scripts dir" is what hatchling's `shared-scripts`
    target maps to, so a `pip install theta-py` lands the binary there.
    """
    candidates: list[Path] = []
    override = os.environ.get("THETA_BIN")
    if override:
        candidates.append(Path(override))
    candidates.append(_scripts_dir() / _bin_name())
    return candidates


def _resolve_binary(*, auto_install: bool = True) -> Path:
    """Locate the theta binary.

    Precedence: $THETA_BIN, sysconfig scripts dir (wheel-installed), $PATH.
    Falls back to running the installer when `auto_install` is set.
    """
    for candidate in _candidate_paths():
        if candidate.exists():
            return candidate
    on_path = shutil.which("theta")
    if on_path is not None:
        return Path(on_path)
    if auto_install:
        _auto_install_binary()
        installed = _scripts_dir() / _bin_name()
        if installed.exists():
            return installed
    raise ThetaBinaryNotFoundError(
        "no theta binary found. Set $THETA_BIN, install via "
        "`python -m theta_py.install`, or put `theta` on PATH.",
    )


def _auto_install_binary() -> None:
    from theta_py.install import install

    install_dir = _scripts_dir()
    print(
        f"theta_py: fetching theta {THETA_VERSION} into {install_dir}",
        file=sys.stderr,
    )
    install(install_dir=install_dir, version=THETA_VERSION)


def run(
    args: Sequence[str],
    *,
    cwd: str | os.PathLike[str] | None = None,
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Resolve the binary and invoke `theta --output-format json <args>`."""
    return run_with_binary(_resolve_binary(), args, cwd=cwd, env=env)


def run_with_binary(
    binary: Path,
    args: Sequence[str],
    *,
    cwd: str | os.PathLike[str] | None = None,
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Invoke a specific binary; raise on `status: "error"` envelopes."""
    envelope = run_raw(binary, args, cwd=cwd, env=env)
    if envelope.get("status") == "error":
        raise ThetaCommandError(
            verb=envelope.get("verb", list(args)),
            diagnostics=envelope.get("diagnostics", []),
            data=envelope.get("data"),
        )
    return envelope


def run_raw(
    binary: Path,
    args: Sequence[str],
    *,
    cwd: str | os.PathLike[str] | None = None,
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Invoke a binary, parse its envelope, never raise on `status: "error"`."""
    full = [str(binary), "--output-format", "json", *args]
    proc_env = dict(os.environ)
    if env is not None:
        proc_env.update(env)
    completed = subprocess.run(
        full,
        capture_output=True,
        text=True,
        cwd=cwd,
        env=proc_env,
        check=False,
    )
    stdout = completed.stdout
    if not stdout.strip():
        raise ThetaError(
            args=args,
            returncode=completed.returncode,
            stdout=stdout,
            stderr=completed.stderr,
        )
    try:
        envelope: dict[str, Any] = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise ThetaError(
            args=args,
            returncode=completed.returncode,
            stdout=stdout,
            stderr=completed.stderr,
        ) from exc
    for key in ("verb", "status", "diagnostics", "data"):
        if key not in envelope:
            raise ThetaError(
                args=args,
                returncode=completed.returncode,
                stdout=stdout,
                stderr=f"envelope missing key {key!r}",
            )
    return envelope
