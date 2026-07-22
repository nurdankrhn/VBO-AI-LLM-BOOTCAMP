import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from deepagents import create_deep_agent

load_dotenv()


def make_model():
    # Claude Haiku 4.5 via OpenRouter (deepagents is Claude-native). See
    # main1_quickstart.py for why.
    return init_chat_model(
        "openai:anthropic/claude-haiku-4.5",
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
        max_tokens=4000,
    )


agent = create_deep_agent(
        model=make_model(),
        tools=[],
        system_prompt=(
            "You are a planning-first assistant. Start by calling write_todos to "
            "record the steps, mark each one in_progress then completed as you do "
            "it, and finish with a one-sentence summary of what you did."
        ),
    )

task = (
        "Prepare an onboarding pack for a backend engineer who starts next week. "
        "It should cover setting up the dev environment, our git workflow, and who "
        "to contact for what. Finish with an index.md that links to each part."
    )

def stream_agent(agent, task: str) -> None:
    """Stream the agent live instead of blocking on invoke().

    Two stream modes at once:
      - "messages": the LLM's text tokens as they are generated
      - "updates":  each node's finished output, so we can announce tool calls
                    (write_todos, write_file, ...) the moment they happen
    LangGraph yields (mode, payload) tuples when stream_mode is a list.
    """
    for mode, payload in agent.stream(
        {"messages": [{"role": "user", "content": task}]},
        stream_mode=["updates", "messages"],
    ):
        if mode == "messages":
            chunk, _metadata = payload
            text = getattr(chunk, "content", "")
            # Some providers return a list of content blocks instead of a string.
            if isinstance(text, list):
                text = "".join(
                    b.get("text", "") for b in text if isinstance(b, dict)
                )
            if text:
                print(text, end="", flush=True)

        elif mode == "updates":
            for _node, update in (payload or {}).items():
                for msg in (update or {}).get("messages", []) or []:
                    for tc in getattr(msg, "tool_calls", None) or []:
                        print(f"\n🔧 {tc['name']}({tc['args']})\n", flush=True)

    print()  # final newline


stream_agent(agent, task)