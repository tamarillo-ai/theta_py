from __future__ import annotations

import os
import sys
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


def _host_platform_tag() -> str:
    override = os.environ.get("THETA_PY_PLATFORM_TAG")
    if override:
        return override

    from packaging.tags import sys_tags

    tag = next(t for t in sys_tags() if "manylinux" not in t.platform and "musllinux" not in t.platform)
    platform_str = tag.platform

    if sys.platform == "darwin":
        from hatchling.builders.macos import process_macos_plat_tag

        platform_str = process_macos_plat_tag(platform_str, compat=False)

    return platform_str


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
