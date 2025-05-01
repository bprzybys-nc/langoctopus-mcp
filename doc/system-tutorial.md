# System Architecture and Agent Tutorial

This document explains the architecture of the LangOctopus MCP example and how the agent uses the different components.

## System Diagram (Mermaid UML Class Diagram)

```mermaid
%% Regenerated based on mermaid.mdc rules
classDiagram
    direction TD

    class TestE2EAgent {
        <<Script: tests/test_e2e_agent.py>>
        +main_test_runner()
        +start_servers()
        +stop_servers()
        +run_single_test()
    }

    class ReActAgentExecutor {
        <<Agent Executor (LangGraph)>>
        +ainvoke(input: dict) AIMessage
    }

    class ChatGoogleGenerativeAI {
        <<LLM (Langchain)>>
        +ainvoke(prompt: BasePromptTemplate) BaseMessage
    }

    class MultiServerMCPClient {
        <<MCP Client (Adapter)>>
        +get_tools() List~Tool~
    }

    class MCPTool {
      <<Tool Representation>>
      +name: string
      +description: string
      +args_schema: PydanticModel
      +invoke(args: dict): any
    }

    class MathServer {
        <<MCP Server: math_server.py (stdio)>>
        +add(a: int, b: int) int
        +subtract(a: int, b: int) int
        +multiply(a: int, b: int) int
        +divide(a: int, b: int) float
    }

    class WeatherServer {
        <<MCP Server: weather_server.py (SSE)>>
        +get_weather(location: string) string
        +get_forecast(location: string, days: int) string
    }

    TestE2EAgent --> MultiServerMCPClient : creates & uses
    TestE2EAgent --> ChatGoogleGenerativeAI : creates
    TestE2EAgent --> ReActAgentExecutor : creates & invokes
    TestE2EAgent ..> MathServer : starts/stops process
    TestE2EAgent ..> WeatherServer : starts/stops process

    ReActAgentExecutor --> ChatGoogleGenerativeAI : uses for reasoning
    ReActAgentExecutor --> MCPTool : executes selected tool

    MultiServerMCPClient ..> MathServer : manages connection (stdio)
    MultiServerMCPClient ..> WeatherServer : manages connection (SSE)
    MultiServerMCPClient --> MCPTool : discovers & wraps tools

    MCPTool ..> MathServer : represents math functions
    MCPTool ..> WeatherServer : represents weather functions
```

## Sequence Diagram (Example Queries)

This diagram shows the typical flow of interactions when the agent processes different types of queries.

```mermaid
%% Regenerated based on mermaid.mdc rules
sequenceDiagram
    participant TestE2E as TestE2EAgent
    participant Agent as ReActAgentExecutor
    participant LLM as ChatGoogleGenerativeAI
    participant MCPClient as MultiServerMCPClient
    participant MathSrv as MathServer
    participant WeatherSrv as WeatherServer

    %% --- Math Query Example --- 
    TestE2E->>Agent: ainvoke({"messages": [<br>{"role": "user", "content": "What is 15 + 7?"}]})
    activate Agent
    Agent->>LLM: invoke(prompt_with_query_and_tools)
    activate LLM
    LLM-->>Agent: Plan: Use math.add<br>(a=15, b=7)
    deactivate LLM
    Agent->>MCPClient: Execute Tool:<br>math.add(a=15, b=7)
    activate MCPClient
    Note over MCPClient, MathSrv: Client uses stdio transport
    MCPClient->>MathSrv: add(a=15, b=7)
    activate MathSrv
    MathSrv-->>MCPClient: result: 22
    deactivate MathSrv
    MCPClient-->>Agent: tool_result: 22
    deactivate MCPClient
    Agent->>LLM: invoke(prompt_with_observation)
    activate LLM
    LLM-->>Agent: Final Answer:<br>"15 + 7 is 22."
    deactivate LLM
    Agent-->>TestE2E: AIMessage(content=<br>"15 + 7 is 22.")
    deactivate Agent

    %% --- Weather Query Example --- 
    TestE2E->>Agent: ainvoke({"messages": [<br>{"role": "user", "content": "Weather in London?"}]})
    activate Agent
    Agent->>LLM: invoke(prompt_with_query_and_tools)
    activate LLM
    LLM-->>Agent: Plan: Use weather.get_weather<br>(location="London")
    deactivate LLM
    Agent->>MCPClient: Execute Tool:<br>weather.get_weather(location="London")
    activate MCPClient
    Note over MCPClient, WeatherSrv: Client uses SSE transport
    MCPClient->>WeatherSrv: get_weather(location="London")
    activate WeatherSrv
    WeatherSrv-->>MCPClient: result: "Sunny, 22C"
    deactivate WeatherSrv
    MCPClient-->>Agent: tool_result: "Sunny, 22C"
    deactivate MCPClient
    Agent->>LLM: invoke(prompt_with_observation)
    activate LLM
    LLM-->>Agent: Final Answer:<br>"The weather in London is Sunny, 22C."
    deactivate LLM
    Agent-->>TestE2E: AIMessage(content=<br>"The weather in London is Sunny, 22C.")
    deactivate Agent

```

## Flowchart (E2E Test Script Logic)

This flowchart outlines the overall execution flow of the `tests/test_e2e_agent.py` script.

```mermaid
%% Regenerated based on mermaid.mdc rules and escaping node text
flowchart TD
    A["Start Script"] --> B{"Parse Args"};
    B -- "dev" --> C["NUM_REQUESTS = 37"];
    B -- "full or default" --> D["NUM_REQUESTS = 100"];
    C --> E["Load .env"];
    D --> E;
    E --> F["Run main_test_runner"];
    subgraph main_test_runner
      direction TB
      G["Call start_servers()"] --> H{"Servers OK"};
      H -- No --> I["Log Error & Exit Subgraph"];
      H -- Yes --> J["async with MCPClient"];
        subgraph async with MCPClient
            direction TB
            K["Client Connected"] --> L["Create LLM"];
            L --> M["Get Tools from Client"];
            M --> N["Create Agent (LLM + Tools)"];
            N --> O["Create N Tasks"];
            O --> P["asyncio.gather(Tasks)"];
            P --> Q["Process Results"];
        end
      Q --> R["Call stop_servers()"];
    end
    F --> S["Print Summary"];
    S --> T["Print Successes"];
    T --> U["Print Failures"];
    U --> V["End Script"];
    I --> V;
```

## How the Agent Selects and Calls MCP Tools

The core of the agent logic resides in the `ReActAgentExecutor`, created using LangGraph's `create_react_agent` function. This agent uses the ReAct (Reasoning and Acting) framework to interact with tools and achieve goals based on user input. Here's the process:

1.  **Initialization:** The `TestE2EAgent` script initializes the `MultiServerMCPClient`. This client connects to the running `MathServer` (via stdio) and `WeatherServer` (via SSE).
2.  **Tool Discovery:** The `MultiServerMCPClient` automatically discovers the functions exposed by each connected MCP server. It uses the `mcp` protocol to get the function names (e.g., `add`, `get_weather`), their docstrings (which become descriptions), and type hints (to generate argument schemas). It wraps these discovered functions into `MCPTool` objects (which are compatible with Langchain tools).
3.  **Agent Setup:** The `TestE2EAgent` script retrieves the list of `MCPTool` objects from the client using `mcp_client.get_tools()`. It then creates the `ReActAgentExecutor`, providing it with the `ChatGoogleGenerativeAI` model (Gemini) and the discovered list of `MCPTool`s.
4.  **Receiving a Query:** When the agent's `ainvoke` method is called with a user query (e.g., "What is 5 times 12?", "What's the weather in Paris?"), the ReAct loop begins.
5.  **Reasoning (Thought):** The `ReActAgentExecutor` sends the query and the descriptions of the available tools (`MCPTool` list) to the Gemini LLM. The LLM analyzes the query and the tool descriptions.
6.  **Tool Selection (Action Planning):** Based on the query's intent, the LLM decides which tool is most appropriate. For "What is 5 times 12?", it identifies the `math.multiply` tool. For "What's the weather in Paris?", it selects the `weather.get_weather` tool. The LLM also determines the arguments needed for the selected tool (e.g., `a=5, b=12` for multiply; `location="Paris"` for weather).
7.  **Execution (Action):** The `ReActAgentExecutor` executes the chosen `MCPTool` with the arguments determined by the LLM. The `MCPTool` wrapper handles calling the actual function on the correct remote MCP server (`MathServer` or `WeatherServer`) via the `MultiServerMCPClient` and the appropriate transport (stdio or SSE).
8.  **Observation:** The result from the MCP server is returned to the `ReActAgentExecutor`.
9.  **Final Answer Generation (Thought):** The agent sends the observation (the tool's result) back to the LLM. The LLM processes the result and formulates a final, user-friendly answer (e.g., "5 times 12 is 60.", "The weather in Paris is currently sunny.").
10. **Response:** The `ReActAgentExecutor` returns the final answer.

Essentially, the LLM acts as the central router, using the descriptions provided by the MCP tools to decide which specialized service (Math or Weather) to delegate the task to.

## MCP Servers (`math_server.py` and `weather_server.py`)

These Python scripts act as simple microservices exposing specific functionalities over the MCP protocol.

*   **`math_server.py`:**
    *   Imports the `mcp` library.
    *   Defines standard Python functions for arithmetic operations (`add`, `subtract`, `multiply`, `divide`).
    *   Includes type hints and docstrings for these functions. These are crucial as MCP uses them for tool discovery and schema generation.
    *   In its `if __name__ == "__main__":` block, it calls `mcp.run(transport="stdio")`. This starts the MCP server, making the defined functions available for remote calls over standard input/output. The `MultiServerMCPClient` is configured to launch this script as a subprocess and communicate with it via stdio.

*   **`weather_server.py`:**
    *   Imports the `mcp` library.
    *   Defines functions like `get_weather` and `get_forecast`. These currently return mock data but demonstrate the structure.
    *   Includes type hints and docstrings.
    *   In its `if __name__ == "__main__":` block, it calls `mcp.run(transport="sse")`. This starts the MCP server using Server-Sent Events (SSE) for communication, typically running as a standalone web server process (by default on port 8000, though the client connects via the specified URL `http://localhost:8000/sse`). The `MultiServerMCPClient` is configured to connect to this server's SSE endpoint URL.

The `mcp.run()` function handles the protocol details, listening for incoming requests, dispatching them to the correct Python function, and sending back the results according to the specified transport mechanism. 

## MCP Server Function Definitions

Below are the actual Python functions defined in the MCP servers, decorated with `@mcp.tool()`. This decorator, along with the function's docstring and type hints, provides the metadata that the `MultiServerMCPClient` uses during the **Tool Discovery** step mentioned above.

### `math_server.py`

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Math")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers"""
    return a * b

@mcp.tool()
def subtract(a: int, b: int) -> int:
    """Subtract b from a"""
    return a - b

@mcp.tool()
def divide(a: int, b: int) -> float:
    """Divide a by b"""
    if b == 0:
        # MCP automatically handles standard exceptions
        # converting them into protocol-level errors.
        raise ValueError("Cannot divide by zero")
    return a / b

# The if __name__ == "__main__": block starts the server
# with mcp.run(transport="stdio")
```

### `weather_server.py`

```python
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
    # ... (random forecast generation logic) ...
    import random
    weather_patterns = [
        "sunny with occasional clouds",
        "partly cloudy with light rain",
        "overcast with heavy rain",
    ]
    pattern = random.choice(weather_patterns)
    return f"{days}-day forecast for {location}: Expect mild temperatures around 20-25°C with {pattern}."

# The if __name__ == "__main__": block starts the server
# with mcp.run(transport="sse")
```

## Additional MCP Examples/Patterns

While this example uses basic request/response with primitive types, MCP supports more advanced patterns:

*   **Complex Data Types (Pydantic):** You can use Pydantic models for arguments and return types. MCP automatically generates JSON schemas for them.

    ```python
    from pydantic import BaseModel
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP("UserData")

    class User(BaseModel):
        user_id: int
        name: str
        is_active: bool

    class StatusResponse(BaseModel):
        message: str
        user_status: dict

    @mcp.tool()
    def update_user(user_data: User) -> StatusResponse:
        """Updates user information based on input model."""
        print(f"Updating user {user_data.user_id}: {user_data.name}")
        # ... database logic ...
        return StatusResponse(
            message=f"User {user_data.user_id} updated.", 
            user_status=user_data.dict()
        )
    ```

*   **Error Handling:** As shown in the `divide` function, raising standard Python exceptions within an `@mcp.tool()` function is the standard way to signal errors. MCP intercepts these and translates them into appropriate error responses in the protocol, which the client can then handle.

*   **Streaming Responses:** While not explicitly used here for complex logic, the SSE (Server-Sent Events) transport used by the `WeatherServer` is inherently a streaming protocol. For tools that generate results incrementally (like a long LLM response), you could `yield` results from your function instead of returning a single value. MCP over SSE would stream these yielded chunks to the client.

    ```python
    # Example (Conceptual - requires client-side handling of streamed chunks)
    @mcp.tool()
    def generate_report(topic: str) -> str: # Return type might vary for streaming
        """Generates a multi-part report, streaming sections."""
        yield "Section 1: Introduction to {topic}\n"
        # ... time consuming step 1 ...
        yield "Section 2: Analysis of {topic}\n"
        # ... time consuming step 2 ...
        yield "Section 3: Conclusion for {topic}\n"
    ```

*   **Different Transports:** This example uses `stdio` and `sse`. MCP also supports other transports like WebSockets (`ws`) which could be used depending on the specific client-server interaction needs. 