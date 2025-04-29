import json
import unittest
import sys
import os
import logging

# Configure test logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Add lambda directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../../lambda/weather'))

from app import lambda_handler

class TestWeatherLambda(unittest.TestCase):
    """Test cases for the Weather Lambda function."""
    
    def setUp(self):
        """Set up test environment variables."""
        # Ensure WEATHER_API_KEY is set for tests
        if 'WEATHER_API_KEY' not in os.environ:
            logger.debug("Setting WEATHER_API_KEY for tests")
            os.environ['WEATHER_API_KEY'] = 'test-api-key'
        
        logger.debug(f"Environment variables: {list(os.environ.keys())}")
    
    def test_get_weather_operation_direct(self):
        """Test get_weather operation with direct invocation."""
        event = {
            'operation': 'get_weather',
            'parameters': {
                'location': 'London'
            }
        }
        context = {}
        logger.debug(f"Calling lambda_handler with event: {json.dumps(event)}")
        response = lambda_handler(event, context)
        logger.debug(f"Response: {json.dumps(response)}")
        
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertTrue('result' in body)
        self.assertIn('London', body['result'])
    
    def test_get_forecast_operation_direct(self):
        """Test get_forecast operation with direct invocation."""
        event = {
            'operation': 'get_forecast',
            'parameters': {
                'location': 'Tokyo',
                'days': 5
            }
        }
        context = {}
        logger.debug(f"Calling lambda_handler with event: {json.dumps(event)}")
        response = lambda_handler(event, context)
        logger.debug(f"Response: {json.dumps(response)}")
        
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertTrue('result' in body)
        self.assertIn('Tokyo', body['result'])
        self.assertIn('5-day', body['result'])
    
    def test_get_forecast_default_days_direct(self):
        """Test get_forecast with default days parameter with direct invocation."""
        event = {
            'operation': 'get_forecast',
            'parameters': {
                'location': 'Paris'
            }
        }
        context = {}
        logger.debug(f"Calling lambda_handler with event: {json.dumps(event)}")
        response = lambda_handler(event, context)
        logger.debug(f"Response: {json.dumps(response)}")
        
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertTrue('result' in body)
        self.assertIn('Paris', body['result'])
        self.assertIn('3-day', body['result'])
    
    def test_missing_location_direct(self):
        """Test missing location parameter error handling with direct invocation."""
        event = {
            'operation': 'get_weather',
            'parameters': {}
        }
        context = {}
        logger.debug(f"Calling lambda_handler with event: {json.dumps(event)}")
        response = lambda_handler(event, context)
        logger.debug(f"Response: {json.dumps(response)}")
        
        self.assertEqual(response['statusCode'], 400)
        body = json.loads(response['body'])
        self.assertTrue('error' in body)
        self.assertIn('Location is required', body['error'])
    
    def test_invalid_operation(self):
        """Test invalid operation error handling."""
        event = {
            'operation': 'invalid_operation',
            'parameters': {
                'location': 'Berlin'
            }
        }
        context = {}
        logger.debug(f"Calling lambda_handler with event: {json.dumps(event)}")
        response = lambda_handler(event, context)
        logger.debug(f"Response: {json.dumps(response)}")
        
        self.assertEqual(response['statusCode'], 400)
        body = json.loads(response['body'])
        self.assertTrue('error' in body)
    
    def test_missing_operation(self):
        """Test missing operation error handling."""
        event = {
            'parameters': {
                'location': 'Rome'
            }
        }
        context = {}
        logger.debug(f"Calling lambda_handler with event: {json.dumps(event)}")
        response = lambda_handler(event, context)
        logger.debug(f"Response: {json.dumps(response)}")
        
        self.assertEqual(response['statusCode'], 400)
        body = json.loads(response['body'])
        self.assertTrue('error' in body)
    
    def test_api_gateway_invocation(self):
        """Test invocation through API Gateway."""
        event = {
            'body': json.dumps({
                'operation': 'get_weather',
                'parameters': {
                    'location': 'Sydney'
                }
            })
        }
        context = {}
        logger.debug(f"Calling lambda_handler with event: {json.dumps(event)}")
        response = lambda_handler(event, context)
        logger.debug(f"Response: {json.dumps(response)}")
        
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertTrue('result' in body)
        self.assertIn('Sydney', body['result'])

if __name__ == '__main__':
    unittest.main() 