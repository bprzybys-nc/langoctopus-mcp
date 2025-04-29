import asyncio
from client import main

async def test_agent():
    # Example test queries
    test_queries = [
        "What is 5 + 7?",
        "What is 8 * 9?",
        "What's the weather in London?",
        "What's the 2-day forecast for Tokyo?",
        "Multiply 12 by 6 and tell me the weather in Paris.",
        "Calculate the derivative of x²"  # Should return error or fallback
    ]
    
    for query in test_queries:
        print(f"\nTesting: {query}")
        try:
            response = await main(query)
            print(f"Response: {response}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_agent()) 