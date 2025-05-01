# Frontend Implementation Plan

## Overview
Create a retro-style UI for the existing agent with a chat interface featuring robot avatars on the left and right sides, with a text display in the middle showing the conversation history.

## Architecture
- Frontend: React.js application with retro-style CSS
- Backend: Flask server that integrates with the existing agent
- Communication: WebSockets for real-time updates

## Directory Structure
```
frontend/
├── public/
│   ├── index.html
│   ├── favicon.ico
│   └── assets/
│       ├── robot-left.svg
│       └── robot-right.svg
├── src/
│   ├── components/
│   │   ├── App.jsx
│   │   ├── ChatHistory.jsx
│   │   ├── LeftRobot.jsx
│   │   └── RightRobot.jsx
│   ├── styles/
│   │   ├── retro.css
│   │   └── animations.css
│   ├── services/
│   │   └── api.js
│   └── index.js
├── package.json
└── README.md
```

## Backend Structure
```
backend/
├── app.py
├── agent_connector.py
└── sample_data.py
```

## Color Palette (Retro-Style)
- Primary: #FF6B6B (Retro Red)
- Secondary: #4ECDC4 (Teal)
- Background: #1A1A2E (Deep Blue)
- Text: #F7FFF7 (Off-White)
- Accent: #FFE66D (Pale Yellow)

## Implementation Steps

### 1. Setup Frontend
- Create React application
- Install dependencies (react, socket.io-client, styled-components)
- Set up the main layout with three panes
- Create SVG robot avatars with retro styling
- Implement retro styling using CSS

### 2. Setup Backend
- Create Flask server app
- Integrate with existing agent code
- Set up WebSocket connection with Socket.IO
- Create endpoints for handling queries
- Implement sample data fallback for testing

### 3. Robot Avatars
- Design retro-style robot avatars for left and right sides
- Add simple animations for "talking" and "thinking" states
- Position avatars at the bottom of the side panes

### 4. Chat History Display
- Implement chat history component with reverse chronological order
- Style chat bubbles with retro design
- Add typing animation effects

### 5. Integration
- Connect frontend to backend via WebSocket
- Implement sequential conversation flow
  - Left robot asks a question
  - Right robot processes and answers
  - After right robot finishes, left robot asks next question
- Add loading/thinking animations

### 6. Testing & Refinement
- Test with sample data from test_queries.py
- Verify responsiveness and styling
- Add error handling and fallbacks

## Service Location
The frontend service will be located at:
- **Development**: http://localhost:3000
- **Backend API**: http://localhost:5000

## API Endpoints
- `GET /api/sample_questions` - Get list of sample questions
- `POST /api/ask` - Send a question to the agent
- WebSocket events:
  - `message` - New message from either robot
  - `typing` - Robot is typing indication
  - `ready` - Ready for next question

## Test Data
Use the test queries from `tests/test_queries.py` for initial testing:
```python
test_queries = [
    "What is 5 + 7?",
    "What is 8 * 9?",
    "What's the weather in London?",
    "What's the 2-day forecast for Tokyo?",
    "Multiply 12 by 6 and tell me the weather in Paris.",
    "Calculate the derivative of x²"
]
``` 