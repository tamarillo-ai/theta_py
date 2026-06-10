"""Python bindings for the theta CLI.

from theta_py import theta
theta.cast.to("claude-code")
theta.init(name="agent")

from theta_py import cast_to, init
cast_to("claude-code")
init(name="agent")
"""

from typing import Any

from theta_py._version import THETA_VERSION
from theta_py.errors import (
    ThetaBinaryNotFoundError,
    ThetaCommandError,
    ThetaError,
    ThetaInvocationError,
)

__version__ = THETA_VERSION


def __getattr__(name: str) -> Any:
    from theta_py._generated import verbs

    if name == "theta":
        return verbs._get_theta()
    if hasattr(verbs, name):
        return getattr(verbs, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "THETA_VERSION",
    "Theta",
    "ThetaBinaryNotFoundError",
    "ThetaCommandError",
    "ThetaError",
    "ThetaInvocationError",
]
