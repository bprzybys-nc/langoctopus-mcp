#!/usr/bin/env zsh

# Function to retry commands on failure
retry_command() {
    local max_attempts=3
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        echo "Attempt $attempt of $max_attempts..."
        if "$@"; then
            return 0
        fi
        
        attempt=$((attempt + 1))
        if [ $attempt -le $max_attempts ]; then
            echo "Command failed, retrying in 2 seconds..."
            sleep 2
        fi
    done
    
    echo "Command failed after $max_attempts attempts"
    return 1
}

# Create and activate virtual environment
echo "Setting up virtual environment..."
if ! command -v python3 -m venv > /dev/null; then
    echo "python3-venv not found, installing..."
    if command -v apt-get > /dev/null; then
        sudo apt-get update
        sudo apt-get install -y python3-venv
    elif command -v brew > /dev/null; then
        brew install python3
    else
        echo "Could not install python3-venv. Please install it manually."
        exit 1
    fi
fi

# Create virtual environment if it doesn't exist
if [ ! -d venv ]; then
    retry_command python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
retry_command pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp env_example .env
    echo "Please edit .env file to add your API keys"
fi

echo "Setup complete! Run 'python run.py' to start the agent." 