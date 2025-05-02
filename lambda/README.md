# MCP Lambda Implementation

This directory contains the implementation of the MCP services (math and weather) as AWS Lambda functions behind API Gateway.

## Structure

- `math/`: Math service Lambda implementation
- `weather/`: Weather service Lambda implementation

## Local Development

The Lambda functions can be run locally using AWS SAM CLI. All services are configured with no authentication ("noauth") for easier development as requested.

### Prerequisites

- AWS SAM CLI
- Python 3.9+
- Required Python packages (install using `pip install -r requirements.txt`)

### Running Locally

1. Run the SAM local API:
   ```bash
   python run_lambda_local.py
   ```

   This will:
   - Start the SAM local API on port 3000
   - Test the math and weather endpoints
   - Keep running until you press Ctrl+C

2. In another terminal, you can interact with the Lambda-based MCP services using:
   ```bash
   python lambda_client.py
   ```

### API Endpoints

When running locally, the API endpoints are:

- `http://localhost:3000/math`: For math operations
  ```json
  {
    "operation": "add|multiply|subtract|divide",
    "parameters": {
      "a": 5,
      "b": 3
    }
  }
  ```

- `http://localhost:3000/weather`: For weather operations
  ```json
  {
    "operation": "get_weather|get_forecast",
    "parameters": {
      "location": "London",
      "days": 3  // Optional, for get_forecast
    }
  }
  ```

## Deployment

The SAM template (`template.yaml`) includes everything needed to deploy to AWS:

```bash
sam build
sam deploy --guided
```

This will deploy:
- API Gateway with no authentication
- Math Lambda function
- Weather Lambda function

## SAML Authentication

SAML authentication is prepared but disabled for now according to the requirements. The template structure is ready for future enhancements when SAML authentication is needed.

When ready to implement SAML authentication:
1. Uncomment the `SamlAuthorizer` section in `template.yaml`
2. Create the authorizer implementation in `lambda/authorizer/`
3. Update the API Gateway `Auth` configuration to use the authorizer
4. Set the appropriate environment variables for the SAML identity provider

### Running the Agent with Lambda Backend

1.  **Set Environment Variables:** Ensure your `GOOGLE_API_KEY` and `API_GATEWAY_URL` (pointing to your deployed API Gateway stage) are set in your environment or a `.env` file.

2.  **Run the Client:**
    ```bash
    # Navigate to the lambda directory if you are not already there
    # cd lambda 
    poetry run python client.py 
    ```

This will start the agent, which will use the `LambdaMcpAdapter` (defined in `client_adapter.py`) to communicate with your deployed Lambda functions via the API Gateway URL. 