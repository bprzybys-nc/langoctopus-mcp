import json
import logging
import os
import sys  # Import sys

# Set up logging
# logger = logging.getLogger()
# logger.setLevel(logging.DEBUG)  # Changed from INFO to DEBUG
# Replaced logger with print for test visibility
def print_debug(msg):
    print(f"DEBUG: {msg}", file=sys.stderr)

def print_info(msg):
    print(f"INFO: {msg}", file=sys.stderr)

def print_warning(msg):
    print(f"WARNING: {msg}", file=sys.stderr)
    
def print_error(msg):
    print(f"ERROR: {msg}", file=sys.stderr)

def add(a: int, b: int) -> int:
    """Add two numbers"""
    print_debug(f"Adding {a} + {b}")
    return a + b

def multiply(a: int, b: int) -> int:
    """Multiply two numbers"""
    print_debug(f"Multiplying {a} * {b}")
    return a * b

def subtract(a: int, b: int) -> int:
    """Subtract b from a"""
    print_debug(f"Subtracting {a} - {b}")
    return a - b

def divide(a: int, b: int) -> float:
    """Divide a by b"""
    print_debug(f"Dividing {a} / {b}")
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

def lambda_handler(event, context):
    """
    Lambda handler for the Math MCP service
    
    Expected event format:
    {
        "operation": "add|multiply|subtract|divide",
        "parameters": {
            "a": 5,
            "b": 3
        }
    }
    """
    try:
        # Log the incoming event
        print_info(f"LAMBDA_HANDLER_MATH ENTRY - Received event: {json.dumps(event)}")
        # print_debug(f"Environment variables: {os.environ.keys()}") # Commented out for brevity

        # Log CWD and script directory
        print_debug(f"LAMBDA_HANDLER_MATH - CWD: {os.getcwd()}")
        try:
            script_dir = os.path.dirname(os.path.realpath(__file__))
            print_debug(f"LAMBDA_HANDLER_MATH - Script Dir: {script_dir}")
        except NameError:
            print_warning("LAMBDA_HANDLER_MATH - __file__ not defined, cannot determine script directory.")
        
        # Parse request body if coming from API Gateway
        if 'body' in event and event['body'] is not None: # Added check for None body
            print_debug("Parsing API Gateway body")
            try:
                # Check if body is already a dict (possible if locally testing with pre-parsed event)
                if isinstance(event['body'], dict):
                     body = event['body']
                else:
                     body = json.loads(event['body'])
                print_debug(f"Parsed body: {json.dumps(body)}")
                operation = body.get('operation')
                parameters = body.get('parameters', {})
            except json.JSONDecodeError:
                print_warning("Failed to parse JSON body")
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'Invalid JSON in request body'})
                }
        else:
            # Assume direct Lambda invocation
            print_debug("Direct Lambda invocation")
            operation = event.get('operation')
            parameters = event.get('parameters', {})
        
        print_info(f"LAMBDA_HANDLER_MATH - Parsed operation: {operation} (Type: {type(operation)})")
        print_info(f"LAMBDA_HANDLER_MATH - Parsed parameters: {json.dumps(parameters)}")
        
        # Validate operation
        if not operation:
            print_warning("Missing operation parameter")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Operation is required'})
            }
        
        # Execute the appropriate math operation
        try:
            # Log operation value just before checking
            print_info(f"LAMBDA_HANDLER_MATH - Checking operation: '{operation}'")
            print_info(f"LAMBDA_HANDLER_MATH - Checking operation repr: {repr(operation)}")
            
            # Ensure parameters 'a' and 'b' exist before trying to convert to int
            if 'a' not in parameters or 'b' not in parameters:
                 if operation in ['add', 'multiply', 'subtract', 'divide']: # Only raise if needed for the op
                    print_warning(f"Missing 'a' or 'b' in parameters for operation '{operation}'")
                    return {
                        'statusCode': 400,
                        'body': json.dumps({'error': f"Missing 'a' or 'b' parameter for operation '{operation}'"})
                    }

            if operation == 'add':
                a = int(parameters.get('a')) # Removed default 0
                b = int(parameters.get('b')) # Removed default 0
                result = add(a, b)
            elif operation == 'multiply':
                a = int(parameters.get('a')) # Removed default 0
                b = int(parameters.get('b')) # Removed default 0
                result = multiply(a, b)
            elif operation == 'subtract':
                a = int(parameters.get('a')) # Removed default 0
                b = int(parameters.get('b')) # Removed default 0
                result = subtract(a, b)
                print_info(f"LAMBDA_HANDLER_MATH - Subtract result: {result} (Type: {type(result)})")
            elif operation == 'divide':
                a = int(parameters.get('a')) # Removed default 0
                b = int(parameters.get('b')) # Removed default 0
                if b == 0:
                    print_warning("Attempted to divide by zero")
                    return {
                        'statusCode': 400,
                        'body': json.dumps({'error': 'Cannot divide by zero'})
                    }
                result = divide(a, b)
            else:
                print_warning(f"Unknown operation: {operation}")
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': f'Unknown operation: {operation}'})
                }
        except (ValueError, TypeError) as e: # Catch TypeError for int() conversion
            print_warning(f"ValueError/TypeError in parameters: {str(e)}")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': f'Invalid parameters: {str(e)}'})
            }
            
        print_debug(f"Operation completed successfully. Result: {result}")
        # Return the result
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'result': result
            })
        }
    
    except Exception as e: # Catch broader exceptions at the top level
        print_error(f"Error processing request: {str(e)} - Event: {json.dumps(event)}")
        # Add traceback for better debugging
        import traceback
        print_error(traceback.format_exc())
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        } 