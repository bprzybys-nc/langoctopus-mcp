import asyncio
import subprocess
import os
import signal
import sys
import time
from client import main

server_processes = []

def start_servers():
    print("Starting MCP servers...")
    # Start math server (stdio transport)
    math_server = subprocess.Popen(["python", "math_server.py"], 
                             stdin=subprocess.PIPE, 
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
    server_processes.append(math_server)
    
    # Start weather server (SSE transport)
    weather_server = subprocess.Popen(["python", "weather_server.py"])
    server_processes.append(weather_server)
    
    print("Waiting for servers to initialize...")
    time.sleep(2)  # Give servers time to start

def cleanup(sig=None, frame=None):
    print("\nShutting down servers...")
    for process in server_processes:
        try:
            if sys.platform == 'win32':
                process.kill()
            else:
                process.terminate()
        except Exception as e:
            print(f"Error shutting down server: {e}")
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    try:
        start_servers()
        asyncio.run(main())
    except Exception as e:
        print(f"Error running agent: {e}")
    finally:
        cleanup() 