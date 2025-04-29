# LangGraph Agent with MCP Tools

A minimalist, robust agent using LangGraph and MCP for a conversational agent that can perform calculations and retrieve weather information, with Gemini 2.5 Flash as the LLM.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file with your API keys:
   ```
   GOOGLE_API_KEY=your_google_api_key
   ```

## Running the Agent

Start the agent with:
```bash
python run.py
```

This will:
1. Start the MCP servers (math and weather)
2. Initialize the LangGraph agent
3. Provide an interactive prompt

Type `exit` to quit.

## Lambda Implementation

The project now includes an AWS Lambda implementation of the MCP services:

- Math and Weather services as Lambda functions
- API Gateway for accessing the Lambda functions
- No authentication required (as per requirements)

### Running Lambda Implementation Locally

Run the local Lambda environment with:
```bash
python run_lambda_local.py
```

This will start the SAM local API on port 3000 and test the endpoints.

In another terminal, run the Lambda-compatible client:
```bash
python lambda_client.py
```

See `lambda/README.md` for more details.

## Testing

Run automated tests with:
```bash
python test_queries.py
```

## Project Structure

- `math_server.py` - MCP server for math operations
- `weather_server.py` - MCP server for weather information
- `client.py` - LangGraph agent implementation
- `run.py` - Script to start everything together
- `test_queries.py` - Test script with example queries

## Architecture

The agent uses:
- LangGraph for the agent workflow
- Gemini 2.5 Flash as the LLM
- MCP for tool integration
- MultiServerMCPClient to connect to multiple MCP servers 