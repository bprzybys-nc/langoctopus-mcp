#!/usr/bin/env fish

# Try to run in fish, fall back to zsh if fish is not available
if ! command -v fish > /dev/null
    exec zsh -c "$0 $argv"
end

# Function to retry commands on failure
function retry_command
    set max_attempts 3
    set attempt 1
    
    while test $attempt -le $max_attempts
        echo "Attempt $attempt of $max_attempts..."
        if $argv
            return 0
        end
        
        set attempt (math $attempt + 1)
        if test $attempt -le $max_attempts
            echo "Command failed, retrying in 2 seconds..."
            sleep 2
        end
    end
    
    echo "Command failed after $max_attempts attempts"
    return 1
end

# Create and activate virtual environment
echo "Setting up virtual environment..."
if ! command -v python3 -m venv > /dev/null
    echo "python3-venv not found, installing..."
    if command -v apt-get > /dev/null
        sudo apt-get update
        sudo apt-get install -y python3-venv
    else if command -v brew > /dev/null
        brew install python3
    else
        echo "Could not install python3-venv. Please install it manually."
        exit 1
    end
end

# Create virtual environment if it doesn't exist
if ! test -d venv
    retry_command python3 -m venv venv
end

# Activate virtual environment
source venv/bin/activate.fish

# Install dependencies
echo "Installing dependencies..."
retry_command pip install -r requirements.txt

# Create .env file if it doesn't exist
if ! test -f .env
    echo "Creating .env file..."
    cp env_example .env
    echo "Please edit .env file to add your API keys"
end

echo "Setup complete! Run 'python run.py' to start the agent." 