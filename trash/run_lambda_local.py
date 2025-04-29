#!/usr/bin/env python3
import os
import sys
import signal
import subprocess
import time
import webbrowser
import threading
import logging

# Constants
SAM_PORT = 3000
API_ENDPOINT = f"http://localhost:{SAM_PORT}"

# Process tracking
sam_process = None

# Set up better logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def signal_handler(sig, frame):
    """Handle interrupt signals by cleaning up processes."""
    print("\nShutting down...")
    cleanup()
    sys.exit(0)

def cleanup():
    """Clean up any running processes."""
    if sam_process:
        logger.info("Stopping SAM local API...")
        sam_process.terminate()
        try:
            sam_process.wait(timeout=5)
            logger.info("SAM local API stopped successfully")
        except subprocess.TimeoutExpired:
            logger.warning("SAM process did not terminate gracefully, killing it")
            sam_process.kill()

def start_sam_local():
    """Start SAM local API."""
    global sam_process
    
    print("Starting SAM local API...")
    # Set NOAUTH=true to enable development mode with no authentication
    env = {**os.environ, "NOAUTH": "true"}
    
    try:
        sam_process = subprocess.Popen(
            ["sam", "local", "start-api", "--port", str(SAM_PORT)],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for SAM to start
        for _ in range(30):  # Wait up to 30 seconds
            if sam_process.poll() is not None:
                # Process exited
                stdout, stderr = sam_process.communicate()
                print(f"SAM process exited with code {sam_process.returncode}")
                print(f"stdout: {stdout}")
                print(f"stderr: {stderr}")
                sys.exit(1)
            
            try:
                import requests
                response = requests.get(f"{API_ENDPOINT}/ping")
                if response.status_code == 200:
                    print(f"SAM local API is running at {API_ENDPOINT}")
                    return True
            except:
                pass
            
            time.sleep(1)
            
        print("Timed out waiting for SAM local API to start")
        return False
    
    except Exception as e:
        print(f"Error starting SAM local API: {str(e)}")
        return False

def test_endpoints():
    """Test the math and weather endpoints."""
    import requests
    import json
    
    # Test Math API
    logger.info("Testing Math API...")
    math_payload = {
        "operation": "add",
        "parameters": {
            "a": 5,
            "b": 7
        }
    }
    try:
        response = requests.post(f"{API_ENDPOINT}/math", json=math_payload, timeout=10)
        logger.info(f"Math API test status: {response.status_code}")
        if response.status_code == 200:
            logger.info(f"Math API test successful: {response.json()}")
        else:
            logger.warning(f"Math API test returned non-200 status: {response.status_code}")
            logger.warning(f"Response: {response.text}")
    except Exception as e:
        logger.error(f"Error testing Math API: {str(e)}")
    
    # Test Weather API
    logger.info("Testing Weather API...")
    weather_payload = {
        "operation": "get_weather",
        "parameters": {
            "location": "London"
        }
    }
    try:
        response = requests.post(f"{API_ENDPOINT}/weather", json=weather_payload, timeout=10)
        logger.info(f"Weather API test status: {response.status_code}")
        if response.status_code == 200:
            logger.info(f"Weather API test successful: {response.json()}")
        else:
            logger.warning(f"Weather API test returned non-200 status: {response.status_code}")
            logger.warning(f"Response: {response.text}")
    except Exception as e:
        logger.error(f"Error testing Weather API: {str(e)}")

def main():
    """Main function to run local Lambda environment."""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start SAM local API
        if not start_sam_local():
            sys.exit(1)
        
        # Wait a moment for API to stabilize
        time.sleep(2)
        
        # Test endpoints
        test_endpoints()
        
        # Set the API Gateway URL for the lambda client
        os.environ["API_GATEWAY_URL"] = API_ENDPOINT
        
        print("\nAPI is ready! You can now use lambda_client.py to interact with the services.")
        print("Press Ctrl+C to quit.")
        
        # Keep the script running until interrupted
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        cleanup()

if __name__ == "__main__":
    main() 