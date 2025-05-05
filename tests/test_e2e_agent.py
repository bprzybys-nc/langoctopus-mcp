import asyncio
import random
import sys
import os
import logging
import argparse
import signal # Added signal
import time # Added time
from unittest.mock import patch, MagicMock
from langchain_mcp_adapters.client import MultiServerMCPClient
from src.agent.manager import AgentManager # <<< Import AgentManager
from typing import List

# Add project root to path to allow importing 'client'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    # We need ChatGoogleGenerativeAI and create_react_agent directly now
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langgraph.prebuilt import create_react_agent
except ImportError as e:
    logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    logger.critical(f"Error importing dependencies: {e}")
    logger.critical("Ensure langchain_google_genai, langgraph, langchain_mcp_adapters are installed.")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ANSI escape codes for colors
YELLOW = "\033[93m"
RESET = "\033[0m"

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
        await asyncio.sleep(7)  # Increase wait time to 7 seconds
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
            pid = process.pid # Store pid in case process object becomes invalid
            logger.info(f"Attempting graceful termination (SIGTERM) for server (PID: {pid})...")
            try:
                process.terminate()
                # Wait up to 5 seconds for graceful termination
                await asyncio.wait_for(process.wait(), timeout=5)
                logger.info(f"Server (PID: {pid}) terminated gracefully.")
            except asyncio.TimeoutError:
                logger.warning(f"Graceful termination timed out for server (PID: {pid}). Attempting forceful kill (SIGKILL)...")
                try:
                    process.kill()
                    # Wait up to 2 seconds for kill confirmation
                    await asyncio.wait_for(process.wait(), timeout=2)
                    logger.info(f"Server (PID: {pid}) killed successfully.")
                except asyncio.TimeoutError:
                    logger.critical(f"Forceful kill (SIGKILL) failed to confirm termination for server (PID: {pid}) within timeout. Process might be defunct.")
                    # Continue cleanup despite this failure
                except ProcessLookupError:
                     logger.warning("Server (PID: {pid}) disappeared before kill could be confirmed (already terminated?).")
                except Exception as kill_exc:
                    logger.error(f"Error during forceful kill for server (PID: {pid}): {kill_exc}")
            except ProcessLookupError:
                 logger.warning("Server (PID: {pid}) already terminated before graceful attempt.")
            except Exception as term_exc:
                logger.error(f"Error during graceful termination for server (PID: {pid}): {term_exc}")
        else:
            logger.info(f"Server (PID: {process.pid}) already finished with code {process.returncode}.")
    server_processes = [] # Clear the list
    logger.info("Servers shut down process completed.") # Changed log slightly

# --- Agent Setup (No longer a separate async def, integrated into runner) ---
# Removed setup_agent function as it's now integrated below

# --- Test Query Generation (Helper Function) ---
def generate_random_query(iteration, total_requests):
    """Generates a random query dict {query: str, expected_hints: list}."""
    
    # Determine service choice based on total requests
    services = ["math", "weather"]
    weights = [0.5, 0.5] # Default weights for dev mode (or fewer requests)
    if total_requests >= 100: # For full mode, introduce combined queries
        services.append("combined")
        # Aim for ~1/3 combined, split rest between math/weather
        weights = [0.33, 0.33, 0.34]
    elif total_requests > 10: # For intermediate, add a smaller chance of combined
        services.append("combined")
        weights = [0.45, 0.45, 0.10]
        
    service = random.choices(services, weights=weights, k=1)[0]
    query = ""
    expected_hints = []

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
            
    elif service == "combined":
        # Generate a query requiring both weather (temperature) and math
        location = random.choice(LOCATIONS)
        num_to_add = random.randint(-20, 20) # Add/subtract a number from temp
        op_phrase = "plus" if num_to_add >= 0 else "minus"
        abs_num = abs(num_to_add)
        
        query = f"What is the current temperature in {location} {op_phrase} {abs_num} degrees?"
        number_hints = [str(num) for num in range(10)]
        expected_hints = [location] + number_hints # Combine location with number hints

    return {"query": query, "expected_hints": expected_hints} # Return dict

# --- Single Test Execution Logic ---
async def run_single_test_standard(iteration, total_requests, agent_manager, query_data):
    """Runs a single test query in Standard mode."""
    query = query_data["query"]
    logger.info(f"[Test {iteration}/{total_requests} Standard] Sending query: '{query}'")
    try:
        response_content = await agent_manager.process_request(query)
        success = "Error:" not in response_content if response_content else False
        
        if success:
            logger.info(f"[Test {iteration}/{total_requests} Standard] Received response: '{response_content}'")
        else:
            logger.error(f"[Test {iteration}/{total_requests} Standard] Failed or error in response: '{response_content}'")
            
        return {"query": query, "response": response_content or "No response", "success": success}
    except Exception as e:
        logger.error(f"[Test {iteration}/{total_requests} Standard] Exception during test execution for query '{query}': {e}", exc_info=True)
        return {"query": query, "response": f"Exception: {e}", "success": False}

# --- Main Test Runner ---
async def main_test_runner(num_requests, run_modes: List[str]):
    """Runs the main E2E test suite for both Standard and Batch modes."""
    
    servers_started = await start_servers()
    if not servers_started:
        logger.critical("Could not start servers. Aborting test run.")
        return False # Indicate failure

    all_results = {} # Store results keyed by mode
    success = True # Overall success flag

    # --- Setup Client and Agent ---
    # Use an async context manager for the client
    logger.info("Setting up MCP client...")
    try: # <<< Outer try block for client/agent setup and run
        async with MultiServerMCPClient(
            { # <<< Pass the configuration dictionary directly
                "math": { # Logical name used by agent/tools
                     # Define how to connect to the math server (e.g., stdio or URL if changed)
                     # Assuming stdio based on server script:
                     "command": sys.executable,
                     "args": [os.path.join(project_root, "src", "mcp_servers", "math_server.py")],
                     "transport": "stdio"
                 },
                 "weather": { # Logical name used by agent/tools
                     # Define how to connect to the weather server (sse)
                     "url": "http://localhost:8000/sse", # SSE endpoint URL
                     "transport": "sse"
                 }
            },
            # Add any other necessary client config here
        ) as mcp_client:
            # Wait for client connection if needed (might be handled internally)
            # await asyncio.sleep(1) # Adjust if necessary

            logger.info("MCP client connected. Setting up agent executor...")
            try:
                model = ChatGoogleGenerativeAI(
                    model="gemini-2.5-flash-preview-04-17",
                    google_api_key=os.environ.get("GOOGLE_API_KEY")
                )
                tools = mcp_client.get_tools()
                if not tools:
                     logger.error("Failed to retrieve tools from MCP servers.")
                     await stop_servers()
                     return False
                logger.info(f"Retrieved tools: {[tool.name for tool in tools]}")

                agent_executor = create_react_agent(model, tools)
                logger.info("Agent executor setup complete.")

            except Exception as agent_setup_exc:
                 logger.error(f"Failed to setup agent executor: {agent_setup_exc}", exc_info=True)
                 await stop_servers()
                 return False
            
            # --- Generate Test Queries ---
            logger.info(f"Generating {num_requests} test queries...")
            test_queries = [generate_random_query(i, num_requests) for i in range(1, num_requests + 1)]
            logger.info("Test queries generated.")

            # --- Run tests for each selected mode ---
            for mode in run_modes:
                logger.info(f"===== Starting Test Run: {mode} Mode =====")
                agent_manager = AgentManager(agent_executor, mode=mode, batch_size=10, request_timeout=120) # Pass configured agent
                mode_results = []
                start_time = time.time()

                if mode == "Standard":
                    logger.info(f"Running {num_requests} requests sequentially (Standard Mode)...")
                    tasks = []
                    for i, query_data in enumerate(test_queries):
                        # Use the helper function for better structure
                        task = asyncio.create_task(
                            run_single_test_standard(i + 1, num_requests, agent_manager, query_data)
                        )
                        tasks.append(task)
                    
                    # Gather results from all standard tasks
                    standard_results_raw = await asyncio.gather(*tasks)
                    # Filter out None results (e.g., if run_single_test_standard returns None on failure)
                    mode_results = [res for res in standard_results_raw if res] 

                elif mode == "Batch":
                     logger.info(f"Queueing {num_requests} requests (Batch Mode)...")
                     for i, query_data in enumerate(test_queries):
                          ack = await agent_manager.process_request(query_data["query"])
                          # Optionally log acknowledgement: logger.debug(f"[Test {i+1}/{num_requests} Batch] {ack}")
                     
                     logger.info(f"Flushing queue (Batch Size: {agent_manager.batch_size})...")
                     batch_start_time = time.time()
                     batch_results_raw = await agent_manager.flush()
                     batch_duration = time.time() - batch_start_time
                     logger.info(f"Batch flush completed in {batch_duration:.2f} seconds.")

                     if batch_results_raw:
                         for res in batch_results_raw:
                             res_content = res.get("response", "")
                             res["success"] = "Error:" not in res_content if res_content else False
                             if not res["success"]:
                                 logger.error(f"[Batch Result] Failed or error in response for query '{res.get('query', 'Unknown')}': '{res_content}'")
                             else:
                                 logger.info(f"[Batch Result] Response for query '{res.get('query', 'Unknown')}': '{res_content}'")
                         mode_results = batch_results_raw
                     else:
                         logger.error("Batch mode flush returned no results or failed.")
                         mode_results = [{"query": q_data["query"], "response": "Batch Flush Failed", "success": False} for q_data in test_queries]

                end_time = time.time()
                duration = end_time - start_time
                logger.info(f"{YELLOW}===== Test Run Complete: {mode} Mode ({duration:.2f} seconds) ====={RESET}")
                
                # --- Process and Log Results for the Mode ---
                failures = [r for r in mode_results if not r.get("success")]
                num_failures = len(failures)
                all_results[mode] = {"results": mode_results, "failures": num_failures}
                
                logger.info(f"--- {mode} Mode Summary ---")
                logger.info(f"Total Requests: {len(mode_results)}")
                logger.info(f"Successful: {len(mode_results) - num_failures}")
                logger.info(f"Failures: {num_failures}")
                if num_failures > 0:
                    success = False # Mark overall run as failed if any mode fails
                    logger.error(f"{mode} mode encountered failures:")
                    for f in failures[:5]: # Log first 5 failures
                        logger.error(f"  - Query: {f.get('query', 'N/A')}, Response: {f.get('response', 'N/A')}")
                logger.info("-" * (len(mode) + 17)) # End summary separator

    except Exception as e:
        logger.error(f"An unexpected error occurred during the test run: {e}", exc_info=True)
        success = False
    finally:
        logger.info("Exiting MultiServerMCPClient context manager block.")
        await stop_servers()
        logger.info("Test run finished.")

    # --- Final Summary ---
    logger.info("======== E2E Test Final Summary ========")
    for mode, summary in all_results.items():
        total = len(summary.get("results", []))
        fails = summary.get("failures", total) # Assume all failed if no results
        logger.info(f"[{mode} Mode]: {total - fails}/{total} successful ({fails} failures)")
    logger.info("========================================")
    
    return success # Return overall success status

# --- Main Execution Block ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run E2E tests for the LangGraph MCP Agent.')
    parser.add_argument(
        '--mode', 
        type=str, 
        choices=['dev', 'full'], 
        default='full', 
        help='Test mode: "dev" for quick run (37 reqs), "full" for complete (100 reqs).'
    )
    # Execution mode flags (mutually exclusive group might be better, but flags are simpler)
    parser.add_argument(
        '--SOLO', 
        action='store_true', 
        help='Run only Standard (sequential/async) mode.'
    )
    parser.add_argument(
        '--BATCH', 
        action='store_true', 
        help='Run only Batch mode.'
    )
    # Implicitly run BOTH if neither --SOLO nor --BATCH is specified.

    args = parser.parse_args()

    # Determine number of requests based on mode
    if args.mode == 'dev':
        NUM_REQUESTS = DEFAULT_NUM_REQUESTS_DEV
    else: # args.mode == 'full'
        NUM_REQUESTS = DEFAULT_NUM_REQUESTS_FULL
        
    # Determine which execution modes to run
    run_modes = []
    if args.SOLO:
        run_modes.append("Standard")
    if args.BATCH:
        run_modes.append("Batch")
        
    # Default to BOTH if neither specific flag is set
    if not run_modes:
        run_modes = ["Standard", "Batch"]
        
    if args.SOLO and args.BATCH:
        logger.warning("Both --SOLO and --BATCH specified. Running both modes.")
        run_modes = ["Standard", "Batch"] # Ensure both run if both flags present

    logger.info(f"E2E Test Config: Mode={args.mode} ({NUM_REQUESTS} requests), Execution={run_modes}")

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
        
    # Handle Ctrl+C gracefully
    loop = asyncio.get_event_loop()
    stop_event = asyncio.Event()

    def signal_handler():
        logger.warning("Ctrl+C detected. Initiating shutdown...")
        stop_event.set()
        # Give tasks a chance to stop gracefully before force-stopping servers
        # asyncio.create_task(stop_servers()) # <<< REMOVE direct call from handler

    # Add signal handlers for SIGINT (Ctrl+C) and SIGTERM
    try:
        loop.add_signal_handler(signal.SIGINT, signal_handler)
        loop.add_signal_handler(signal.SIGTERM, signal_handler)
    except NotImplementedError:
         # Windows doesn't support add_signal_handler
         logger.warning("Signal handlers not fully supported on this platform (e.g., Windows). Manual interruption might be needed.")

    # --- Run the main test runner ---
    exit_code = 1 # Default to error unless explicitly set to 0
    try:
        overall_success = loop.run_until_complete(main_test_runner(NUM_REQUESTS, run_modes))
        exit_code = 0 if overall_success else 1
    except KeyboardInterrupt:
         logger.info("Test run interrupted by user. Cleaning up...")
         exit_code = 1 # <<< SET exit_code on interrupt
         pass 
    except Exception as e:
         logger.critical(f"Main test runner failed with an unhandled exception: {e}", exc_info=True)
         exit_code = 1
    finally:
        # Clean up signal handlers
        try:
             loop.remove_signal_handler(signal.SIGINT)
             loop.remove_signal_handler(signal.SIGTERM)
        except NotImplementedError:
             pass # Ignore if not supported
        # Ensure servers are stopped (This runs regardless of how the try block exited)
        logger.info("Main block finally: Ensuring server cleanup...")
        loop.run_until_complete(stop_servers()) 
        logger.info("Cleanup complete.")
        sys.exit(exit_code) # <<< Ensure this is uncommented

# --- Mocked Tests (Keep existing mocks if needed) ---
# Note: These might need adaptation if they rely on the old structure
# Example of adapting a mock test (conceptual)
class MockTests(unittest.TestCase):

    @patch("src.agent.manager.AgentManager.process_request", new_callable=AsyncMock) # Patch the manager now
    @patch("tests.test_e2e_agent.start_servers", new_callable=AsyncMock)
    @patch("tests.test_e2e_agent.stop_servers", new_callable=AsyncMock)
    @patch("langchain_mcp_adapters.client.MultiServerMCPClient") 
    @patch("langchain_google_genai.ChatGoogleGenerativeAI") 
    @patch("langgraph.prebuilt.create_react_agent")
    async def test_e2e_standard_mocked(self, mock_create_agent, mock_llm_constructor, mock_mcp_client_constructor, mock_stop_servers, mock_start_servers, mock_process_request):
        # Arrange Mocks
        mock_start_servers.return_value = True
        mock_agent_executor = AsyncMock()
        mock_create_agent.return_value = mock_agent_executor
        
        # Mock the MCP client context manager and get_tools
        mock_mcp_instance = AsyncMock()
        mock_mcp_instance.get_tools.return_value = [MagicMock()] # Return some dummy tools
        mock_mcp_client_constructor.return_value.__aenter__.return_value = mock_mcp_instance
        
        # Define the mock response from the manager's process_request
        mock_process_request.return_value = "Mocked Standard Response"

        # Act
        # Run ONLY the Standard mode part of the runner for this test
        # This requires either adapting main_test_runner or calling a specific part
        # For simplicity, let's assume we can test the flow conceptually
        
        # Concept: Instantiate manager, call process_request
        num_req = 5
        test_queries = [generate_random_query(i, num_req) for i in range(1, num_req + 1)]
        
        # Simulate running standard mode part:
        manager = AgentManager(mock_agent_executor, mode='Standard')
        results = []
        for i, q_data in enumerate(test_queries):
             response = await manager.process_request(q_data['query']) # Use the actual manager method which is mocked
             results.append({'query': q_data['query'], 'response': response, 'success': 'Error:' not in response})

        # Assert
        self.assertEqual(mock_process_request.call_count, num_req)
        self.assertEqual(len(results), num_req)
        self.assertTrue(all(r['success'] for r in results))
        mock_start_servers.assert_called_once() # Assert servers are started/stopped appropriately if testing main_test_runner
        # mock_stop_servers.assert_called_once() 

# Example for running async tests with unittest
# if __name__ == '__main__':
#      unittest.main() # Or use asyncio.run(unittest.main()) if needed for async test discovery 

# Corrected exit call outside the finally block of the main try/except/finally -> REMOVED this block
# if 'exit_code' in locals() or 'exit_code' in globals(): # Check if exit_code was set
#    sys.exit(exit_code)
# else:
#    # Fallback if something went very wrong before exit_code was initialized
#    logger.critical("exit_code was not defined before attempting to exit.")
#    sys.exit(1) 