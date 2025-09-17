# Agent Development Guide

This guide explains how to use the `openai-agents` SDK to build task-focused assistants for the local coding agent platform. Follow these steps whenever you add or update agent capabilities.

## 1. Define the Application Context
Create a context object that carries the app state your agent needs (database handles, feature flags, request metadata, etc.). The SDK wraps the object in a `RunContextWrapper`, making it available to your hooks, tools, and guardrails without ever sending it to the model.

```python
from dataclasses import dataclass

from local_agent import Shell


@dataclass
class AppContext:
    user_id: str
    session_id: str
    shell: Shell
```

Pass an instance of this context to each run so tools and hooks have access to shared resources.

## 2. Declare Tools
Wrap Python functions with `@function_tool` to expose them to the agent. The decorator inspects type hints and docstrings to generate the JSON schema the model uses when calling the tool.

```python
from openai.agents import function_tool

@function_tool
def run_shell(context: AppContext, command: str) -> str:
    """Execute a shell command in the caller's jailed workspace."""
    result = context.shell.run(command)
    return result.stdout
```

Each tool receives a `ToolContext` plus the JSON-parsed arguments at runtime. Raise exceptions to surface errors back to the model.

## 3. Configure the Agent
Instantiate an `Agent` with instructions, model configuration, tools, and optional guardrails or sub-agents. Use the context type you defined earlier.

```python
from openai.agents import Agent

coding_agent = Agent[
    AppContext
](
    name="workspace-helper",
    instructions="""You are a coding assistant that works inside a jailed shell.
Follow the user's plan, prefer safe commands, and summarize results.""",
    model="gpt-4.1-mini",
    tools=[run_shell],
)
```

## 4. Run the Agent Synchronously
Call `Agent.run_sync(...)` when you want a blocking helper that loops until the agent produces a final answer or hits your turn limit. Provide the app context and reuse a conversation ID to keep threaded history with the OpenAI Conversations API.

```python
response = coding_agent.run_sync(
    prompt="List the files in the repo root and describe the docs folder.",
    context=AppContext(user_id="alice", session_id="S123", shell=my_shell),
    conversation_id="session-S123",
    max_turns=8,
)
print(response.output_text)
```

Behind the scenes the runner handles LLM invocations, tool calls, guardrails, and handoffs until it obtains a final response.

## 5. Manage Conversations and History
To persist history yourself, implement the `Session` protocol. The built-in `OpenAIConversationsSession` automatically stores conversation transcripts using `conversations.items.list` so you can fetch prior messages when resuming a task.

```python
from openai.agents.sessions import OpenAIConversationsSession

session = OpenAIConversationsSession(conversation_id="session-S123")
items = session.get_items(limit=10)
```

Attach the session to your agent runs when you need consistent backscroll across CLI and web clients.

## 6. Apply Guardrails and Handoffs
Guardrails can inspect tool inputs, model outputs, or usage totals. Configure them on the agent to enforce safety policies (e.g., blocking destructive shell commands). Handoffs allow one agent to delegate to another when specialized expertise is needed—describe each handoff so downstream agents know when to take over.

## 7. Log Usage and Outcomes
Every run returns metadata including tool invocations, usage statistics, and any guardrail events. Store this data in the analytics pipeline so the platform can report token consumption per session and feature.

## 8. Testing Tips
- Write unit tests that call your tools directly with representative contexts.
- Use short `max_turns` in automated tests to detect runaway conversations.
- Capture regression fixtures for important conversations and validate that outputs stay within expected bounds after refactors.

Keeping this guide current will help future contributors extend the agent ecosystem safely and consistently.
