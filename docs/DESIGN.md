# System Design

This document describes the major components required to deliver the local coding agent platform. Update the module breakdown as the architecture evolves.

## High-Level Architecture
The system is composed of several services orchestrated around session management:

- **Gateway Layer**: REST/GraphQL APIs supporting both CLI and web clients, plus WebSocket channels for streaming shell output.
- **Agent Orchestrator**: Coordinates task assignment, invokes the jailed shell, manages tool availability per agent persona, and brokers OpenAI-powered assistance flows.
- **Workspace Service**: Prepares repo copies, enforces filesystem quotas, and snapshots state for auditing.
- **Analytics Pipeline**: Captures token usage, session metrics, and operational telemetry for reporting and alerting.
- **Data Stores**: SQLite for early metadata (sessions, tasks, analytics summaries), object storage for workspace snapshots, and a time-series store for metrics as scale increases.

## Module Breakdown

### 1. CLI Interface
- **Responsibilities**: Authenticate users, render command menus, stream shell output, and surface task details.
- **Key Interactions**: Calls Gateway APIs, subscribes to WebSocket channels, and posts task status updates.
- **Implementation Notes**: Favor a plugin architecture for future tooling; support offline caching of task metadata.
- **Open Questions**: Should the CLI embed an editor mode or rely on external editors synced to the workspace?

### 2. Web Application
- **Responsibilities**: Provide interactive dashboards for sessions, tasks, and analytics while maintaining parity with CLI capabilities.
- **Key Interactions**: Uses Gateway APIs and WebSocket endpoints; renders charts from analytics summaries.
- **Implementation Notes**: Consider a component library that supports dark mode and accessibility standards.
- **Open Questions**: Determine preferred front-end stack (React, Svelte, etc.) and hosting model.

### 3. Session Manager
- **Responsibilities**: Maintain session lifecycle, allocate jailed shell instances, and enforce concurrency policies.
- **Key Interactions**: Communicates with Workspace Service for repo preparation and with Analytics Pipeline for event emission.
- **Implementation Notes**: Use an event-driven architecture (message queue) to decouple shell provisioning from user requests and persist session metadata in SQLite.
- **Open Questions**: How should long-running background tasks (e.g., tests) be tracked within a session?

### 4. Jailed Shell Service
- **Responsibilities**: Provide isolated execution environments with network, filesystem, and process limits.
- **Key Interactions**: Receives command requests from the Session Manager and streams output to clients via Gateway.
- **Implementation Notes**: Use Bubblewrap (`bwrap`) to create process-isolated sandboxes with predefined filesystem and network policies.
- **Open Questions**: What auditing mechanism is required to track file diffs and commands executed?

### 4a. Local Shell Utility
- **Responsibilities**: Provide a lightweight Python interface for issuing commands against the local workspace while respecting session boundaries.
- **Key Interactions**: Serves as an adapter for higher-level services or tests that need shell semantics (e.g., `cd`, `pwd`) without bootstrapping the full session-management stack.
- **Implementation Notes**: Launch a Bubblewrap-jailed `/bin/sh` per session (sharing processes by session identifier), stream commands through stdin, detect completion via unique sentinels, and expose structured results (`exit_code`, `stdout`, `stderr`).
- **Open Questions**: Do we need to stream output for long-running commands or surface a mechanism to terminate runaway processes?

### 5. Task Coordination Service
- **Responsibilities**: Store task metadata, track ownership, log progress updates, and integrate with PR tooling.
- **Key Interactions**: Syncs with `docs/TASKS.md` (initial source of truth) and exposes CRUD operations to clients.
- **Implementation Notes**: Start with markdown parsing backed by SQLite tables for richer queries; evolve to a larger database once collaborative edits become frequent.
- **Open Questions**: When should we automate task assignment based on agent workload or expertise?

### 6. Analytics & Reporting
- **Responsibilities**: Aggregate token consumption, session duration, task completion metrics, and cost estimates.
- **Key Interactions**: Ingests events from Gateway, Session Manager, and Task Coordination services; exposes dashboards via the web app.
- **Implementation Notes**: Choose a telemetry stack (OpenTelemetry, Prometheus) that integrates with both CLI and web clients.
- **Open Questions**: What cadence should usage reports be delivered, and who consumes them?

## Cross-Cutting Concerns
- **Authentication & Authorization**: Centralize identity enforcement at the Gateway and propagate scoped tokens to downstream services.
- **Configuration Management**: Maintain environment-specific settings in version-controlled templates with secrets stored externally.
- **Logging & Monitoring**: Standardize structured logging formats and ensure trace IDs propagate across components.
- **Runtime Baseline**: Standardize on Python 3.9+ for backend services and tooling to simplify packaging and compatibility.
- **Testing Strategy**: Provide extensive automated coverage—unit tests per module, integration tests for key workflows (session creation, shell command execution), and end-to-end tests for CLI and web flows—with gating in CI.
- **Documentation**: Keep module documentation synchronized with implementation; link code references back to this design.

## Future Enhancements
- Model-based policy engine to limit tool usage by role or compliance category.
- AI-assisted code review workflows integrated with the task coordination service.
- Extension marketplace for third-party tools vetted through sandboxed execution.
