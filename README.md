# Local Coding Agent Workspace

This repository documents the plan for building a local-first coding assistant that can operate via both a command-line interface and a web application. The assistant will coordinate with a jailed shell for workspace execution, support session tracking for multiple users, and capture token-usage analytics.

## Getting Started
1. Review the **Plan**, **Requirements**, **Design**, and **Task Board** documents in the [`docs/`](docs/) directory before working on the project.
2. Install the Python dependencies listed in [`requirements.txt`](requirements.txt) to run the automated test suite.
3. Update the relevant documentation whenever you add features or make architectural decisions.
4. Keep this top-level README aligned with the current system direction.

## Key Documents
- [`docs/PLAN.md`](docs/PLAN.md) – delivery roadmap and milestones.
- [`docs/REQUIREMENTS.md`](docs/REQUIREMENTS.md) – functional and non-functional expectations.
- [`docs/DESIGN.md`](docs/DESIGN.md) – module-level architecture and integration notes.
- [`docs/TASKS.md`](docs/TASKS.md) – active and upcoming tasks.

## Python Environment
- Install dependencies: `pip install -r requirements.txt`.
- Run the automated tests with `pytest` from the repository root.

## Persistent Shell Utility
The `local_agent.shell.Shell` class launches a persistent `/bin/sh` process inside a Bubblewrap (`bwrap`) jail that is rooted at your workspace directory. Commands execute with real shell semantics (including built-ins such as `cd` and `export`), and state persists across calls.

```python
from pathlib import Path

from local_agent import Shell

shell = Shell(session="demo", base_directory=Path.cwd())
shell.run("ls")
shell.run("cd docs")
result = shell.run("pwd")
print(result.stdout.strip())  # -> /docs
```

Each invocation returns a `ShellResult` containing the exit code, standard output, and standard error. The jailed shell cannot see paths outside the supplied workspace, and changes made through the shell are reflected on disk for the caller.

> **Prerequisite:** Install Bubblewrap (e.g., `sudo apt-get install bubblewrap`) and ensure the host allows user namespaces so the jail can be created.

### Async Usage

Web-facing services that rely on asyncio event loops can offload blocking shell invocations using `asyncio.to_thread` (Python 3.9+):

```python
import asyncio
from local_agent import Shell

async def run_in_session(shell: Shell) -> None:
    await asyncio.to_thread(shell.run, "cd docs")
    result = await asyncio.to_thread(shell.run, "pwd")
    print(result.stdout.strip())
```

This pattern preserves shell state across commands while keeping the event loop responsive.

## Key Technology Decisions
- **Sandboxing**: Bubblewrap (`bwrap`) provides jailed shell execution for all sessions.
- **Runtime**: All Python services target version 3.9+ to maximize compatibility.
- **Storage**: SQLite backs early metadata needs (sessions, tasks, analytics) before migrating to heavier stores.
- **LLM Integration**: OpenAI-based agents coordinate coding assistance across CLI and web experiences.

## Contributing Guidance
- Follow any instructions in `AGENTS.md` files before making changes.
- Prefer incremental updates: keep documentation accurate as you implement functionality.
- Capture open questions or assumptions in the documentation to help future contributors.

## Testing
- Run `pytest` to execute the full suite, including smoke tests that validate the shell wrapper.

## Current Status
Planning documents have completed stakeholder review. Implementation work on the core infrastructure can now begin.
