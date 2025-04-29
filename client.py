import os
import asyncio
from dotenv import load_dotenv
from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables
load_dotenv()

async def main(user_query=None):
    # Configure Gemini 2.5 Flash
    model = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=os.environ.get("GOOGLE_API_KEY")
    )

    # Setup multi-server client
    async with MultiServerMCPClient({
        "math": {
            "command": "python",
            "args": ["math_server.py"],
            "transport": "stdio"
        },
        "weather": {
            "url": "http://localhost:8000/sse",
            "transport": "sse"
        }
    }) as client:
        # Create and run agent
        tools = client.get_tools()
        agent = create_react_agent(model, tools)

        if user_query:
            # For programmatic use or testing
            response = await agent.ainvoke({"messages": [{"role": "user", "content": user_query}]})
            return response['messages'][-1]['content']
        else:
            # Interactive mode
            print("Agent ready! Type 'exit' to quit.")
            while True:
                query = input("\nYou: ")
                if query.lower() == "exit":
                    break
                try:
                    response = await agent.ainvoke({"messages": [{"role": "user", "content": query}]})
                    print(f"\nAgent: {response['messages'][-1]['content']}")
                except Exception as e:
                    print(f"\nError: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 