import json
import unittest
import sys
import os

from app import lambda_handler

class TestMathLambda(unittest.TestCase):
    """Test cases for the Math Lambda function."""
    
    def test_add_operation(self):
        """Test add operation."""
        context = {}
        event = {
            'operation': 'add',
            'parameters': {
                'a': 5,
                'b': 7
            }
        }
        response = lambda_handler(event, context)
        
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertEqual(body['result'], 12)
    
    def test_multiply_operation(self):
        """Test multiply operation."""
        context = {}
        event = {
            'operation': 'multiply',
            'parameters': {
                'a': 5,
                'b': 7
            }
        }
        response = lambda_handler(event, context)
        
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertEqual(body['result'], 35)
    
    def test_subtract_operation(self):
        """Test subtract operation."""
        context = {}
        event = {
            'operation': 'subtract',
            'parameters': {
                'a': 10,
                'b': 3
            }
        }
        response = lambda_handler(event, context)
        
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertEqual(body['result'], 7)
    
    def test_divide_operation(self):
        """Test divide operation."""
        context = {}
        event = {
            'operation': 'divide',
            'parameters': {
                'a': 10,
                'b': 2
            }
        }
        response = lambda_handler(event, context)
        
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertEqual(body['result'], 5.0)
    
    def test_divide_by_zero(self):
        """Test divide by zero error handling."""
        context = {}
        event = {
            'operation': 'divide',
            'parameters': {
                'a': 10,
                'b': 0
            }
        }
        response = lambda_handler(event, context)
        
        self.assertEqual(response['statusCode'], 400)
        body = json.loads(response['body'])
        self.assertTrue('error' in body)
    
    def test_invalid_operation(self):
        """Test invalid operation error handling."""
        context = {}
        event = {
            'operation': 'invalid_op',
            'parameters': {
                'a': 10,
                'b': 5
            }
        }
        response = lambda_handler(event, context)
        
        self.assertEqual(response['statusCode'], 400)
        body = json.loads(response['body'])
        self.assertTrue('error' in body)
    
    def test_missing_operation(self):
        """Test missing operation error handling."""
        context = {}
        event = {
            'parameters': {
                'a': 10,
                'b': 5
            }
        }
        response = lambda_handler(event, context)
        
        self.assertEqual(response['statusCode'], 400)
        body = json.loads(response['body'])
        self.assertTrue('error' in body)
    
    def test_api_gateway_invocation(self):
        """Test invocation through API Gateway."""
        context = {}
        event = {
            'body': json.dumps({
                'operation': 'add',
                'parameters': {
                    'a': 3,
                    'b': 4
                }
            })
        }
        response = lambda_handler(event, context)
        
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertEqual(body['result'], 7)

if __name__ == '__main__':
    unittest.main() 