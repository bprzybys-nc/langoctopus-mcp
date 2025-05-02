# LangOctopus MCP Project

A retro-style chat interface for interacting with the LangGraph MCP agent.

## Project Structure

```
/
├── backend/              # Flask backend server for the UI
│   ├── app.py
│   └── ... (removed requirements.txt)
├── config/               # Configuration files (if any)
├── doc/                  # Project documentation files
├── frontend/             # React frontend application
│   ├── public/
│   ├── src/
│   ├── package.json
│   └── package-lock.json  # npm lock file
├── lambda/               # AWS SAM application for deploying MCP servers as Lambda
│   ├── math/
│   ├── weather/
│   ├── authorizer/
│   ├── client.py          # Lambda-specific agent entrypoint
│   ├── client_adapter.py  # Adapter for Lambda client
│   └── README.md
├── scripts/              # Utility scripts
│   └── run_ui.sh        # Runs frontend and backend
├── src/                  # Core agent source code
│   ├── agent/             # LangGraph agent implementation
│   │   └── client.py
│   ├── mcp_servers/       # MCP server implementations (local)
│   │   ├── math_server.py
│   │   └── weather_server.py
│   └── utils/
├── tests/                # Test files
│   └── run_tests.py       # Test runner
├── trash/                # Directory for deleted/obsolete files
├── .cursor/              # Cursor configuration and rules
├── .git/                 # Git directory
├── .gitignore
├── .env.example          # Example environment variables
├── pyproject.toml        # Python dependencies (Poetry)
├── poetry.lock           # Poetry lock file
├── README.md             # This file
├── run.py                # Main script to run the agent (local servers)
└── test_queries.py       # Example queries for the agent
```

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd langoctopus-mcp
    ```

2.  **Install Python Dependencies:**
    *   Ensure you have Python 3.10+ and Poetry installed.
    *   Install dependencies:
        ```bash
        poetry install
        ```

3.  **Install Frontend Dependencies:**
    *   Ensure you have Node.js and npm installed.
    *   Navigate to the frontend directory and install dependencies:
        ```bash
        cd frontend
        npm install
        cd ..
        ```

4.  **Environment Variables:**
    *   Copy `.env.example` to `.env`.
    *   Fill in your `GOOGLE_API_KEY` in the `.env` file.

## Running the Application

### Option 1: Local MCP Servers (Recommended for Development)

1.  **Run the Agent and Local Servers:**
    This script handles starting the local Math and Weather MCP servers and then runs the main agent (`src/agent/client.py`).
    ```bash
    poetry run python run.py
    ```
    The agent will be ready for input in the terminal.

2.  **Run the UI:**
    Open another terminal and run the UI script. This starts the Flask backend and serves the React frontend.
    ```bash
    ./scripts/run_ui.sh
    ```
    Access the UI at `http://localhost:5000` (or the specified port).

### Option 2: Agent with Deployed Lambda MCP Servers

Refer to the `lambda/README.md` for instructions on deploying the SAM application and running the agent (`lambda/client.py`) against the deployed functions.

## Running Tests

```bash
cd tests
poetry run python run_tests.py
cd ..
```

## Using the Agent

Once the agent is running (either via `run.py` or `lambda/client.py`), you can interact with it in the terminal where it was started. Type your queries and press Enter. Type `exit` to quit.

Example queries are available in `test_queries.py`.

## Project Overview

This project consists of:

1. **Backend**: A Flask server with Socket.IO integration that connects to the LangGraph MCP agent.
2. **Frontend**: A React application with a retro-style UI featuring robot avatars and a chat interface.
3. **Agent**: The existing LangGraph MCP agent that can answer math and weather questions.

## Directory Structure

- `/src` - Core agent functionality
  - `/agent` - LangGraph agent implementation
  - `/mcp_servers` - MCP server implementations (math, weather)
- `/frontend` - React-based retro-style UI
- `/backend` - Flask server with Socket.IO integration
- `/run.sh` - Script to run the agent servers
- `/run_ui.sh` - Script to run the frontend and backend servers

## Features

- Retro-style UI with custom robot avatars
- Real-time communication using Socket.IO
- Automated conversation flow (questions and answers)
- Integration with the existing agent for math and weather questions
- Responsive design with animations

## Development

### Backend

The backend is a Flask application with Socket.IO integration. It connects to the existing LangGraph MCP agent to process questions.

Key files:
- `backend/app.py` - Main Flask application with Socket.IO setup

### Frontend

The frontend is a React application with a retro-style UI.

Key components:
- `App.jsx` - Main application component
- `LeftRobot.jsx` - Left robot component (questioner)
- `RightRobot.jsx` - Right robot component (answerer)
- `ChatHistory.jsx` - Chat history display component

### Adding Custom Questions

You can modify the `test_queries.py` file to add your own questions to the sample set.

## Troubleshooting

- **Port conflicts**: The script will detect if ports 3001 or 5001 are already in use and will automatically kill the processes using them.
- **Missing dependencies**: The script will attempt to install missing dependencies automatically.

## License

[Your license information here] 