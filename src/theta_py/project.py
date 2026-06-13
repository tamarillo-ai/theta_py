from __future__ import annotations

import shutil
import tempfile
import tomllib
from pathlib import Path
from typing import Any, Self, cast

from theta_py import runner
from theta_py._generated.constants import (
    DOT_THETA_DIR as _DOT_THETA,
)
from theta_py._generated.constants import (
    LOCKFILE as _LOCKFILE,
)
from theta_py._generated.constants import (
    MANIFEST_FILE_NAME as _MANIFEST_FILE,
)
from theta_py._generated.constants import (
    SKILLS_DIR as _SKILLS_DIR,
)
from theta_py._generated.constants import (
    THETA_OUT_DIR_ENV as _THETA_OUT_DIR_ENV,
)
from theta_py._generated.manifest import ThetaManifest
from theta_py._generated.outcomes import ProjectSnapshot
from theta_py._generated.project import ThetaProjectMixin
from theta_py._generated.verbs import Theta


class _DisabledNamespace:
    def __init__(self, name: str) -> None:
        self._name = name

    def __getattr__(self, item: str) -> None:
        raise AttributeError(
            f"ThetaProject.theta.{self._name} is disabled: '{self._name}' operations "
            f"write to the global system store and are not safe inside an isolated "
            f"project. Use Theta() directly if you need system-store access."
        )


class ThetaProject(ThetaProjectMixin):
    """A Python view over a materialized theta project in a temp directory.

    Typed properties (``system_prompt``, ``rules``, ``skills``, ``name``, etc.)
    are codegen'd in `~theta_py._generated.project.ThetaProjectMixin`
    from ``theta schema --get``. This class owns the lifecycle orchestration.

    Two internal modes:
    - **temp mode** (``_source_manifest is None``): a brand-new project lives
      entirely inside the temp dir. Normal ``theta sync`` with ``cwd=temp``.
    - **from_manifest mode** (``_source_manifest`` is set): the source project
      lives elsewhere. ``THETA_OUT_DIR`` redirects ``.theta/`` and
      ``theta.lock`` into the temp dir. The source project is never touched.
    """

    def __init__(
        self,
        _temp_dir: Path,
        _owns_temp: bool = False,
        _source_manifest: Path | None = None,
    ) -> None:
        self._temp_dir = _temp_dir
        self._owns_temp = _owns_temp
        # in from_manifest mode the manifest is in the source dir, not temp.
        self._source_manifest = _source_manifest
        self._theta_dir = _temp_dir / _DOT_THETA
        # identity reads come from the real manifest; sync outputs go to temp.
        self._manifest_path = _source_manifest if _source_manifest else (_temp_dir / _MANIFEST_FILE)
        self._lock_path = _temp_dir / _LOCKFILE
        self._has_synced = self._theta_dir.exists()
        self._sync_dirty = False

    @classmethod
    def from_manifest(
        cls,
        manifest_path: str | Path,
        *,
        no_sync: bool = False,
    ) -> Self:
        """Load an existing theta project without modifying it.

        Creates a temp directory and uses ``THETA_OUT_DIR`` to direct
        ``.theta/`` and ``theta.lock`` there. The source project is never
        copied or modified. Source files (rules, skills) are read from their
        real locations via the ``--manifest`` flag.

        Returns a `ThetaProject` that owns the temp directory and
        cleans it up on ``__exit__``.

        By default, ``from_manifest`` performs an immediate ``sync`` into the
        temp directory so post-sync properties (``rules``, ``skills``,
        ``system_prompt``, ``tools``, ``lock_hash``) are ready to read.

        Set ``no_sync=True`` to skip this eager sync and call ``sync()``
        manually.
        """
        manifest_path = Path(manifest_path).resolve()
        if not manifest_path.exists():
            raise FileNotFoundError(f"theta.toml not found: {manifest_path}")

        tmp_root = tempfile.mkdtemp(prefix="theta-project-")
        project = cls(Path(tmp_root), _owns_temp=True, _source_manifest=manifest_path)
        if not no_sync:
            project.sync(validate=False)
        return project

    @classmethod
    def create(
        cls,
        *,
        name: str,
        description: str = "add your description here",
    ) -> Self:
        """Create a brand-new theta project in a temp directory.

        Runs ``theta init``. Caller adds rules/skills/system via the
        mutation methods, then calls `sync`.

        Returns a `ThetaProject` that owns the temp directory and
        cleans it up on ``__exit__``.
        """
        tmp_root = tempfile.mkdtemp(prefix="theta-project-")
        tmp = Path(tmp_root)

        try:
            runner.run(["init", "--name", name], cwd=tmp)
        except Exception:
            shutil.rmtree(tmp_root, ignore_errors=True)
            raise

        return cls(tmp, _owns_temp=True)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        if self._owns_temp:
            shutil.rmtree(self._temp_dir, ignore_errors=True)

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        return getattr(self.theta, name)

    def _out_dir_env(self) -> dict[str, str] | None:
        """In from_manifest mode, redirect .theta/ and theta.lock to temp dir."""
        if self._source_manifest is not None:
            return {_THETA_OUT_DIR_ENV: str(self._temp_dir)}
        return None

    def check(self) -> None:
        """Run ``theta check`` and raise on validation errors."""
        self.theta.check(cwd=self._temp_dir, env=self._out_dir_env())

    def sync(self, *, validate: bool = True) -> None:
        """Materialize ``.theta/`` from ``theta.toml``.

        In from_manifest mode, ``THETA_OUT_DIR`` redirects ``.theta/`` and
        ``theta.lock`` into the temp directory. The source project is never
        modified. Source files (rules, skills) are still read from their real
        locations via the ``--manifest`` flag.

        Args:
            validate: If True (default), runs ``theta check`` first.
        """
        if validate:
            self.check()
        self.theta.sync(cwd=self._temp_dir, env=self._out_dir_env())

    def _refresh_sync_state(self) -> None:
        outcome = self.theta.check(
            skip_materialization=True,
            cwd=self._temp_dir,
            env=self._out_dir_env(),
        )
        self._sync_dirty = (outcome.errors + outcome.warnings + outcome.hints) > 0

    def needs_sync(self, *, deep: bool = True) -> bool:
        if not self._has_synced:
            return True

        if deep:
            self._refresh_sync_state()

        return self._sync_dirty

    @property
    def is_synced(self) -> bool:
        return self._has_synced and not self._sync_dirty

    @property
    def theta(self) -> Theta:
        if not hasattr(self, "_theta_instance"):
            t = Theta(cwd=self._temp_dir, manifest=self._source_manifest)
            t.register = cast(Any, _DisabledNamespace("register"))

            original_run = t._run

            def _wrapped_run(
                argv: list[str],
                *,
                cwd: str | Path | None = None,
                env: dict[str, str] | None = None,
            ) -> dict[str, Any]:
                envelope = original_run(argv, cwd=cwd, env=env)
                head = argv[0] if argv else ""

                if head == "sync":
                    self._has_synced = True
                    self._sync_dirty = False
                    if hasattr(self, "_materialized_cache"):
                        del self._materialized_cache
                elif head != "check":
                    self._refresh_sync_state()

                return envelope

            t._run = cast(Any, _wrapped_run)
            self._theta_instance = t
        return self._theta_instance

    @property
    def manifest(self) -> ThetaManifest:
        if not hasattr(self, "_manifest_cache"):
            with self._manifest_path.open("rb") as f:
                raw = tomllib.load(f)
            self._manifest_cache = ThetaManifest.model_validate(raw)
        return self._manifest_cache

    def _require_synced(self, prop: str) -> None:
        if not self._has_synced and not self._theta_dir.exists():
            raise RuntimeError(f"Cannot read {prop!r}: call sync() first to materialize .theta/")

    @property
    def _materialized(self) -> ProjectSnapshot:
        if not hasattr(self, "_materialized_cache"):
            self._require_synced("materialized content")
            self._materialized_cache = self.theta.get(cwd=self._temp_dir, env=self._out_dir_env())
        return self._materialized_cache

    @property
    def theta_dir(self) -> Path:
        return self._theta_dir

    @property
    def skills_path(self) -> Path:
        self._require_synced("skills_path")
        return self._theta_dir / _SKILLS_DIR

    def __repr__(self) -> str:
        synced = "synced" if self.is_synced else "not synced"
        return f"ThetaProject({self._temp_dir}, {synced})"
