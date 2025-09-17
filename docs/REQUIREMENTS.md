# System Requirements

This document captures the initial requirements for the local CLI and web-based coding assistant. Revisit and expand these requirements as implementation progresses.

## Functional Requirements
1. **Jailed Shell Workspaces**
   - Provision isolated shell environments per session with access to a dedicated workspace copy of the repository.
   - Support command execution, file inspection, and modification within the sandbox while preventing host escape.
   - Allow configurable resource limits (CPU, memory, disk) and runtime timeouts.
   - Use Bubblewrap (`bwrap`) for sandbox enforcement and document default profiles.

2. **Session Management**
   - Track sessions by user identity, creation timestamp, active workspace, and status.
   - Support concurrent sessions for different users and serialize state for restoration after restarts.
   - Provide lifecycle controls: create, pause, resume, archive, and delete.

3. **CLI Interface**
   - Enable authenticated users to start sessions, run commands, edit files, and request tasks.
   - Display streamed shell output with clear prompts and error handling.
   - Offer shortcuts for viewing documentation, task lists, and analytics summaries.

4. **Web Application**
   - Provide equivalent capabilities to the CLI through a responsive user interface.
   - Support real-time shell output updates (web sockets preferred, fallback to polling).
   - Include session dashboards, token-usage charts, and task progress indicators.

5. **Task Coordination**
   - Integrate with `docs/TASKS.md` (or successor system) to present available work and capture status updates.
   - Allow agents to claim tasks, record notes, and mark completion with links to commits or PRs.

6. **Token Usage Reporting**
   - Record tokens consumed per session, per task, and per feature (CLI vs. web).
   - Provide exportable summaries (CSV/JSON) and visualizations for trending.
   - Trigger alerts when usage exceeds configurable thresholds.

7. **Agent Orchestration**
   - Leverage OpenAI-powered agents for coding assistance across CLI and web clients.
   - Provide configuration for model selection, safety filters, and per-session policy controls.
   - Log prompts/responses with privacy safeguards to feed analytics and debugging workflows.

8. **Local Shell Utility**
   - Offer a Python wrapper that executes commands inside a Bubblewrap-jailed `/bin/sh` rooted at a workspace directory.
   - Allow callers to rely on native shell semantics (e.g., `cd`, environment exports) with state persisting between invocations.
   - Return structured command results (exit code, standard output, standard error) for downstream consumers.
   - Document Bubblewrap prerequisites (binary availability, user-namespace support) and cover the utility with automated tests.
   - Support invocation from asynchronous web services by ensuring thread-safe execution for concurrent callers.

## Non-Functional Requirements
1. **Security**: Ensure shell isolation, sanitize user input, and protect stored credentials.
2. **Reliability**: Aim for 99% session uptime and graceful recovery from infrastructure failures.
3. **Performance**: Shell command latency should remain under 2 seconds for 95% of operations.
4. **Scalability**: Support at least 20 concurrent active sessions without resource contention.
5. **Observability**: Capture structured logs, metrics, and traces across components.
6. **Extensibility**: Architect modules with clear interfaces to enable future agent tooling integrations.
7. **Compliance**: Retain token usage records according to organizational policy (default 90 days) and respect user privacy preferences.
8. **Compatibility**: Ensure all services, tooling, and dependencies run on Python 3.9+.
9. **Quality**: Maintain comprehensive automated test coverage (unit, integration, and end-to-end) with continuous enforcement in CI.

## Open Questions
- What identity provider will back authentication for CLI and web clients?
- How will tasks transition from markdown to a database-backed system if needed?
- Are there budget constraints influencing infrastructure or token consumption limits?
- What governance is required around OpenAI model usage (e.g., rate limits, data retention, fallback providers)?
