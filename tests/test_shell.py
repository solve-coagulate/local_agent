"""Tests for the Bubblewrap-backed persistent shell utility."""

from pathlib import Path
from uuid import uuid4

import pytest

from local_agent import Shell


@pytest.fixture()
def shell(tmp_path: Path) -> Shell:
    """Create a shell rooted at a temporary directory."""

    workspace = tmp_path / "workspace"
    workspace.mkdir()

    session_name = f"test-session-{uuid4().hex}"
    try:
        return Shell(session=session_name, base_directory=workspace)
    except RuntimeError as exc:
        pytest.skip(f"Bubblewrap shell unavailable: {exc}")


def test_run_basic_command(shell: Shell) -> None:
    """The shell should run basic commands and capture output."""

    (shell.root / "file.txt").write_text("sample", encoding="utf-8")
    result = shell.run("ls")
    assert result.exit_code == 0
    assert "file.txt" in result.stdout
    assert result.stderr == ""


def test_cd_updates_working_directory(shell: Shell) -> None:
    """Changing directories should affect subsequent commands."""

    make_dir = shell.run("mkdir subdir")
    assert make_dir.exit_code == 0

    change = shell.run("cd subdir")
    assert change.exit_code == 0

    pwd = shell.run("pwd")
    assert pwd.exit_code == 0
    assert pwd.stdout.strip() == "/subdir"


def test_cd_to_parent_stays_in_root(shell: Shell) -> None:
    """Navigating above the workspace root should leave us at `/`."""

    first = shell.run("cd ..")
    assert first.exit_code == 0

    pwd = shell.run("pwd")
    assert pwd.stdout.strip() == "/"


def test_cd_requires_existing_directory(shell: Shell) -> None:
    """The shell should refuse to change to missing directories."""

    missing = shell.run("cd missing")
    assert missing.exit_code != 0
    assert "can't cd to missing" in missing.stderr


def test_environment_state_persists(shell: Shell) -> None:
    """Exports and other shell state should persist across invocations."""

    export = shell.run("export DEMO_VAR=value")
    assert export.exit_code == 0

    echo = shell.run('printf "%s" "$DEMO_VAR"')
    assert echo.exit_code == 0
    assert echo.stdout == "value"


def test_session_persists_across_instances(tmp_path: Path) -> None:
    """Creating another shell with the same session shares state."""

    workspace = tmp_path / "workspace"
    workspace.mkdir()

    shell_a = Shell(session="shared", base_directory=workspace)
    setup = shell_a.run("mkdir nested && cd nested")
    assert setup.exit_code == 0

    shell_b = Shell(session="shared", base_directory=workspace)
    result = shell_b.run("pwd")
    assert result.exit_code == 0
    assert result.stdout.strip() == "/nested"


def test_filesystem_changes_are_visible(shell: Shell) -> None:
    """Files created in the jailed shell should appear in the workspace."""

    write = shell.run("printf 'data' > sample.txt")
    assert write.exit_code == 0

    assert (shell.root / "sample.txt").read_text(encoding="utf-8") == "data"
