import json
import logging
import os
import random

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)  # Changed from INFO to DEBUG

# List of weather templates with location variable
WEATHER_TEMPLATES = [
    "The skies over {location} are clear today with gentle breezes.",
    "A beautiful sunny day in {location} with temperatures above average.",
    "Residents of {location} can expect scattered clouds with occasional sunshine.",
    "Heavy rain is currently falling in {location}, bringing much needed moisture.",
    "Thunderstorms are rolling through {location} with lightning visible on the horizon.",
    "Light snow is blanketing {location}, creating a winter wonderland.",
    "Dense fog has reduced visibility in {location} this morning.",
    "Strong winds are sweeping through {location}, causing minor disruptions.",
    "A mix of sun and clouds hover over {location} today.",
    "Unusually warm temperatures are being reported in {location}.",
    "Light drizzle is falling across {location}, but expected to clear soon.",
    "A cold front is moving through {location}, bringing cooler temperatures.",
    "Perfect weather conditions in {location} with clear skies and comfortable temperatures."
]

# List of forecast templates with location variable
FORECAST_TEMPLATES = [
    "Expect sunny conditions in {location} with temperatures remaining stable.",
    "Increasing cloud cover will bring afternoon showers to {location}.",
    "A warming trend begins in {location} with clearer skies expected.",
    "Rain will develop later in the day across {location}, becoming heavier overnight.",
    "Thunderstorms will move through {location} with potential for heavy downpours.",
    "Snow showers will continue in {location} with accumulations possible.",
    "Morning fog in {location} will give way to partly cloudy conditions.",
    "Windy conditions will persist in {location} with gusts up to 30mph.",
    "A beautiful day ahead for {location} with abundant sunshine.",
    "Temperatures in {location} will drop as a cold front approaches.",
    "Scattered showers possible throughout the day in {location}.",
    "Unstable atmospheric conditions over {location} may lead to isolated storms.",
    "Pleasant weather will continue in {location} with ideal conditions."
]

def get_weather(location: str) -> str:
    """
    Get the current weather for a location
    """
    logger.debug(f"get_weather called for location: {location}")
    
    # Check if API key exists
    api_key = os.environ.get('WEATHER_API_KEY')
    logger.debug(f"WEATHER_API_KEY environment variable: {'present' if api_key else 'missing'}")
    
    # Simulate a weather response using templates
    weather_template = random.choice(WEATHER_TEMPLATES)
    return weather_template.format(location=location)

def get_forecast(location: str, days: int = 3) -> str:
    """
    Get the weather forecast for a location
    """
    logger.debug(f"get_forecast called for location: {location}, days: {days}")
    
    # Check if API key exists
    api_key = os.environ.get('WEATHER_API_KEY')
    logger.debug(f"WEATHER_API_KEY environment variable: {'present' if api_key else 'missing'}")
    
    # Simulate a forecast response using templates
    forecast = [random.choice(FORECAST_TEMPLATES).format(location=location) for _ in range(days)]
    forecast_str = " ".join([f"Day {i+1}: {f}" for i, f in enumerate(forecast)])
    return f"{days}-day forecast for {location}: {forecast_str}"

def lambda_handler(event, context):
    """
    Lambda handler for the Weather MCP service
    
    Expected event format:
    {
        "operation": "get_weather|get_forecast",
        "parameters": {
            "location": "London",
            "days": 3  # Optional, for forecast only
        }
    }
    """
    try:
        # Log the incoming event
        logger.info(f"Received event: {json.dumps(event)}")
        logger.debug(f"Environment variables: {str(os.environ.keys())}")
        
        # Parse request body if coming from API Gateway
        if 'body' in event:
            try:
                logger.debug("Parsing API Gateway body")
                body = json.loads(event['body'])
                logger.debug(f"Parsed body: {json.dumps(body)}")
            except Exception as e:
                logger.error(f"Error parsing body: {str(e)}")
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'Invalid JSON in request body'})
                }
            operation = body.get('operation')
            parameters = body.get('parameters', {})
        else:
            # Assume direct Lambda invocation
            logger.debug("Direct Lambda invocation")
            operation = event.get('operation')
            parameters = event.get('parameters', {})
        
        logger.debug(f"Operation: {operation}")
        logger.debug(f"Parameters: {json.dumps(parameters)}")
        
        # Validate operation
        if not operation:
            logger.warning("Missing operation parameter")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Operation is required'})
            }
        
        # Execute the appropriate weather operation
        if operation == 'get_weather':
            location = parameters.get('location')
            if not location:
                logger.warning("Missing location parameter for get_weather")
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'Location is required'})
                }
            result = get_weather(location)
        elif operation == 'get_forecast':
            location = parameters.get('location')
            if not location:
                logger.warning("Missing location parameter for get_forecast")
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'Location is required'})
                }
            days = int(parameters.get('days', 3))
            result = get_forecast(location, days)
        else:
            logger.warning(f"Unknown operation: {operation}")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': f'Unknown operation: {operation}'})
            }
        
        logger.debug(f"Operation result: {result}")
        
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
    
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        } 