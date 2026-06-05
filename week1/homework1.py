"""
    # Week 1 Homework — Agents & Tools with LangChain + OpenRouter

    Improve th class example. Your different models if necessary like openrouter:openai/gpt-oss-120b:free.

    ## Task 1 — A second tool

    Add a **second** tool alongside `get_weather`:

    - `get_time(city: str) -> str` — return a (fake is fine) current time string for the city,
    e.g. `"The local time in Istanbul is 14:30."`

    Give **both** tools to the agent. Then ask a question that needs both, for example:

    > "What's the weather and the local time in Istanbul?"

    Print the result and confirm the agent called *both* tools.
"""
from dotenv import load_dotenv
from langchain.agents import create_agent
import os
from datetime import datetime
from zoneinfo import ZoneInfo

load_dotenv()

openrouterkey = os.getenv('OPENROUTER_API_KEY')

def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"

def get_time(city: str) -> str:
    """Get current time for a given city."""
    currentTime = datetime.now(ZoneInfo(f"Europe/{city}"))
    return currentTime.strftime("%Y-%m-%d %H:%M:%S")


agent = create_agent(
    model="openrouter:anthropic/claude-3.5-haiku",
    tools=[get_weather,get_time ],
    system_prompt="You are a helpful assistant",
)

result = agent.invoke(
    {"messages": [{"role": "user", "content": "What's the weather and the local time in Istanbul?"}]}
)

print(result)