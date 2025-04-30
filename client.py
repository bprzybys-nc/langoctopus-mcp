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
            
            # Get the last message, which should contain the final response
            if response and isinstance(response, dict) and 'messages' in response and isinstance(response['messages'], list) and len(response['messages']) > 0:
                last_message = response['messages'][-1]
                
                # Extract content based on whether it's an AIMessage or dict
                if hasattr(last_message, 'content'):
                    return last_message.content # Handle AIMessage
                elif isinstance(last_message, dict) and 'content' in last_message:
                     return last_message['content'] # Handle dict message
                else:
                    print(f"Error: Could not extract content from last message. Type: {type(last_message)}, Value: {last_message}")
                    return "Error: Could not parse final message content."
            else:
                 # If the structure is unexpected (e.g., not a dict, no 'messages' key)
                 print(f"Error: Unexpected agent response structure: {type(response)} - {response}")
                 return "Error: Could not parse agent response structure."
        else:
            # Interactive mode
            print("Agent ready! Type 'exit' to quit.")
            while True:
                query = input("\nYou: ")
                if query.lower() == "exit":
                    break
                try:
                    response = await agent.ainvoke({"messages": [{"role": "user", "content": query}]})
                    print(f"\nAgent: {response.content}")
                except Exception as e:
                    print(f"\nError: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 