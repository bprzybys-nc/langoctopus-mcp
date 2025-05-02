# LangOctopus MCP Project

A retro-style chat interface for interacting with the LangGraph MCP agent.

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

## Running the Application

### Prerequisites

- Python 3.8+
- Node.js 14+
- npm or yarn

### Setup

1. Clone the repository:
   ```
   git clone [repository_url]
   cd langoctopus-mcp
   ```

2. Set up the Python environment:
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Install frontend dependencies:
   ```
   cd frontend
   npm install
   cd ..
   ```

### Running the UI

To start both the frontend and backend servers:

```
./run_ui.sh
```

This script:
- Checks if required ports (3001, 5001) are available
- Installs dependencies if needed
- Starts the backend Flask server on port 5001
- Starts the frontend React server on port 3001

### Accessing the Application

- Frontend UI: http://localhost:3001
- Backend API: http://localhost:5001
- API documentation: http://localhost:5001/api/docs (if available)

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