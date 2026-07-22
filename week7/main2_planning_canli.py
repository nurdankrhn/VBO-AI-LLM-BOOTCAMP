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

result = agent.invoke({"messages": [{"role": "user", "content": task}]})

print(result)