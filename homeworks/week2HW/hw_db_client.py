import asyncio

from dotenv import load_dotenv

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
import os
from pathlib import Path
from langchain_openai import ChatOpenAI

load_dotenv()


BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env", override=True)

model = ChatOpenAI(
    model="openai/gpt-4o-mini",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    temperature=0,
    max_tokens=1000,
)


async def main():

    client = MultiServerMCPClient(
        {
            "database": {
                "transport": "streamable_http",
                "url": "http://localhost:8001/mcp",
            }
        }
    )

    tools = await client.get_tools()

    print("\nLoaded tools:")
    for tool in tools:
        print(f"- {tool.name}")

    agent = create_agent(model, tools)

    response = await agent.ainvoke(
        {
            "messages": [
                {
                    "role": "system",
                    "content": """
    You are a database assistant.

    Before writing any SQL:

    1. Call list_tables.
    2. Call describe_table for every relevant table.
    3. Discover foreign keys.
    4. Only then call run_select.

    Never guess table names or column names.
    Always inspect the schema first.
    """
                },
                {
                    "role": "user",
                    "content":
                    "Engineering departmanındaki en yüksek maaşlı çalışanın adını ve maaşını ver."
                }
            ]
        }
    )

    print("\n===== MESSAGE TRACE =====\n")

    #for debugging purposes, print the entire message trace
    #for msg in response["messages"]:
    #    print(msg)
    #    print()

    print(response["messages"][-1].content)

if __name__ == "__main__":
    asyncio.run(main())