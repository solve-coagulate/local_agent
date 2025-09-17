"""Utilities for running persistent shell sessions backed by Bubblewrap."""

from __future__ import annotations

import os
import selectors
import shlex
import shutil
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import IO, Dict, List, Optional, Tuple
from uuid import uuid4


@dataclass
class ShellResult:
    """Represents the outcome of executing a shell command."""

    exit_code: int
    stdout: str
    stderr: str


class _ShellProcess:
    """Manages a persistent Bubblewrap-backed shell process."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self._lock = threading.Lock()
        self._process = self._spawn_process()

    def run(self, command: str) -> ShellResult:
        """Execute ``command`` inside the persistent shell process."""

        with self._lock:
            return self._run_locked(command)

    def _spawn_process(self) -> subprocess.Popen:
        _ensure_bwrap_available()
        command = _bubblewrap_command(self.root)
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
        )
        return process

    def _run_locked(self, command: str) -> ShellResult:
        process = self._process
        if process.poll() is not None:
            raise RuntimeError(self._terminated_message())

        stdin = process.stdin
        stdout = process.stdout
        stderr = process.stderr
        if stdin is None or stdout is None or stderr is None:
            raise RuntimeError("Shell process pipes are not available")

        marker = f"__SHELL_DONE_{uuid4().hex}__"
        payload = command
        if not payload.endswith("\n"):
            payload += "\n"
        payload += "status=$?\n"
        payload += f"printf '%s %s\\n' {shlex.quote(marker)} \"$status\"\n"

        try:
            stdin.write(payload.encode("utf-8"))
            stdin.flush()
        except BrokenPipeError as exc:  # pragma: no cover - defensive guard
            raise RuntimeError(self._terminated_message()) from exc

        stdout_bytes, stderr_bytes, exit_code = _capture_output(stdout, stderr, marker)
        return ShellResult(
            exit_code=exit_code,
            stdout=stdout_bytes.decode("utf-8", errors="replace"),
            stderr=stderr_bytes.decode("utf-8", errors="replace"),
        )

    def _terminated_message(self) -> str:
        message = "Shell session has terminated."
        stderr = self._process.stderr
        if stderr is not None:
            try:
                detail = stderr.read().decode("utf-8", errors="replace")
            except OSError:  # pragma: no cover - extremely unlikely
                detail = ""
            if detail:
                message = f"{message} Bubblewrap stderr:\n{detail.strip()}"
        return message


class Shell:
    """Execute commands in a persistent Bubblewrap-jailed shell session."""

    _sessions: Dict[str, _ShellProcess] = {}
    _sessions_lock = threading.Lock()

    def __init__(self, session: str, base_directory: Optional[Path] = None) -> None:
        if not session:
            raise ValueError("session must be a non-empty string")

        base_dir = Path(base_directory) if base_directory is not None else Path.cwd()
        if not base_dir.exists() or not base_dir.is_dir():
            raise ValueError(f"base_directory {base_dir!s} is not a valid directory")
        base_dir = base_dir.resolve()

        with self._sessions_lock:
            existing = self._sessions.get(session)
            if existing is None:
                process = _ShellProcess(root=base_dir)
                self._sessions[session] = process
            else:
                if existing.root != base_dir:
                    raise ValueError(
                        "Session already exists with a different base directory"
                    )
                process = existing

        self._session = session
        self._process = process

    @property
    def root(self) -> Path:
        """Return the workspace root bound inside the Bubblewrap jail."""

        return self._process.root

    @property
    def session(self) -> str:
        """Return the session identifier backing this shell instance."""

        return self._session

    def run(self, command: str) -> ShellResult:
        """Run ``command`` and return the captured result."""

        if not isinstance(command, str):
            raise TypeError("command must be a string")

        if command.strip() == "":
            return ShellResult(exit_code=0, stdout="", stderr="")

        return self._process.run(command)


def _ensure_bwrap_available() -> None:
    if shutil.which("bwrap") is None:
        raise RuntimeError(
            "Bubblewrap (bwrap) is required to run shell sessions but was not found in PATH."
        )


def _bubblewrap_command(root: Path) -> List[str]:
    command: List[str] = [
        "bwrap",
        "--die-with-parent",
        "--unshare-user-try",
        "--bind",
        str(root),
        "/",
        "--tmpfs",
        "/tmp",
        "--dev-bind-try",
        "/dev",
        "/dev",
        "--proc",
        "/proc",
        "--setenv",
        "HOME",
        "/",
        "--setenv",
        "PATH",
        "/bin:/usr/bin",
    ]

    for path in ("/bin", "/usr"):
        command.extend(["--ro-bind", path, path])

    for optional in ("/lib", "/lib64", "/lib/x86_64-linux-gnu", "/etc"):
        command.extend(["--ro-bind-try", optional, optional])

    command.extend(["--chdir", "/", "/bin/sh"])
    return command


def _capture_output(stdout: IO[bytes], stderr: IO[bytes], marker: str) -> Tuple[bytes, bytes, int]:
    selector = selectors.DefaultSelector()
    selector.register(stdout, selectors.EVENT_READ)
    selector.register(stderr, selectors.EVENT_READ)

    marker_bytes = marker.encode("utf-8")
    stdout_buffer = bytearray()
    stderr_buffer = bytearray()
    exit_code: Optional[int] = None
    captured_stdout = b""
    timeout: Optional[float] = None

    while True:
        events = selector.select(timeout)
        if not events:
            if exit_code is not None:
                break
            continue

        for key, _ in events:
            stream = key.fileobj
            if stream is stdout:
                chunk = os.read(stdout.fileno(), 4096)
                if not chunk:
                    selector.unregister(stdout)
                    continue
                stdout_buffer.extend(chunk)
                extraction = _extract_completion(stdout_buffer, marker_bytes)
                if extraction is not None:
                    exit_code, captured_stdout = extraction
                    selector.unregister(stdout)
                    timeout = 0.0
            else:
                chunk = os.read(stderr.fileno(), 4096)
                if not chunk:
                    selector.unregister(stderr)
                    continue
                stderr_buffer.extend(chunk)

        if exit_code is not None and timeout == 0.0 and not selector.get_map():
            break
        if exit_code is not None and timeout == 0.0:
            continue

    if exit_code is None:
        raise RuntimeError("Shell session did not report a completion marker")

    return captured_stdout, bytes(stderr_buffer), exit_code


def _extract_completion(
    buffer: bytearray, marker: bytes
) -> Optional[Tuple[int, bytes]]:
    index = buffer.find(marker)
    if index == -1:
        return None

    newline_index = buffer.find(b"\n", index)
    if newline_index == -1:
        return None

    marker_line = buffer[index:newline_index].strip()
    parts = marker_line.split()
    if len(parts) < 2:
        raise RuntimeError("Malformed completion marker from shell session")

    try:
        exit_code = int(parts[-1])
    except ValueError as exc:  # pragma: no cover - unexpected shell behaviour
        raise RuntimeError("Invalid exit code reported by shell session") from exc

    stdout_bytes = bytes(buffer[:index])
    remainder = buffer[newline_index + 1 :]
    buffer[:] = remainder
    return exit_code, stdout_bytes
