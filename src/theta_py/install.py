from __future__ import annotations

import os
import subprocess
import sys
import sysconfig
from pathlib import Path

from theta_py._version import THETA_VERSION

INSTALL_SCRIPT_URL = "https://raw.githubusercontent.com/tamarillo-ai/theta/main/scripts/install.sh"


def install(
    *,
    install_dir: Path | None = None,
    version: str | None = None,
) -> Path:
    """Run the theta installer; return the path the binary was installed to."""
    target = install_dir if install_dir is not None else Path(sysconfig.get_path("scripts"))
    target.mkdir(parents=True, exist_ok=True)

    env = dict(os.environ)
    env["THETA_INSTALL_DIR"] = str(target)
    if version is not None:
        env["THETA_VERSION"] = version if version.startswith("v") else f"v{version}"

    cmd = f"curl -fsSL {INSTALL_SCRIPT_URL} | bash"
    completed = subprocess.run(
        ["bash", "-c", cmd],
        env=env,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"theta installer exited with code {completed.returncode}",
        )
    installed = target / ("theta.exe" if os.name == "nt" else "theta")
    if not installed.exists():
        raise RuntimeError(
            f"theta installer reported success but {installed} does not exist",
        )
    return installed


def main() -> int:
    try:
        path = install(version=THETA_VERSION)
    except Exception as exc:
        print(f"theta_py.install: {exc}", file=sys.stderr)
        return 1
    print(f"installed theta {THETA_VERSION} to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
