import json
import unittest
import sys
import os

# Add lambda directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../../lambda/math'))

from app import lambda_handler

class TestMathLambda(unittest.TestCase):
    """Test cases for the Math Lambda function."""
    
    def test_add_operation(self):
        """Test add operation."""
        event = {
            'operation': 'add',
            'parameters': {
                'a': 5,
                'b': 7
            }
        }
        context = {}
        response = lambda_handler(event, context)
        
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertEqual(body['result'], 12)
    
    def test_multiply_operation(self):
        """Test multiply operation."""
        event = {
            'operation': 'multiply',
            'parameters': {
                'a': 5,
                'b': 7
            }
        }
        context = {}
        response = lambda_handler(event, context)
        
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertEqual(body['result'], 35)
    
    def test_subtract_operation(self):
        """Test subtract operation."""
        event = {
            'operation': 'subtract',
            'parameters': {
                'a': 10,
                'b': 3
            }
        }
        context = {}
        response = lambda_handler(event, context)
        
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertEqual(body['result'], 7)
    
    def test_divide_operation(self):
        """Test divide operation."""
        event = {
            'operation': 'divide',
            'parameters': {
                'a': 10,
                'b': 2
            }
        }
        context = {}
        response = lambda_handler(event, context)
        
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertEqual(body['result'], 5.0)
    
    def test_divide_by_zero(self):
        """Test divide by zero error handling."""
        event = {
            'operation': 'divide',
            'parameters': {
                'a': 10,
                'b': 0
            }
        }
        context = {}
        response = lambda_handler(event, context)
        
        self.assertEqual(response['statusCode'], 400)
        body = json.loads(response['body'])
        self.assertTrue('error' in body)
    
    def test_invalid_operation(self):
        """Test invalid operation error handling."""
        event = {
            'operation': 'invalid_op',
            'parameters': {
                'a': 10,
                'b': 5
            }
        }
        context = {}
        response = lambda_handler(event, context)
        
        self.assertEqual(response['statusCode'], 400)
        body = json.loads(response['body'])
        self.assertTrue('error' in body)
    
    def test_missing_operation(self):
        """Test missing operation error handling."""
        event = {
            'parameters': {
                'a': 10,
                'b': 5
            }
        }
        context = {}
        response = lambda_handler(event, context)
        
        self.assertEqual(response['statusCode'], 400)
        body = json.loads(response['body'])
        self.assertTrue('error' in body)
    
    def test_api_gateway_invocation(self):
        """Test invocation through API Gateway."""
        event = {
            'body': json.dumps({
                'operation': 'add',
                'parameters': {
                    'a': 3,
                    'b': 4
                }
            })
        }
        context = {}
        response = lambda_handler(event, context)
        
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertEqual(body['result'], 7)

if __name__ == '__main__':
    unittest.main() 