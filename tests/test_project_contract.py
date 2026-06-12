"""Contract tests for ThetaProject layout assumptions.

These tests verify that the path constants hardcoded in project.py match the
actual output of the theta binary. If theta renames '.theta/' to something
else, or changes where rules/skills land, these tests will fail immediately.

"""

from __future__ import annotations

from theta_py import ThetaProject
from theta_py.project import (
    _DOT_THETA,
    _LOCKFILE,
    _RULES_DIR,
    _SYSTEM_FILE,
)


def test_system_lands_at_dot_theta_system_md():
    with ThetaProject.temp(name="contract-system") as proj:
        proj.add.system(content="contract test system prompt")
        proj.sync(validate=False)
        expected = proj._temp_dir / _DOT_THETA / _SYSTEM_FILE
        assert expected.exists(), (
            f"theta did not write system prompt to {expected}. "
            f"Update _DOT_THETA or _SYSTEM_FILE in project.py."
        )
        assert "contract test system prompt" in expected.read_text()


def test_rule_lands_at_dot_theta_rules_name_md():
    with ThetaProject.temp(name="contract-rule") as proj:
        proj.add.rule("my-rule", content="contract rule content")
        proj.sync(validate=False)
        expected = proj._temp_dir / _DOT_THETA / _RULES_DIR / "my-rule.md"
        assert expected.exists(), (
            f"theta did not write rule to {expected}. Update _DOT_THETA or _RULES_DIR in project.py."
        )
        assert "contract rule content" in expected.read_text()


def test_lock_lands_at_theta_lock():
    with ThetaProject.temp(name="contract-lock") as proj:
        proj.add.system(content="lock test")
        proj.sync(validate=False)
        expected = proj._temp_dir / _LOCKFILE
        assert expected.exists(), (
            f"theta did not write lockfile to {expected}. Update _LOCKFILE in project.py."
        )


def test_skills_dir_is_dot_theta_skills():
    with ThetaProject.temp(name="contract-skills-dir") as proj:
        proj.sync(validate=False)
        assert proj.theta_dir == proj._temp_dir / _DOT_THETA
