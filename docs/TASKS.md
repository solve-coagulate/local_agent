# Task Board

This backlog highlights near-term priorities and longer-term initiatives. Update task status as work progresses and create new tasks for uncovered work.

## Legend
- **Status**: `Todo`, `In Progress`, `Blocked`, `Review`, `Done`
- **Owner**: `Unassigned` unless a contributor has claimed it
- **Priority**: `P0` (urgent) to `P3` (nice to have)

## Active Tasks
| ID | Title | Status | Priority | Owner | Notes |
| --- | --- | --- | --- | --- | --- |
| T-001 | Finalize requirements and design review | Review | P0 | Unassigned | Updated docs with decisions on Bubblewrap, Python 3.9, SQLite, and OpenAI agents—await stakeholder sign-off. |
| T-002 | Define sandbox technology stack | Done | P0 | Unassigned | Bubblewrap (`bwrap`) selected for jailed shell execution. |
| T-003 | Draft session manager data model | Todo | P1 | Unassigned | Outline schema for sessions, users, and token usage events. |
| T-004 | Outline CLI user journey | Todo | P1 | Unassigned | Create wireframes/flows for CLI interactions and error handling. |
| T-005 | Outline web UI information architecture | Todo | P1 | Unassigned | Draft navigation, views, and component responsibilities. |
| T-006 | Evaluate analytics tooling options | Todo | P2 | Unassigned | Assess metrics, logging, and visualization stack compatibility. |
| T-007 | Establish contribution guidelines | Todo | P2 | Unassigned | Expand README with coding standards and review process once implementation begins. |
| T-008 | Prototype token usage reporting schema | Todo | P2 | Unassigned | Define aggregation strategy for session and task level usage data. |
| T-009 | Implement Bubblewrap sandbox provisioning | In Progress | P0 | Unassigned | Python shell wrapper now launches `bwrap`-jailed sessions; follow-up work needed for automation and auditing hooks. |
| T-010 | Stand up SQLite-backed session store | Todo | P1 | Unassigned | Model tables for sessions, token usage, and task links with migration tooling. |
| T-011 | Integrate OpenAI agent orchestration | Todo | P1 | Unassigned | Wire agent orchestrator to OpenAI APIs with configurable policies and logging. |
| T-012 | Establish automated testing baseline | Todo | P0 | Unassigned | Define CI workflows and minimum coverage thresholds across services. |

## Upcoming Ideas
- Automate synchronization between markdown tasks and a future database-backed service.
- Investigate agent persona configuration and policy management.
- Explore integration with external issue trackers for bidirectional updates.

## How to Work on a Task
1. Claim the task by updating the Owner and Status columns.
2. Reference relevant requirements and design sections when planning implementation.
3. Upon completion, link to the commit/PR and summarize results in the Notes column.
4. If a task becomes blocked, add context in Notes and propose a follow-up task if necessary.
