r"""
Week 7 — Part 1: Deep Agent quickstart.

The smallest possible deep agent: one `create_deep_agent(...)` call, no custom
tools. We give it a small multi-step task and watch the BUILT-IN tools fire —
write_todos to plan, then the filesystem tools to do the work.

Prerequisites:
  - uv add deepagents
  - OPENROUTER_API_KEY in .env

Run:
    uv run python week_07/main1_quickstart.py
"""

import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from deepagents import create_deep_agent

load_dotenv()


def make_model():
    # Claude Haiku 4.5 via OpenRouter. deepagents is Claude-native, so Claude
    # drives the planning / filesystem / sub-agent loop reliably. Cap max_tokens
    # — deepagents defaults to 65535, which is needlessly expensive.
    return init_chat_model(
        "openai:anthropic/claude-haiku-4.5",
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
        max_tokens=4000,
    )


def main():
    # No tools of our own — the deep agent already has write_todos, the
    # filesystem tools, task, execute, etc. built in.
    agent = create_deep_agent(
        model=make_model(),
        tools=[],
        system_prompt=(
            "You are a careful assistant. For any multi-step request, first write "
            "a short plan with write_todos, then carry it out, using the filesystem "
            "tools to save your work."
        ),
    )

    # A realistic task where the FILESYSTEM IS ACTUALLY NEEDED: the agent drafts
    # three separate documents, then has to READ THEM BACK to assemble the final
    # one. Composing from parts is why write_file/read_file exist — not "write a
    # file and then re-read what you just wrote".
    task = (
        "Draft a customer support FAQ for our SaaS product. Write three separate "
        "files — billing.md, account.md and api.md — each containing two Q&A pairs "
        "for that topic. Then combine all three into a single faq.md."
    )

    result = agent.invoke({"messages": [{"role": "user", "content": task}]})

    # 1) Which built-in tools did the model actually call?
    tool_calls = [
        c["name"]
        for m in result["messages"]
        for c in (getattr(m, "tool_calls", None) or [])
    ]
    print("Tools the agent used:", tool_calls)

    # 2) The virtual filesystem lives in result["files"] — IN MEMORY, not on disk.
    #    The default backend is StateBackend, so "/faq.md" is a path inside
    #    the agent's virtual filesystem, NOT your real filesystem root. Nothing was
    #    written to your disk, and it disappears when this process exits.
    #    (To write real files, use FilesystemBackend — see main3_filesystem.py.)
    files = result.get("files", {})
    print("Files created (virtual, in agent state):", list(files.keys()))

    # Each value is a dict: {"content": ..., "encoding": ..., "created_at": ...}
    for path, entry in files.items():
        content = entry["content"] if isinstance(entry, dict) else entry
        print(f"\n--- contents of {path} ---")
        print(content)
        print("--- end ---")

    # 3) The final answer.
    print("\nFinal answer:\n" + result["messages"][-1].content)


    # 4) all result
    # print(result)


if __name__ == "__main__":
    main()