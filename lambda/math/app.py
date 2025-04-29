import json
import logging

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

def multiply(a: int, b: int) -> int:
    """Multiply two numbers"""
    return a * b

def subtract(a: int, b: int) -> int:
    """Subtract b from a"""
    return a - b

def divide(a: int, b: int) -> float:
    """Divide a by b"""
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
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Parse request body if coming from API Gateway
        if 'body' in event:
            try:
                body = json.loads(event['body'])
            except:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'Invalid JSON in request body'})
                }
            operation = body.get('operation')
            parameters = body.get('parameters', {})
        else:
            # Assume direct Lambda invocation
            operation = event.get('operation')
            parameters = event.get('parameters', {})
        
        # Validate operation
        if not operation:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Operation is required'})
            }
        
        # Execute the appropriate math operation
        if operation == 'add':
            a = int(parameters.get('a', 0))
            b = int(parameters.get('b', 0))
            result = add(a, b)
        elif operation == 'multiply':
            a = int(parameters.get('a', 0))
            b = int(parameters.get('b', 0))
            result = multiply(a, b)
        elif operation == 'subtract':
            a = int(parameters.get('a', 0))
            b = int(parameters.get('b', 0))
            result = subtract(a, b)
        elif operation == 'divide':
            a = int(parameters.get('a', 0))
            b = int(parameters.get('b', 0))
            result = divide(a, b)
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': f'Unknown operation: {operation}'})
            }
        
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
    
    except ValueError as e:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': str(e)})
        }
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        } 