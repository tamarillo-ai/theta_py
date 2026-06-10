from __future__ import annotations

from collections.abc import Sequence
from typing import Any


class ThetaInvocationError(RuntimeError):
    """Base class for any failure invoking the theta binary."""


class ThetaError(ThetaInvocationError):
    """Transport-level failure invoking the theta binary.

    Covers non-zero exit with no parseable envelope, malformed stdout, or any
    other failure that is *not* a clean `status: "error"` envelope.
    """

    def __init__(self, *, args: Sequence[str], returncode: int, stdout: str, stderr: str) -> None:
        super().__init__(f"theta {' '.join(args)} exited with {returncode}: {stderr.strip()}")
        self.args_passed = list(args)
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class ThetaCommandError(ThetaInvocationError):
    """A well-formed `status: "error"` envelope from the theta binary.

    `diagnostics` mirrors the rust-side `theta_schema::Diagnostic` shape:
    every entry has `level`, `path`, `message` keys. `data` is the verb's
    partial outcome at the moment of failure (typically empty fields).
    """

    def __init__(
        self,
        *,
        verb: Sequence[str],
        diagnostics: list[dict[str, Any]],
        data: Any,
    ) -> None:
        msg = "; ".join(d.get("message", "") for d in diagnostics if d.get("level") == "error")
        super().__init__(f"theta {' '.join(verb)} failed: {msg or '(no diagnostic message)'}")
        self.verb = list(verb)
        self.diagnostics = diagnostics
        self.data = data


class ThetaBinaryNotFoundError(FileNotFoundError):
    """No theta binary could be located and auto-install was disabled."""
