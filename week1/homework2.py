"""
    # Week 1 Homework — Agents & Tools with LangChain + OpenRouter

    Improve th class example. Your different models if necessary like openrouter:openai/gpt-oss-120b:free.

    ## Task 2 — A tool that actually computes something

    Real tools do real work. Write a tool that does a genuine calculation (not a hardcoded
    string):

    ```python
    def convert_currency(amount: float, rate: float) -> str:
        ```Convert an amount using a given exchange rate.```
        ...
    ```

    - It must take **two arguments** and return a clear sentence with the computed result.
    - Ask the agent something like:
    *"I have 100 euros and the rate is 1.08 — how many dollars is that?"*
    - Verify the number in the answer is correct (108.0).
"""
from dotenv import load_dotenv
from langchain.agents import create_agent
import os

load_dotenv()

openrouterkey = os.getenv('OPENROUTER_API_KEY')

def convert_currency(amount: float, rate: float) -> str:
    """Convert an amount using a given exchange rate."""
    converted = amount * rate
    return f"{amount} at an exchange rate of {rate} equals {converted}."


agent = create_agent(
    model="openrouter:anthropic/claude-3.5-haiku",
    tools=[convert_currency],
    system_prompt="You are a helpful assistant",
)

result = agent.invoke(
    {"messages": [{"role": "user", "content": "I have 100 euros and the rate is 1.08 — how many dollars is that?"}]}
)

print(result)