from __future__ import annotations

from theta_py import ThetaProject
from theta_py._generated.constants import (
    DOT_THETA_DIR as _DOT_THETA,
)
from theta_py._generated.constants import (
    LOCKFILE as _LOCKFILE,
)
from theta_py._generated.constants import (
    RULES_DIR as _RULES_DIR,
)
from theta_py._generated.constants import (
    SYSTEM_FILE_NAME as _SYSTEM_FILE,
)


def test_system_lands_at_dot_theta_system_md():
    with ThetaProject.create(name="contract-system") as proj:
        proj.add.system(content="contract test system prompt")
        proj.sync(validate=False)
        expected = proj._temp_dir / _DOT_THETA / _SYSTEM_FILE
        assert expected.exists(), (
            f"theta did not write system prompt to {expected}. "
            f"Update _DOT_THETA or _SYSTEM_FILE in project.py."
        )
        assert "contract test system prompt" in expected.read_text()


def test_rule_lands_at_dot_theta_rules_name_md():
    with ThetaProject.create(name="contract-rule") as proj:
        proj.add.rule("my-rule", content="contract rule content")
        proj.sync(validate=False)
        expected = proj._temp_dir / _DOT_THETA / _RULES_DIR / "my-rule.md"
        assert expected.exists(), (
            f"theta did not write rule to {expected}. Update _DOT_THETA or _RULES_DIR in project.py."
        )
        assert "contract rule content" in expected.read_text()


def test_lock_lands_at_theta_lock():
    with ThetaProject.create(name="contract-lock") as proj:
        proj.add.system(content="lock test")
        proj.sync(validate=False)
        expected = proj._temp_dir / _LOCKFILE
        assert expected.exists(), (
            f"theta did not write lockfile to {expected}. Update _LOCKFILE in project.py."
        )


def test_skills_dir_is_dot_theta_skills():
    with ThetaProject.create(name="contract-skills-dir") as proj:
        proj.sync(validate=False)
        assert proj.theta_dir == proj._temp_dir / _DOT_THETA
