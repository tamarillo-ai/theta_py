from __future__ import annotations

import os
import sys
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


def _host_platform_tag() -> str:
    """The PEP 425 platform tag we stamp into the wheel filename.

    PyPI rejects bare `linux_*` tags. Wheels MUST carry a `manylinux_*` (or
    `musllinux_*`) tag on Linux, `macosx_X_Y_*` on macOS, and `win_*` on
    Windows. We compute the right value per platform; CI can override with
    `THETA_PY_PLATFORM_TAG` when cross-building.
    """
    override = os.environ.get("THETA_PY_PLATFORM_TAG")
    if override:
        return override

    from packaging.tags import sys_tags

    if sys.platform == "linux":
        # prefer the lowest manylinux floor we can match. PyPI accepts
        # `manylinux_2_X_<arch>`; `manylinux2014_<arch>` (the legacy alias)
        # is equivalent to `manylinux_2_17_<arch>`. CI sets the runner image
        # so this just reflects what the runner provides.
        for tag in sys_tags():
            if tag.platform.startswith("manylinux"):
                return tag.platform
        msg = (
            "no manylinux tag available on this host; cannot build a "
            "PyPI-acceptable Linux wheel. Override with "
            "THETA_PY_PLATFORM_TAG (e.g. manylinux_2_28_x86_64)."
        )
        raise RuntimeError(msg)

    if sys.platform == "darwin":
        from hatchling.builders.macos import process_macos_plat_tag

        tag = next(t for t in sys_tags() if t.platform.startswith("macosx"))
        return process_macos_plat_tag(tag.platform, compat=False)

    # Windows: just pick the first concrete tag, which is `win_amd64`
    # (or `win_arm64`).
    return next(t for t in sys_tags() if t.platform.startswith("win")).platform


class ThetaPyBuildHook(BuildHookInterface):
    PLUGIN_NAME = "custom"

    def initialize(self, version: str, build_data: dict) -> None:
        if self.target_name != "wheel":
            return

        binary = Path(self.root) / "src" / "theta_py" / "_bin" / ("theta.exe" if os.name == "nt" else "theta")

        if not binary.exists():
            if os.environ.get("THETA_PY_REQUIRE_BINARY") == "1":
                msg = (
                    f"THETA_PY_REQUIRE_BINARY=1 but no binary found at {binary}. "
                    "Download it from the matching theta release before building "
                    "(see scratch/theta-py-release-dry-run.fish)."
                )
                raise RuntimeError(msg)
            return

        build_data["shared_scripts"][str(binary)] = "theta.exe" if os.name == "nt" else "theta"

        build_data["pure_python"] = False

        build_data["tag"] = f"py3-none-{_host_platform_tag()}"
