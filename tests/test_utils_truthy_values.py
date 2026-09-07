"""Tests for shared utility helpers."""

import os
import stat
import sys

import pytest

from utils import copytree_owner_writable, env_var_enabled, is_truthy_value


def test_is_truthy_value_accepts_common_truthy_strings():
    assert is_truthy_value("true") is True
    assert is_truthy_value(" YES ") is True
    assert is_truthy_value("on") is True
    assert is_truthy_value("1") is True


def test_is_truthy_value_respects_default_for_none():
    assert is_truthy_value(None, default=True) is True
    assert is_truthy_value(None, default=False) is False


def test_is_truthy_value_rejects_falsey_strings():
    assert is_truthy_value("false") is False
    assert is_truthy_value("0") is False
    assert is_truthy_value("off") is False


def test_env_var_enabled_uses_shared_truthy_rules(monkeypatch):
    monkeypatch.setenv("HERMES_TEST_BOOL", "YeS")
    assert env_var_enabled("HERMES_TEST_BOOL") is True

    monkeypatch.setenv("HERMES_TEST_BOOL", "no")
    assert env_var_enabled("HERMES_TEST_BOOL") is False


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX mode bits and symlinks required")
def test_copytree_owner_writable_keeps_external_symlink_target_unchanged(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "SKILL.md").write_text("source\n")
    external = tmp_path / "external"
    external.mkdir()
    (external / "SKILL.md").write_text("external\n")
    link = source / "linked-skill"
    link.symlink_to(external, target_is_directory=True)

    for path in (source / "SKILL.md", external / "SKILL.md"):
        os.chmod(path, 0o444)
    for path in (source, external):
        os.chmod(path, 0o555)

    try:
        destination = tmp_path / "destination"
        copytree_owner_writable(source, destination, symlinks=True)

        assert destination.joinpath("SKILL.md").stat().st_mode & stat.S_IWUSR
        assert destination.is_dir()
        assert destination.joinpath("linked-skill").is_symlink()
        assert stat.S_IMODE(external.stat().st_mode) == 0o555
        assert stat.S_IMODE(external.joinpath("SKILL.md").stat().st_mode) == 0o444
    finally:
        for path in (source / "SKILL.md", external / "SKILL.md"):
            os.chmod(path, 0o644)
        for path in (source, external):
            os.chmod(path, 0o755)
