"""
Chief of Staff Agent

Run from a terminal, from the module directory (reads its .env: CLAUDE_CODE_USE_BEDROCK,
ANTHROPIC_MODEL, ANTHROPIC_SMALL_FAST_MODEL, AWS_REGION, AWS_PROFILE):

    cd module-1-local-agent
    uv run python chief_of_staff_agent/agent.py "What is our current runway?"
    uv run python chief_of_staff_agent/agent.py --continue "And if we hire 3 more engineers?"
    uv run python chief_of_staff_agent/agent.py --output-style executive "Summarise our burn rate"
"""

import argparse
import asyncio
import json
import os
import sys
from collections.abc import Callable
from typing import Any, Literal

from dotenv import load_dotenv

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient
from claude_agent_sdk import AssistantMessage, ResultMessage, TextBlock, ToolResultBlock, ToolUseBlock

load_dotenv()


# The agent's "identity" — the single source of truth, shared by the local
# send_query() path (Module 1) and the AgentCore entrypoint (Module 2+).
SYSTEM_PROMPT = """You are the Chief of Staff for TechStart Inc, a 50-person startup.

        Apart from your tools and two subagents, you also have custom Python scripts in the scripts/ directory you can run with Bash:
        - python scripts/financial_forecast.py: Advanced financial modeling
        - python scripts/talent_scorer.py: Candidate scoring algorithm
        - python scripts/decision_matrix.py: Strategic decision framework

        You have access to company data in the financial_data/ directory.
        """

# The agent's working directory — the bundle root (CLAUDE.md, .claude/, scripts/,
# financial_data/ all live here and are loaded from disk via setting_sources).
AGENT_DIR = os.path.dirname(os.path.abspath(__file__))


def build_agent_options(
    *,
    continue_conversation: bool = False,
    permission_mode: Literal["default", "plan", "acceptEdits"] = "default",
    output_style: str | None = None,
    extra_tools: list[str] | None = None,
    system_prompt_suffix: str | None = None,
    **overrides: Any,
) -> ClaudeAgentOptions:
    """Build the agent's ClaudeAgentOptions — the single source of truth.

    Both the local ``send_query()`` and the AgentCore entrypoint call this, so the
    agent's identity (system prompt, tools, cwd, setting_sources) is defined in one
    place. Later modules override defaults rather than forking:

    - ``extra_tools``: append tools (e.g. Module 3 memory tools).
    - ``system_prompt_suffix``: append text to the system prompt (e.g. Module 3
      injects recalled memory here) without replacing the canonical prompt — keeps
      prompt assembly inside this single source of truth.
    - ``**overrides``: override any ClaudeAgentOptions field (e.g. ``max_turns=50``).

    No ``model=`` is set — this workshop runs on Amazon Bedrock and the model comes
    from the ``ANTHROPIC_MODEL`` env var (with ``CLAUDE_CODE_USE_BEDROCK=1``).
    """
    tools = ["Agent", "Read", "Write", "Edit", "Bash"]  # "Agent" was called "Task" in older Claude Code
    if extra_tools:
        tools = tools + extra_tools

    system_prompt = SYSTEM_PROMPT + (system_prompt_suffix or "")

    defaults: dict[str, Any] = dict(
        allowed_tools=tools,
        system_prompt=system_prompt,
        continue_conversation=continue_conversation,
        permission_mode=permission_mode,
        cwd=AGENT_DIR,
        settings=json.dumps({"outputStyle": output_style}) if output_style else None,
        # IMPORTANT: setting_sources must include "project" to load filesystem settings:
        # CLAUDE.md, skills (.claude/skills), subagents (.claude/agents), slash
        # commands (.claude/commands), output styles, and hooks (.claude/settings.json).
        # Without this, the SDK runs in isolation mode with no filesystem settings.
        setting_sources=["project"],
    )
    defaults.update(overrides)  # callers override any field
    return ClaudeAgentOptions(**defaults)


def print_activity(msg: Any) -> None:
    """Print activity to console: model text, tool calls and results, final cost"""

    def short(text: Any) -> str:  # one line, max 120 chars, paths relative to the agent dir
        return " ".join(str(text).replace(AGENT_DIR, ".").split())[:120]

    indent = "    " if getattr(msg, "parent_tool_use_id", None) else ""  # subagent activity
    for block in msg.content if isinstance(getattr(msg, "content", None), list) else []:
        if isinstance(block, TextBlock) and isinstance(msg, AssistantMessage):
            print(f"{indent}💬 {short(block.text)}")
        elif isinstance(block, ToolUseBlock):
            print(f"{indent}🔧 {block.name}: {short(json.dumps(block.input))}")
        elif isinstance(block, ToolResultBlock):
            print(f"{indent}{'❌' if block.is_error else '✓'} {short(block.content)}")
    if isinstance(msg, ResultMessage):
        print(f"🏁 Done in {msg.duration_ms / 1000:.1f}s, {msg.num_turns} turns, ${msg.total_cost_usd or 0:.4f}")


async def send_query(
    prompt: str,
    continue_conversation: bool = False,
    permission_mode: Literal["default", "plan", "acceptEdits"] = "default",
    output_style: str | None = None,
    activity_handler: Callable[[Any], None | Any] = print_activity,
) -> tuple[str | None, list]:
    """
    Send a query to the Chief of Staff agent with all features integrated.

    Args:
        prompt: The query to send (can include slash commands like /budget-impact)
        activity_handler: Callback for activity updates (default: print_activity)
        continue_conversation: Continue the previous conversation if True
        permission_mode: "default" (execute), "plan" (think only), or "acceptEdits"
        output_style: Override output style (e.g., "executive", "technical", "board-report")

    Returns:
        Tuple of (result, messages) - result is the final text, messages is the full conversation

    Features automatically included/leveraged:
        - Memory: CLAUDE.md context loaded from chief_of_staff/CLAUDE.md
        - Subagents: financial-analyst and recruiter via the Agent tool, formerly Task (defined in .claude/agents)
        - Custom scripts: Python scripts in tools/ via Bash
        - Slash commands: Expanded from .claude/commands/
        - Output styles: Custom output styles defined in .claude/output-styles
        - Hooks: Triggered based on settings.json, defined in .claude/hooks
    """

    # Agent identity lives in build_agent_options() — the single source of truth
    # shared with the AgentCore entrypoint (Module 2+).
    options = build_agent_options(
        continue_conversation=continue_conversation,
        permission_mode=permission_mode,
        output_style=output_style,
    )

    result = None
    messages = []  # this is to append the messages ONLY for this agent turn

    try:
        async with ClaudeSDKClient(options=options) as agent:
            await agent.query(prompt=prompt)
            async for msg in agent.receive_response():
                messages.append(msg)
                if asyncio.iscoroutinefunction(activity_handler):
                    await activity_handler(msg)
                else:
                    activity_handler(msg)

                if hasattr(msg, "result"):
                    result = msg.result
    except Exception as e:
        print(f"❌ Query error: {e}")
        raise

    return result, messages


def _main() -> None:
    """Command-line entrypoint: run one query with send_query() and print the answer."""
    styles_dir = os.path.join(AGENT_DIR, ".claude", "output-styles")
    styles = sorted(f.removesuffix(".md") for f in os.listdir(styles_dir) if f.endswith(".md"))

    parser = argparse.ArgumentParser(description="Ask the Chief of Staff agent a question.")
    parser.add_argument(
        "prompt", nargs="+", help="the query (quotes optional; slash commands like /budget-impact work)"
    )
    parser.add_argument(
        "--continue",
        dest="continue_conversation",
        action="store_true",
        help="continue the most recent conversation of this agent",
    )
    parser.add_argument(
        "--output-style", metavar="NAME", help=f"output style from .claude/output-styles: {', '.join(styles)}"
    )
    parser.add_argument(
        "--permission-mode",
        choices=["default", "plan", "acceptEdits"],
        default="default",
        help='"default" (execute, the default), "plan" (think only) or "acceptEdits"',
    )
    args = parser.parse_args()

    # The agent runs `python scripts/...` via Bash: put this interpreter's bin dir
    # (e.g. .venv/bin) first on PATH so that works without an activated venv.
    os.environ["PATH"] = os.path.dirname(sys.executable) + os.pathsep + os.environ.get("PATH", "")

    result, _ = asyncio.run(
        send_query(
            " ".join(args.prompt),
            continue_conversation=args.continue_conversation,
            permission_mode=args.permission_mode,
            output_style=args.output_style,
        )
    )
    if result is None:
        print("No result returned by the agent.", file=sys.stderr)
        sys.exit(1)
    print(f"\n{'─' * 60}\n{result}")


if __name__ == "__main__":
    _main()
