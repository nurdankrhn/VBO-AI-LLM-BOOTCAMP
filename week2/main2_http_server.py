import asyncio
import random
from datetime import datetime
from mcp.server.fastmcp import FastMCP
from langchain_tavily import TavilySearch
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP("Weather")

@mcp.tool()
async def get_weather(location: str) -> str:
    """
    Get current weather for a given location.
    
    In a real implementation, this would call a weather API like OpenWeatherMap.
    For demo purposes, we return mock data.
    """
    # Simulate API call delay
    await asyncio.sleep(0.5)
    
    # Mock weather data
    weather_conditions = ["sunny", "cloudy", "rainy", "snowy", "foggy"]
    temperatures = list(range(-10, 35))
    
    condition = random.choice(weather_conditions)
    temp = random.choice(temperatures)
    
    result = f"Weather in {location}: {condition.title()}, {temp}°C"
    print(f"[MCP Weather Server] {result}")
    return result

@mcp.tool()
async def get_forecast(location: str, days: int = 3) -> str:
    """
    Get weather forecast for a given location and number of days.
    
    Args:
        location: The city or location to get forecast for
        days: Number of days to forecast (default: 3, max: 7)
    """
    # Validate days parameter
    days = min(max(days, 1), 7)  # Clamp between 1 and 7
    
    # Simulate API call delay
    await asyncio.sleep(1.0)
    
    forecast_data = []
    weather_conditions = ["sunny", "cloudy", "rainy", "partly cloudy", "thunderstorms"]
    
    for day in range(days):
        date_str = datetime.now().strftime(f"%Y-%m-%d +{day}d")
        condition = random.choice(weather_conditions)
        high_temp = random.randint(15, 30)
        low_temp = random.randint(5, high_temp - 5)
        
        forecast_data.append(f"Day {day + 1}: {condition.title()}, High: {high_temp}°C, Low: {low_temp}°C")
    
    result = f"Weather forecast for {location} ({days} days):\n" + "\n".join(forecast_data)
    print(f"[MCP Weather Server] Generated {days}-day forecast for {location}")
    return result

@mcp.tool()
async def get_weather_alerts(location: str) -> str:
    """
    Get weather alerts and warnings for a given location.
    """
    # Simulate API call delay
    await asyncio.sleep(0.3)
    
    # Mock alerts (in real implementation, this would come from weather service)
    alert_types = [
        "No active alerts",
        "Heavy rain warning until 6 PM",
        "High wind advisory in effect",
        "Heat wave warning for next 3 days",
        "Winter storm watch issued"
    ]
    
    alert = random.choice(alert_types)
    result = f"Weather alerts for {location}: {alert}"
    print(f"[MCP Weather Server] {result}")
    return result


# Create the Tavily search tool once and reuse it across calls.
search = TavilySearch(
    max_results=5,
    topic="general",
    # include_answer=False,
    # include_raw_content=False,
    # include_images=False,
    # include_image_descriptions=False,
    # search_depth="basic",
    # time_range="day",
    # start_date=None,
    # end_date=None,
    # include_domains=None,
    # exclude_domains=None,
    # include_usage= False
)


@mcp.tool()
async def search_internet(query: str) -> str:
    """Use web search to find accurate, up-to-date information.

    Args:
        query: The search query / question to look up on the web.
    """
    # Actually run the search and return the results (not the tool object).
    result = await search.ainvoke({"query": query})
    print(f"[MCP Weather Server] Web search for: {query!r}")
    return str(result)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")