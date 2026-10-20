# Agentic AI with Claude Agent SDK + Amazon Bedrock AgentCore

> [!NOTE]
> **About this fork.** This is a fork of [aws-samples/sample-agentic-ai-with-claude-agent-sdk-and-amazon-bedrock-agentcore](https://github.com/aws-samples/sample-agentic-ai-with-claude-agent-sdk-and-amazon-bedrock-agentcore). The upstream repository targets Workshop Studio, and its constraints keep these changes out of upstream. This fork adapts the **foundations** track (modules 1-4) for running in your own AWS account with current tooling. The `advanced/` track is unchanged.
>
> What this fork changes (details in [issue #10](https://github.com/aws-samples/sample-agentic-ai-with-claude-agent-sdk-and-amazon-bedrock-agentcore/issues/10)):
>
> - **SDK:** `claude-agent-sdk` 0.2.168 instead of the yanked 0.2.88. Subagents run in the foreground (`CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1`), so answers that use them are complete, not an interim "still working" reply ([#11](https://github.com/aws-samples/sample-agentic-ai-with-claude-agent-sdk-and-amazon-bedrock-agentcore/pull/11)).
> - **CDK:** the CDK projects build with AgentCore CLI 0.31 (`@aws/agentcore-cdk` 0.1.0-alpha.54), and `setup.sh` installs CLI 0.31.1 ([#12](https://github.com/aws-samples/sample-agentic-ai-with-claude-agent-sdk-and-amazon-bedrock-agentcore/pull/12)).
> - **Notebooks:** the account cells use the `AWS_PROFILE` from `.env` and fail loudly instead of writing an empty account. The module 4 span cell also finds spans in the runtime's log group ([#13](https://github.com/aws-samples/sample-agentic-ai-with-claude-agent-sdk-and-amazon-bedrock-agentcore/pull/13)).
> - **Models:** Claude Sonnet 5.5 and Claude Haiku 5.5 by default ([#14](https://github.com/aws-samples/sample-agentic-ai-with-claude-agent-sdk-and-amazon-bedrock-agentcore/pull/14)).
> - **Clean-up:** each module ends with an opt-in clean-up section, off by default (`RUN_CLEANUP = False`) ([#15](https://github.com/aws-samples/sample-agentic-ai-with-claude-agent-sdk-and-amazon-bedrock-agentcore/pull/15)).
> - **Small fixes** ([#16](https://github.com/aws-samples/sample-agentic-ai-with-claude-agent-sdk-and-amazon-bedrock-agentcore/pull/16)):
>   - `WebSearch` is removed, because Claude Code doesn't offer it on Bedrock.
>   - Deployed agents stream only the model's replies.
>   - The audit logs are no longer tracked.
>   - Doc updates.
>
> Tested end to end (modules 1-4, including clean-up) in us-west-2 with AgentCore CLI 0.31.1 and Python 3.11. It needs Node.js 20+ and AgentCore CLI 0.31.0 or newer. If you're taking the hosted workshop, follow upstream instead.

A hands-on workshop that progressively builds, deploys, and operationalizes AI agents using the [Claude Agent SDK](https://docs.anthropic.com/en/docs/agents-and-tools/claude-agent-sdk) and [Amazon Bedrock AgentCore](https://aws.amazon.com/bedrock/agentcore/).

## Workshop structure

The workshop is organized as a progressive ladder across two tracks. Each module builds on the previous one, adding a new capability while keeping the agent code as the single source of truth.

### Foundations — Build an AI Chief of Staff

A lightweight agent (fictional startup "TechStart Inc" — runway, burn, hiring analysis) that requires only AWS credentials + Bedrock model access.

| Module | What you learn |
|--------|---------------|
| [1 — Local Agent](foundations/build-an-ai-chief-of-staff/module-1-local-agent/) | Build an agent with `ClaudeSDKClient`, system prompts, `CLAUDE.md`, skills, and multi-turn conversation |
| [2 — Deploy](foundations/build-an-ai-chief-of-staff/module-2-deploy/) | Package and deploy the agent to AgentCore Runtime (Container/ECR), invoke over HTTP |
| [3 — Memory](foundations/build-an-ai-chief-of-staff/module-3-memory/) | Add cross-session memory with AgentCore Memory (short-term events + long-term extraction) |
| [4 — Observability](foundations/build-an-ai-chief-of-staff/module-4-observability/) | Trace agent execution in CloudWatch GenAI dashboards via OpenTelemetry |

### Advanced — Agentic Analytics (optional)

A text-to-SQL agent that queries a Student Analytics dataset on Athena. Requires the Athena/S3 infrastructure set up in Module 0.

| Module | What you learn |
|--------|---------------|
| [0 — Setup](advanced/agentic-analytics/module-0-setup/) | Provision S3, Glue catalog, and Athena tables for the demo dataset |
| [1 — Local Agent](advanced/agentic-analytics/module-1-local-agent/) | Build a BI agent that translates natural language to SQL |
| [2 — Deploy + Observe](advanced/agentic-analytics/module-2-deploy/) | Full CLI lifecycle: create, deploy, invoke, and trace the agent |
| [3 — Follow-up](advanced/agentic-analytics/module-3-follow-up/) | Handle ambiguous queries with clarification questions and session resume |

## Prerequisites

- AWS account with Amazon Bedrock model access to the Claude models set in each module's `.env.example` (foundations: Claude Sonnet 5.5 and Claude Haiku 5.5; advanced: Claude Opus 4.6 and Claude Haiku 4.5)
- AWS CLI configured with appropriate credentials
- Python 3.11
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Node.js 20+ (for the `@aws/agentcore` CLI)

## Getting started

Each module is self-contained with its own virtual environment. To start a module:

```bash
cd foundations/build-an-ai-chief-of-staff/module-1-local-agent
./setup.sh          # installs deps, registers Jupyter kernel
```

Then open the module's notebook (e.g. `module-1-local-agent.ipynb`) and follow along.

## Key design decisions

- **Bedrock, not the Anthropic API** — model selection comes from environment variables (`ANTHROPIC_MODEL` + `CLAUDE_CODE_USE_BEDROCK=1`), not hardcoded in agent code.
- **Container builds** — the Claude Agent SDK bundles a native CLI that requires correct permissions and architecture; Container builds (`pip install` on Linux/arm64) handle this correctly where CodeZip cannot.
- **Single source of truth** — each track has one `build_agent_options()` function shared across all modules; drift-guard tests enforce byte-identical copies.
- **`@aws/agentcore` CLI** — all deployment uses the current npm CLI (`agentcore create/deploy/invoke/remove`), not the deprecated starter toolkit.
