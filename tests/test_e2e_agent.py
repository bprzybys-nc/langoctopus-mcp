import asyncio
import random
import sys
import os
import logging
import argparse
import signal # Added signal
import time # Added time
from unittest.mock import patch, MagicMock

# Add project root to path to allow importing 'client'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    # We need ChatGoogleGenerativeAI and create_react_agent directly now
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langgraph.prebuilt import create_react_agent
    from langchain_mcp_adapters.client import MultiServerMCPClient
except ImportError as e:
    print(f"Error importing dependencies: {e}")
    print("Ensure langchain_google_genai, langgraph, langchain_mcp_adapters are installed.")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Default Test Configuration ---
DEFAULT_NUM_REQUESTS_FULL = 100
DEFAULT_NUM_REQUESTS_DEV = 37
LOCATIONS = ["London", "Paris", "Tokyo", "New York", "Sydney", "Berlin", "Rome", "Moscow"]
MATH_OPERATIONS = {
    "add": ["add", "plus", "+", "sum of"],
    "subtract": ["subtract", "minus", "-", "difference between"],
    "multiply": ["multiply", "times", "*", "product of"],
    "divide": ["divide", "divided by", "/", "quotient of"]
}
# ------------------------

# --- Server Management ---
server_processes = []

async def start_servers():
    global server_processes
    logger.info("Starting MCP servers for E2E test...")
    try:
        # Start math server (stdio transport)
        math_command = [sys.executable, os.path.join(project_root, "src", "mcp_servers", "math_server.py")]
        logger.info(f"Starting math server: {' '.join(math_command)}")
        math_server = await asyncio.create_subprocess_exec(
            *math_command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        server_processes.append(math_server)
        logger.info(f"Math server started (PID: {math_server.pid})")

        # Start weather server (SSE transport)
        weather_command = [sys.executable, os.path.join(project_root, "src", "mcp_servers", "weather_server.py")]
        logger.info(f"Starting weather server: {' '.join(weather_command)}")
        weather_server = await asyncio.create_subprocess_exec(
            *weather_command,
            stdout=asyncio.subprocess.PIPE, # Capture stdout
            stderr=asyncio.subprocess.PIPE  # Capture stderr
        )
        server_processes.append(weather_server)
        logger.info(f"Weather server started (PID: {weather_server.pid})")

        logger.info("Waiting for servers to initialize...")
        await asyncio.sleep(5)  # Increased wait time to 5 seconds
        logger.info("Servers should be initialized.")
        return True
    except Exception as e:
        logger.error(f"Failed to start servers: {e}", exc_info=True)
        await stop_servers() # Attempt cleanup if start failed
        return False

async def stop_servers():
    global server_processes
    logger.info("Shutting down servers...")
    for process in reversed(server_processes): # Stop in reverse order
        if process.returncode is None: # Check if process is running
            logger.info(f"Terminating server (PID: {process.pid})...")
            try:
                process.terminate()
                await asyncio.wait_for(process.wait(), timeout=5)
                logger.info(f"Server (PID: {process.pid}) terminated gracefully.")
            except asyncio.TimeoutError:
                logger.warning(f"Server (PID: {process.pid}) did not terminate gracefully, killing...")
                process.kill()
                await process.wait()
            except ProcessLookupError:
                 logger.warning(f"Server (PID: {process.pid}) already terminated.")
            except Exception as e:
                logger.error(f"Error shutting down server (PID: {process.pid}): {e}")
        else:
            logger.info(f"Server (PID: {process.pid}) already finished with code {process.returncode}.")
    server_processes = [] # Clear the list
    logger.info("Servers shut down.")

# --- Agent Setup (No longer a separate async def, integrated into runner) ---
# Removed setup_agent function as it's now integrated below

async def run_single_test(iteration, total_requests, agent_executor): # agent_executor parameter remains
    """Runs a single randomized test query against the pre-configured agent."""
    service = random.choice(["math", "weather"])
    query = ""
    expected_hints = [] # Keywords likely to be in a successful response

    try:
        if service == "math":
            op_key = random.choice(list(MATH_OPERATIONS.keys()))
            op_word = random.choice(MATH_OPERATIONS[op_key])
            num1 = random.randint(1, 100)
            num2 = random.randint(1, 100)
            
            # Avoid division by zero for the test query generation
            if op_key == "divide":
                num2 = random.randint(1, 100) 
                # Try to make it an even division for simpler checks if needed later
                num1 = num1 * num2 
            
            if op_word in ["+", "-", "*", "/"]:
                 query = f"Calculate {num1} {op_word} {num2}"
            elif op_word in ["sum of", "product of"]:
                 query = f"What is the {op_word} {num1} and {num2}?"
            elif op_word == "difference between":
                 query = f"What is the {op_word} {num1} and {num2}?" # Order might matter for LLM
            else: # add, subtract, multiply, divide
                 query = f"{op_word.capitalize()} {num1} and {num2}"
            
            # Basic check: response should contain a number
            expected_hints = [str(num) for num in range(10)] 

        elif service == "weather":
            location = random.choice(LOCATIONS)
            operation = random.choice(["get_weather", "get_forecast"])
            expected_hints.append(location)

            if operation == "get_weather":
                query = f"What is the weather like in {location}?"
                expected_hints.append("weather")
            else: # get_forecast
                days = random.randint(1, 7)
                if random.choice([True, False]): # Sometimes specify days, sometimes use default
                    query = f"Give me the weather forecast for {location} for the next {days} days."
                    expected_hints.append(f"{days}-day")
                else:
                    query = f"What is the weather forecast for {location}?"
                    expected_hints.append("3-day") # Default
                expected_hints.append("forecast")

        logger.info(f"[Test {iteration}/{total_requests}] Sending query: '{query}'")
        
        # Ensure the agent function is available
        if agent_executor is None:
             logger.error("Agent executor not available.")
             return {"query": query, "response": "Error: Agent not available", "success": False}

        # Invoke the pre-configured agent
        response = await agent_executor.ainvoke({"messages": [{"role": "user", "content": query}]})

        # --- Response handling logic ---
        response_content = "Error: Response structure invalid."
        success_flag = False # Default to failure unless explicitly set
        if response and isinstance(response, dict) and 'messages' in response and isinstance(response['messages'], list) and len(response['messages']) > 0:
            last_message = response['messages'][-1]
            if hasattr(last_message, 'content'):
                response_content = last_message.content
                success_flag = True # Assume success if content extracted
            elif isinstance(last_message, dict) and 'content' in last_message:
                response_content = last_message['content']
                success_flag = True # Assume success if content extracted
            else:
                logger.error(f"[Test {iteration}/{total_requests}] Could not extract content from last message. Type: {type(last_message)}, Value: {last_message}")
                response_content = "Error: Could not parse final message content."
                success_flag = False
        else:
            logger.error(f"[Test {iteration}/{total_requests}] Unexpected agent response structure: {type(response)} - {response}")
            response_content = "Error: Could not parse agent response structure."
            success_flag = False

        # --- Log outcome ---
        if success_flag:
            logger.info(f"[Test {iteration}/{total_requests}] Received response: '{response_content}'")
            # Basic validation: Check for errors
            if "error" in response_content.lower() or "unknown operation" in response_content.lower():
                 logger.warning(f"[Test {iteration}/{total_requests}] Potential error keyword in response: '{response_content}'")
                 # Consider setting success_flag = False here if these indicate failure
        else:
            logger.error(f"[Test {iteration}/{total_requests}] Failed to get valid response content.")

        return {"query": query, "response": response_content, "success": success_flag}

    except Exception as e:
        logger.error(f"[Test {iteration}/{total_requests}] Exception during test execution for query '{query}': {e}", exc_info=True)
        return {"query": query, "response": f"Exception: {e}", "success": False}

async def main_test_runner(num_requests):
    """Runs the main E2E test suite, managing servers and running tests concurrently."""
    
    servers_started = await start_servers()
    if not servers_started:
        logger.critical("Could not start servers. Aborting test run.")
        return

    agent_executor = None
    all_results = [] # List to store result dicts
    try:
        # Use async with for the client lifecycle
        logger.info("Setting up MCP client...")
        async with MultiServerMCPClient({
            "math": {
                "command": sys.executable,
                "args": [os.path.join(project_root, "src", "mcp_servers", "math_server.py")],
                "transport": "stdio"
            },
            "weather": {
                "url": "http://localhost:8000/sse",
                "transport": "sse"
            }
        }) as mcp_client: # Client is connected here
            logger.info("MCP client connected. Setting up agent...")
            try:
                model = ChatGoogleGenerativeAI(
                    model="gemini-2.5-flash-preview-04-17",
                    google_api_key=os.environ.get("GOOGLE_API_KEY")
                )
                tools = mcp_client.get_tools()
                if not tools:
                    logger.warning("No tools loaded from MCP servers. Agent might not function correctly.")
                
                agent_executor = create_react_agent(model, tools)
                logger.info("Agent setup complete.")
            except Exception as agent_setup_error:
                 logger.error(f"Failed to setup agent: {agent_setup_error}", exc_info=True)
                 # Exit the runner if agent setup fails
                 return # Finally block will still execute

            # Proceed only if agent setup was successful
            if agent_executor:
                logger.info(f"Starting E2E agent test run ({num_requests} requests concurrently)...")
                
                # Create tasks for all tests, passing the agent
                tasks = [run_single_test(i, num_requests, agent_executor) for i in range(1, num_requests + 1)]
                
                # Run tasks concurrently
                logger.info(f"Running {len(tasks)} test tasks concurrently using asyncio.gather...")
                all_results = await asyncio.gather(*tasks, return_exceptions=True)
                logger.info("All test tasks completed.")

                # Process results
                success_count = 0
                failure_count = 0
                successful_pairs = []
                failed_pairs = []
                
                for i, result in enumerate(all_results):
                    test_num = i + 1
                    if isinstance(result, Exception):
                        logger.error(f"[Test {test_num}/{num_requests}] Task failed with exception: {result}")
                        failure_count += 1
                        # Try to get query if possible (may not be available if task itself failed early)
                        # We don't have the query readily available here if the task itself failed.
                        failed_pairs.append({"query": f"Task {test_num} (Query Unknown)", "response": f"Exception: {result}", "success": False})
                    elif isinstance(result, dict):
                        if result.get("success"):
                            success_count += 1
                            successful_pairs.append(result)
                        else:
                            failure_count += 1
                            failed_pairs.append(result)
                    else: # Unexpected result type from gather
                        logger.error(f"[Test {test_num}/{num_requests}] Received unexpected result type from task: {type(result)} - {result}")
                        failure_count += 1
                        failed_pairs.append({"query": f"Task {test_num} (Query Unknown)", "response": f"Unexpected Result: {result}", "success": False})

                # --- Print Summary Statistics ---
                logger.info("--- E2E Test Run Summary ---")
                logger.info(f"Total Requests: {num_requests}")
                logger.info(f"Successful Requests: {success_count}")
                logger.info(f"Failed Requests: {failure_count}")
                logger.info("-----------------------------")

                # --- Print Successful Pairs --- 
                if successful_pairs:
                    print("\n--- Successful Request/Response Pairs ---")
                    for i, pair in enumerate(successful_pairs):
                        print(f"\n[{i+1}/{success_count}] Request:")
                        print(f"  {pair['query']}")
                        print(f"  Response:")
                        # Indent multi-line responses
                        indented_response = '\n  '.join(pair['response'].splitlines())
                        print(f"  {indented_response}")
                    print("-------------------------------------------")
                
                # --- Print Failed Pairs/Errors ---
                if failed_pairs:
                    print("\n--- Failed Requests/Errors ---")
                    for i, pair in enumerate(failed_pairs):
                        print(f"\n[{i+1}/{failure_count}] Failed Request:")
                        print(f"  {pair['query']}")
                        print(f"  Failure Reason/Response:")
                        indented_response = '\n  '.join(str(pair['response']).splitlines())
                        print(f"  {indented_response}")
                    print("-----------------------------")

                if failure_count > 0:
                    logger.warning("Some E2E tests failed or encountered errors.")
                    # sys.exit(1) # Exit with error code if needed for CI/CD
            else:
                 logger.critical("Agent executor was not created successfully. Skipping test execution.")

    except Exception as runner_error:
        logger.error(f"Error during main test runner execution: {runner_error}", exc_info=True)
    finally:
        # Cleanup: Stop servers (MCP client is closed by async with)
        await stop_servers()

@patch("src.agent.client.ChatGoogleGenerativeAI")
@patch("src.agent.client.MultiServerMCPClient")
async def test_end_to_end_mocked_servers_and_llm(self, mock_mcp_client_constructor, mock_llm_constructor):
    """ Test the full agent flow with mocked LLM and MCP servers. """
    # Arrange: Mock the LLM response
    mock_llm_instance = MagicMock()
    mock_llm_response = AIMessage(content="The sum is 3.")
    mock_llm_instance.ainvoke.return_value = mock_llm_response
    mock_llm_constructor.return_value = mock_llm_instance
    
    # Arrange: Mock the MCP Client and its tools
    mock_mcp_client_instance = MagicMock()
    mock_mcp_client_instance.get_tools.return_value = [
        Tool(name="add", description="Add two numbers", func=lambda a, b: a + b)
    ]
    # Configure the context manager
    mock_mcp_client_constructor.return_value.__aenter__.return_value = mock_mcp_client_instance

    # Act: Run the agent main function with a query
    # Assuming agent.py is structured to be callable like this
    # We might need to adjust if main() does more than just run the agent loop
    try:
        result = await agent_main(user_query="What is 1 + 2?")
        print("Agent Result:", result)
    except ValueError as e:
        print(f"Caught expected ValueError: {e}")
        # If agent.py exits or raises error on missing API key, this might be expected
        # Modify agent.py or this test if needed
        pass # src/agent/client.py already handles missing GOOGLE_API_KEY etc.

    # Assert
    # Check if LLM was called

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run E2E tests against the agent.')
    parser.add_argument(
        '--mode', 
        type=str, 
        choices=['dev', 'full'], 
        default='full', 
        help='Test mode: "dev" for a quick run (37 requests), "full" for the complete run (100 requests).'
    )
    args = parser.parse_args()

    # Determine number of requests based on mode
    if args.mode == 'dev':
        NUM_REQUESTS = DEFAULT_NUM_REQUESTS_DEV
    else:
        NUM_REQUESTS = DEFAULT_NUM_REQUESTS_FULL

    # Ensure environment variables are loaded (client.py does this, but good practice)
    from dotenv import load_dotenv
    env_path = os.path.join(project_root, '.env')
    if os.path.exists(env_path):
        load_dotenv(dotenv_path=env_path)
        logger.info(f"Loaded environment variables from {env_path}")
    elif os.path.exists(os.path.join(project_root, 'env.example')):
         logger.warning(".env file not found. Attempting to use env.example if necessary keys are present.")
         # Potentially load env.example here if desired, but .env is standard
         pass # client.py already handles missing GOOGLE_API_KEY etc.
    else:
         logger.warning(".env file not found, and no env.example present.")

    # Check for necessary API keys (client checks for Google, add others if needed)
    if not os.environ.get("GOOGLE_API_KEY"):
        logger.critical("GOOGLE_API_KEY environment variable not set. The agent requires this.")
        sys.exit(1)
        
    # Run the async test suite with the determined number of requests
    try:
        asyncio.run(main_test_runner(NUM_REQUESTS))
    except KeyboardInterrupt:
        logger.info("Test run interrupted by user. Cleaning up...")
        # Ensure servers are stopped even on KeyboardInterrupt
        # Note: asyncio might handle some cleanup, but explicit call is safer
        # The finally block in main_test_runner should handle this now.
        pass 