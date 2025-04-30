import asyncio
import os
import sys
import logging
from dotenv import load_dotenv

# Add project root to path to allow importing client dependencies if needed later
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_connection():
    logger.info("Attempting to load environment variables...")
    try:
        from dotenv import load_dotenv
        env_path = os.path.join(project_root, '.env')
        if os.path.exists(env_path):
            load_dotenv(dotenv_path=env_path)
            logger.info(f"Loaded environment variables from {env_path}")
        else:
            logger.warning(".env file not found. Relying on environment variables.")
    except ImportError:
        logger.warning("python-dotenv not installed. Relying on environment variables.")

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        logger.critical("GOOGLE_API_KEY environment variable not set. Cannot test connection.")
        return False
    else:
         # Mask part of the key for logging
        masked_key = api_key[:4] + "..." + api_key[-4:]
        logger.info(f"Found GOOGLE_API_KEY: {masked_key}")

    model_name = "gemini-2.5-flash-preview-04-17" # Using the corrected model name
    logger.info(f"Attempting to initialize ChatGoogleGenerativeAI with model: {model_name}")

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        model = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0 # Reduce randomness for simple test
        )
        logger.info("Model initialized successfully.")

        logger.info("Attempting simple API call...")
        response = await model.ainvoke("Hello?")
        
        if response and response.content:
             logger.info(f"Received response: {response.content[:100]}...") # Log beginning of response
             logger.info("SUCCESS: Gemini API connection and model seem operational.")
             return True
        else:
             logger.error("FAILED: Received empty or invalid response from API.")
             return False

    except ImportError as e:
        logger.critical(f"FAILED: Could not import langchain_google_genai. Is it installed correctly? Error: {e}")
        return False
    except Exception as e:
        logger.error(f"FAILED: Error during model initialization or API call: {e}", exc_info=True)
        # Log the specific type of exception, especially for API errors
        if "404" in str(e) and model_name in str(e):
             logger.error(f"API returned 404 Not Found for model '{model_name}'. Check if the model name is still valid.")
        return False

if __name__ == "__main__":
    if asyncio.run(test_connection()):
        sys.exit(0) # Exit code 0 for success
    else:
        sys.exit(1) # Exit code 1 for failure 