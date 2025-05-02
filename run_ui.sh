#!/bin/bash

# Define port variables
BACKEND_PORT=5001
FRONTEND_PORT=3001
ACTUAL_BACKEND_PORT=""
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to cleanup processes on exit
cleanup() {
  echo "Shutting down servers..."
  kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
  exit 0
}

# Function to check if port is available
check_port() {
  if lsof -i:$1 >/dev/null 2>&1; then
    return 1
  else
    return 0
  fi
}

# Function to kill process using a port (more forcefully)
kill_port_process() {
  local port=$1
  local pids=$(lsof -ti:$port)
  
  if [ -n "$pids" ]; then
    echo "Killing process using port $port..."
    kill -9 $pids
    # Wait longer to ensure the port is fully released
    sleep 3
    
    # Double-check if port is still in use
    if ! check_port $port; then
      echo "Port $port is still in use. Trying again more aggressively..."
      pids=$(lsof -ti:$port)
      if [ -n "$pids" ]; then
        kill -9 $pids
        sleep 5
      fi
      
      # Final check
      if ! check_port $port; then
        echo "ERROR: Could not free port $port. Please close the applications using this port manually."
        echo "Try running: sudo lsof -i:$port"
        echo "Then manually kill the processes using: sudo kill -9 [PID]"
        exit 1
      fi
    fi
  fi
}

# Function to verify and install Python dependencies
check_python_deps() {
  cd "${SCRIPT_DIR}/backend"
  echo "Checking Python dependencies..."
  pip install -r requirements.txt
  if [ $? -ne 0 ]; then
    echo "Error installing backend dependencies"
    cd "${SCRIPT_DIR}"
    exit 1
  fi
  cd "${SCRIPT_DIR}"
}

# Function to detect actual backend port by checking health endpoint
detect_backend_port() {
  # Try the original port first
  if curl -s "http://localhost:${BACKEND_PORT}/api/health" > /dev/null 2>&1; then
    ACTUAL_BACKEND_PORT=$BACKEND_PORT
    echo "Backend detected on original port: $ACTUAL_BACKEND_PORT"
    return 0
  fi
  
  # Check a range of ports
  for port in $(seq $BACKEND_PORT $(($BACKEND_PORT + 100))); do
    if [ "$port" != "$BACKEND_PORT" ]; then
      if curl -s "http://localhost:${port}/api/health" > /dev/null 2>&1; then
        ACTUAL_BACKEND_PORT=$port
        echo "Backend detected on alternative port: $ACTUAL_BACKEND_PORT"
        return 0
      fi
    fi
  done
  
  echo "Could not detect backend port"
  return 1
}

# Set trap for script termination
trap cleanup SIGINT SIGTERM

# Verify directory structure using absolute paths
BACKEND_DIR="${SCRIPT_DIR}/backend"
FRONTEND_DIR="${SCRIPT_DIR}/frontend"

if [ ! -d "$BACKEND_DIR" ]; then
  echo "Error: 'backend' directory not found at $BACKEND_DIR"
  exit 1
fi

if [ ! -d "$FRONTEND_DIR" ]; then
  echo "Error: 'frontend' directory not found at $FRONTEND_DIR."
  echo "Creating it..."
  mkdir -p "${FRONTEND_DIR}/src/components"
  mkdir -p "${FRONTEND_DIR}/src/services"
  mkdir -p "${FRONTEND_DIR}/src/styles"
  mkdir -p "${FRONTEND_DIR}/public"
  echo "Created frontend directory structure."
fi

# Check if package.json exists in frontend directory
if [ ! -f "${FRONTEND_DIR}/package.json" ]; then
  echo "Error: 'frontend/package.json' not found. Please make sure the frontend is properly set up."
  exit 1
fi

echo "Using directories:"
echo "- Script dir: ${SCRIPT_DIR}"
echo "- Backend dir: ${BACKEND_DIR}"
echo "- Frontend dir: ${FRONTEND_DIR}"

# Check if ports are in use and kill processes (no confirmation)
echo "Checking port availability..."
if ! check_port $BACKEND_PORT; then
  echo "Port $BACKEND_PORT is already in use. Killing process automatically..."
  kill_port_process $BACKEND_PORT
fi

if ! check_port $FRONTEND_PORT; then
  echo "Port $FRONTEND_PORT is already in use. Killing process automatically..."
  kill_port_process $FRONTEND_PORT
fi

# Verify ports again
if ! check_port $BACKEND_PORT || ! check_port $FRONTEND_PORT; then
  echo "ERROR: Ports still in use after cleanup attempt. Please close them manually."
  exit 1
fi

# Check and install Python dependencies
check_python_deps

# Check if Node dependencies are installed
if [ ! -d "${FRONTEND_DIR}/node_modules" ]; then
  echo "Installing frontend dependencies..."
  cd "${FRONTEND_DIR}" && npm install
  cd "${SCRIPT_DIR}"
fi

# Start the backend server (with verification)
echo "Starting backend server on port $BACKEND_PORT..."
cd "${BACKEND_DIR}" && python app.py --port $BACKEND_PORT &
BACKEND_PID=$!
cd "${SCRIPT_DIR}"

# Verify backend started successfully
echo "Waiting for backend to start..."
sleep 5
if ! ps -p $BACKEND_PID > /dev/null; then
  echo "Error: Backend server failed to start"
  exit 1
fi

# The eventlet.listen issue usually happens when the port is in use
# Let's do one more check to make sure the port is really free
if ! check_port $BACKEND_PORT; then
  echo "WARNING: Port $BACKEND_PORT appears to be in use even though we tried to free it."
  echo "The backend server might have selected an alternative port."
fi

# Try to detect actual backend port
echo "Detecting actual backend port..."
attempt=1
max_attempts=10
while [ $attempt -le $max_attempts ]; do
  if detect_backend_port; then
    break
  fi
  echo "Attempt $attempt/$max_attempts: Backend not detected yet. Waiting..."
  sleep 2
  attempt=$((attempt + 1))
done

if [ -z "$ACTUAL_BACKEND_PORT" ]; then
  echo "WARNING: Could not detect actual backend port. Using the default: $BACKEND_PORT"
  ACTUAL_BACKEND_PORT=$BACKEND_PORT
fi

# Start the frontend development server
echo "Starting frontend server on port $FRONTEND_PORT..."
# Explicitly cd to frontend directory using full path
cd "${FRONTEND_DIR}"
if [ $? -ne 0 ]; then
  echo "Error: Failed to change to frontend directory at ${FRONTEND_DIR}"
  kill $BACKEND_PID 2>/dev/null
  exit 1
fi

# Start the frontend with environment variables
REACT_APP_BACKEND_PORT=$ACTUAL_BACKEND_PORT PORT=$FRONTEND_PORT npm start &
FRONTEND_PID=$!
cd "${SCRIPT_DIR}"

# Verify frontend started successfully
echo "Waiting for frontend to start..."
sleep 5
if ! ps -p $FRONTEND_PID > /dev/null; then
  echo "Error: Frontend server failed to start"
  kill $BACKEND_PID 2>/dev/null
  exit 1
fi

echo "Servers are running!"
echo "- Backend: http://localhost:$ACTUAL_BACKEND_PORT"
echo "- Frontend: http://localhost:$FRONTEND_PORT"
echo "Press Ctrl+C to stop servers"

# Keep script running
wait $BACKEND_PID $FRONTEND_PID 