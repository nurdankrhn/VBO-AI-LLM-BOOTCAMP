import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from deepagents import create_deep_agent
from langchain.agents import create_agent

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

agent = create_deep_agent(
        model=make_model(),
        tools=[],
        system_prompt=(
            "You are a careful assistant. For any multi-step request, first write "
            "a short plan with write_todos, then carry it out, using the filesystem "
            "tools to save your work."
        ),
    )


task = (
        "Draft a customer support FAQ for our SaaS product. Write three separate "
        "files — billing.md, account.md and api.md — each containing two Q&A pairs "
        "for that topic. Then combine all three into a single faq.md."
    )

result = agent.invoke({"messages": [{"role": "user", "content": task}]})

print(result)