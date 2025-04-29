from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Weather")

@mcp.tool()
def get_weather(location: str) -> str:
    """Get weather for a location"""
    # Placeholder for real API call
    return f"It's currently sunny and 22°C in {location}."

@mcp.tool()
def get_forecast(location: str, days: int = 3) -> str:
    """Get weather forecast for a location for the next few days"""
    # Placeholder for real API call
    weather_patterns = [
        "sunny with occasional clouds",
        "partly cloudy with light rain",
        "overcast with heavy rain",
        "clear skies with strong winds",
        "thunderstorms in the afternoon",
        "foggy in the morning, clearing later",
        "scattered showers throughout the day",
        "hazy with moderate humidity",
        "breezy with light drizzle",
        "mostly sunny with isolated storms",
        "cloudy with chance of rain",
        "windy with clear skies",
        "misty with light showers"
    ]
    import random
    pattern = random.choice(weather_patterns)
    return f"{days}-day forecast for {location}: Expect mild temperatures around 20-25°C with {pattern}."

if __name__ == "__main__":
    mcp.run(transport="sse", port=8000) 