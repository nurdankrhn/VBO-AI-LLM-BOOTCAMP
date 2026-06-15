import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv

load_dotenv()


# Initialize the model
model = init_chat_model(
    model="gemini-2.5-flash-lite", 
    model_provider="google_genai", 
    max_tokens=300
)

async def demonstrate_multi_server_mcp():
    client = MultiServerMCPClient({
                
            # Remote weather server using HTTP transport
            # Note: You need to run main2_http_server.py separately
            "weather": {
                "transport": "streamable_http",
                "url": "http://localhost:8000/mcp"
            }
        })

    tools = await client.get_tools()

    # for tool in tools:
    #     print(f"   - {tool.name}: {tool.description}")

    agent = create_agent(model, tools)

    weather_response = await agent.ainvoke({
            "messages": [
                {"role": "user", "content": "2026 NATO zirvesi hangi ülkede yapılacak?"}
            ]
        })
    print(f"Result: {weather_response}")

if __name__=='__main__':
    asyncio.run(demonstrate_multi_server_mcp())