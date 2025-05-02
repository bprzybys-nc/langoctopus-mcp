import os
import sys
import asyncio
import argparse
import socket
from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import time
from threading import Thread

# Parse command line arguments
parser = argparse.ArgumentParser(description='Start the Flask backend server')
parser.add_argument('--port', type=int, default=5001, help='Port to run the server on')
args = parser.parse_args()

# Function to check if port is available
def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

# If port is in use, try to find an available port
port = args.port
if is_port_in_use(port):
    print(f"Warning: Port {port} is already in use.")
    # Try to find an available port in the range [port, port+100]
    for p in range(port, port+100):
        if not is_port_in_use(p):
            port = p
            print(f"Using alternative port: {port}")
            break
    else:
        print(f"Error: Could not find an available port in range {port}-{port+100}")
        sys.exit(1)

# Add project root to path to allow importing from src
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Set up Flask app with Socket.IO
app = Flask(__name__, static_folder='../frontend/build')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Sample test queries from tests/test_queries.py
test_queries = [
    "What is 5 + 7?",
    "What is 8 * 9?",
    "What's the weather in London?",
    "What's the 2-day forecast for Tokyo?",
    "Multiply 12 by 6 and tell me the weather in Paris.",
    "Calculate the derivative of x²"
]

# Sample responses for testing (when agent is not available)
sample_responses = {
    "What is 5 + 7?": "The sum of 5 and 7 is 12.",
    "What is 8 * 9?": "The product of 8 and 9 is 72.",
    "What's the weather in London?": "It's currently sunny and 25°C in London.",
    "What's the 2-day forecast for Tokyo?": "2-day forecast for Tokyo: Expect temperatures between 26-31°C with partly cloudy with light rain.",
    "Multiply 12 by 6 and tell me the weather in Paris.": "12 multiplied by 6 is 72. The weather in Paris is currently sunny and 28°C.",
    "Calculate the derivative of x²": "The derivative of x² is 2x."
}

# Agent connection status
agent_available = False

# Try to import the agent
try:
    from src.agent.client import main as agent_main
    agent_available = True
    print("Agent successfully imported!")
except ImportError as e:
    print(f"Could not import agent: {e}")
    print("Running in demo mode with sample responses.")

async def ask_agent(question):
    """Send a question to the agent and get a response."""
    if not agent_available:
        # Use sample responses in demo mode
        time.sleep(1)  # Simulate processing time
        return sample_responses.get(question, "I don't know the answer to that question.")
    
    try:
        return await agent_main(question)
    except Exception as e:
        print(f"Error calling agent: {e}")
        return f"Sorry, there was an error processing your request: {str(e)}"

def process_question_thread(question):
    """Process a question in a separate thread."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Emit typing indicator
    socketio.emit('typing', {'robot': 'right'})
    
    # Get response from agent
    response = loop.run_until_complete(ask_agent(question))
    
    # Emit response with a slight delay
    time.sleep(0.5)
    socketio.emit('message', {'robot': 'right', 'text': response})
    
    # Signal that the right robot is ready for the next question
    time.sleep(1)
    socketio.emit('ready')
    
    loop.close()

@app.route('/')
def serve_frontend():
    """Serve the React frontend."""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files from the React build."""
    return send_from_directory(app.static_folder, path)

@app.route('/api/sample_questions')
def get_sample_questions():
    """Return the list of sample questions."""
    return jsonify(test_queries)

@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'ok', 'port': port})

@app.route('/api/ask', methods=['POST'])
def ask():
    """Process a question through the agent."""
    data = request.json
    question = data.get('question', '')
    
    if not question:
        return jsonify({'error': 'No question provided'}), 400
    
    # Start processing in a background thread
    thread = Thread(target=process_question_thread, args=(question,))
    thread.daemon = True
    thread.start()
    
    return jsonify({'status': 'processing'})

@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    print('Client connected')
    emit('ready')

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    print('Client disconnected')

@socketio.on('message')
def handle_message(data):
    """Handle incoming messages from the client."""
    if data.get('robot') == 'left':
        # Left robot sent a message, process it
        question = data.get('text', '')
        thread = Thread(target=process_question_thread, args=(question,))
        thread.daemon = True
        thread.start()

if __name__ == '__main__':
    # Use the port determined above
    print(f"Starting server on port {port}...")
    try:
        socketio.run(app, host='0.0.0.0', port=port, debug=True)
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1) 