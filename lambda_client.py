import os
import asyncio
import logging
from typing import Optional
from dotenv import load_dotenv
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from lambda_client_adapter import LambdaMcpAdapter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def main(user_query: Optional[str] = None):
    """
    Main function to run the agent with Lambda-based MCP services.
    
    Args:
        user_query: Optional query to process. If not provided, runs in interactive mode.
        
    Returns:
        If user_query is provided, returns the agent's response.
    """
    try:
        # Configure Gemini model
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is not set")
        
        logger.info("Initializing Gemini model")
        model = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=api_key
        )

        # Get API Gateway URL from environment or use default
        api_gateway_url = os.environ.get("API_GATEWAY_URL", "http://localhost:3000")
        
        # Setup Lambda MCP adapter
        logger.info(f"Initializing Lambda MCP adapter with API Gateway URL: {api_gateway_url}")
        adapter = LambdaMcpAdapter(api_gateway_url)
        
        # Get tools from adapter
        tools = adapter.get_tools()
        logger.info(f"Loaded {len(tools)} tools from adapter")
        
        # Create langgraph react agent
        logger.info("Creating agent")
        agent = create_react_agent(model, tools)

        if user_query:
            # For programmatic use or testing
            logger.info(f"Processing query: {user_query}")
            response = await agent.ainvoke({"messages": [{"role": "user", "content": user_query}]})
            return response['messages'][-1]['content']
        else:
            # Interactive mode
            print("=" * 50)
            print("Agent ready! Type 'exit' to quit.")
            print(f"Using API Gateway at: {api_gateway_url}")
            print("=" * 50)
            
            while True:
                query = input("\nYou: ")
                if query.lower() == "exit":
                    break
                if not query.strip():
                    continue
                    
                try:
                    logger.info(f"Processing interactive query: {query}")
                    response = await agent.ainvoke({"messages": [{"role": "user", "content": query}]})
                    print(f"\nAgent: {response['messages'][-1]['content']}")
                except Exception as e:
                    logger.error(f"Error processing query: {str(e)}")
                    print(f"\nError: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")
        if user_query:
            raise
        else:
            print(f"Error initializing agent: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 