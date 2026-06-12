from __future__ import annotations

import pytest

from theta_py import ThetaProject


def test_temp_creates_project_with_name():
    with ThetaProject.temp(name="my-agent") as proj:
        assert proj.name == "my-agent"
        assert proj._manifest_path.exists()


def test_temp_cleans_up_on_exit():
    with ThetaProject.temp(name="cleanup-test") as proj:
        temp_dir = proj._temp_dir
    assert not temp_dir.exists()


def test_temp_sync_materializes_system_and_rules():
    with ThetaProject.temp(name="sync-test") as proj:
        proj.add.system(content="You are a test agent.")
        proj.add.rule("safety", content="Never do bad things.")
        proj.sync(validate=False)

        assert proj.system_prompt is not None
        assert "You are a test agent" in proj.system_prompt

        rules = proj.rules
        assert "safety" in rules
        assert "Never do bad things" in rules["safety"].content


def test_temp_identity_before_sync():
    with ThetaProject.temp(name="identity-agent") as proj:
        assert proj.name == "identity-agent"
        assert isinstance(proj.version, str)
        assert isinstance(proj.authors, list)
        assert proj.model is None
        assert proj.tags == []


def test_temp_rules_empty_when_only_system_synced():
    with ThetaProject.temp(name="no-rules") as proj:
        proj.add.system(content="just a system prompt")
        proj.sync(validate=False)
        assert proj.rules == {}


def test_temp_lock_hash_after_sync():
    with ThetaProject.temp(name="hash-test") as proj:
        proj.add.system(content="hello")
        proj.sync(validate=False)
        h = proj.lock_hash
        assert h is not None
        assert len(h) > 10


def test_from_manifest_reads_existing_project(tmp_path):
    from theta_py import runner

    runner.run(["init", "--name", "existing-agent"], cwd=tmp_path)
    runner.run(["add", "system", "--content", "Existing system."], cwd=tmp_path)

    with ThetaProject.from_manifest(tmp_path / "theta.toml") as proj:
        assert proj.name == "existing-agent"
        proj.sync(validate=False)
        assert proj.system_prompt is not None
        assert "Existing system" in proj.system_prompt

    assert not (tmp_path / ".theta").exists()
    assert not (tmp_path / "theta.lock").exists()


def test_from_manifest_does_not_touch_source(tmp_path):
    from theta_py import runner

    runner.run(["init", "--name", "untouched"], cwd=tmp_path)
    runner.run(["add", "system", "--content", "Original."], cwd=tmp_path)

    before_files = set(tmp_path.iterdir())

    with ThetaProject.from_manifest(tmp_path / "theta.toml") as proj:
        proj.sync(validate=False)

    after_files = set(tmp_path.iterdir())
    assert before_files == after_files, (
        f"from_manifest modified source directory. New files: {after_files - before_files}"
    )


def test_from_manifest_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        ThetaProject.from_manifest("/nonexistent/path/theta.toml")


def test_system_prompt_raises_before_sync():
    with ThetaProject.temp(name="unsync-guard") as proj, pytest.raises(RuntimeError, match="sync"):
        _ = proj.system_prompt


def test_rules_raises_before_sync():
    with ThetaProject.temp(name="rules-guard") as proj, pytest.raises(RuntimeError, match="sync"):
        _ = proj.rules


def test_skills_path_raises_before_sync():
    with ThetaProject.temp(name="skills-guard") as proj, pytest.raises(RuntimeError, match="sync"):
        _ = proj.skills_path


def test_tools_empty_on_fresh_project():
    with ThetaProject.temp(name="no-tools") as proj:
        proj.add.system(content="placeholder")
        proj.sync(validate=False)
        assert proj.tools == {}
