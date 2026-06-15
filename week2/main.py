
from langchain.tools import tool
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from models import WeatherInput
from dotenv import load_dotenv
import json

load_dotenv()


model = init_chat_model(model="gemini-2.5-flash-lite", model_provider="google_genai", max_tokens=500)

@tool
def search_database(query: str, limit: int = 10) -> str:
    """Search the customer database for records matching the query.

    Args:
        query: Search terms to look for
        limit: Maximum number of results to return
    """
    
    customers = ["Alice Johnson", "Bob Smith", "Charlie Brown", "Diana Wilson"]
    matches = [c for c in customers if query.lower() in c.lower()][:limit]
    
    return f"Found {len(matches)} customers: {', '.join(matches)}"


@tool("calculator", description="Performs arithmetic calculations. Use this for any math problems.")
def calc(expression: str) -> str:
    """Evaluate mathematical expressions."""
    try:
        allowed = "0123456789+-*/(). "
        if all(c in allowed for c in expression):
            return f"{expression} = {eval(expression)}"
        else:
            return "Error: Only basic math operations allowed"
    except:
        return "Error: Invalid expression"

@tool(args_schema=WeatherInput)
def get_weather(location: str, units: str = "celsius") -> str: # , include_forecast: bool = False
    """Get current weather and optional forecast."""
    
    temp = 22 if units == "celsius" else 72
    result = f"Current weather in {location}: {temp}° {units.title()}"

    if include_forecast:
        result += "\n5-day forecast: Sunny, Cloudy, Rainy, Sunny, Partly Cloudy"

    return result

agent = create_agent(
        model=model,
        tools=[search_database, calc, get_weather],
        system_prompt=""
    )

result = agent.invoke({"messages": "Get weather for Tokyo in fahrenheit with forecast"})

print(f"Agent: {result}\n")