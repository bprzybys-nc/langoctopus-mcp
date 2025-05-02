#!/usr/bin/env python3
import sys
import os
import unittest
import logging
import argparse
import importlib
import subprocess

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_tests(pattern):
    """
    Run tests matching the given pattern
    """
    # Define project_root early for use within the function
    project_root = os.path.dirname(os.path.abspath(__file__))
    logger.info(f"Running tests in tests/lambda matching {pattern}...")
    
    # Reset sys.modules
    modules_to_remove = []
    for mod in sys.modules.keys():
        if mod.startswith('app') or mod.startswith('lambda.') or mod.startswith('tests.lambda.'):
            modules_to_remove.append(mod)
    
    # # Commented out the generic removal for now to rely on specific reload/clear -> UNCOMMENTING
    for mod in modules_to_remove:
        logger.debug(f"Removing module {mod} from sys.modules")
        if mod in sys.modules: # Check if it exists before deleting
            del sys.modules[mod]

    # Add all lambda directories to path -> KEEP REMOVED
    # project_root = os.path.dirname(os.path.abspath(__file__))
    lambda_dirs = [
        os.path.join(project_root, 'lambda', d) 
        for d in os.listdir(os.path.join(project_root, 'lambda'))
        if os.path.isdir(os.path.join(project_root, 'lambda', d))
    ]
    
    for lambda_dir in lambda_dirs:
        if lambda_dir not in sys.path:
            logger.debug(f"Adding {lambda_dir} to sys.path")
            sys.path.insert(0, lambda_dir)
    
    # Discover and run tests using discover consistently
    loader = unittest.TestLoader()
    suite = loader.discover('lambda', pattern=pattern)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if not result.wasSuccessful():
        logger.error(f"Some tests matching '{pattern}' failed")
        return False
    
    logger.info(f"All tests matching '{pattern}' passed!")
    return True

def main():
    """
    Main function to run tests
    """
    parser = argparse.ArgumentParser(description='Run tests for the MCP service')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--math', action='store_true', help='Run math lambda tests')
    group.add_argument('--weather', action='store_true', help='Run weather lambda tests')
    group.add_argument('--all', action='store_true', help='Run all lambda tests')
    
    args = parser.parse_args()
    
    # Ensure lambda path is added early
    # project_root = os.path.dirname(os.path.abspath(__file__))
    # math_lambda_path = os.path.join(project_root, 'lambda', 'math')
    # weather_lambda_path = os.path.join(project_root, 'lambda', 'weather')
    # if math_lambda_path not in sys.path:
    #     logger.debug(f"Adding {math_lambda_path} to sys.path for main")
    #     sys.path.insert(0, math_lambda_path)

    # exit_code = 1 # Default to failure

    if args.math:
        # clear_math_module() # Keep clear -> REMOVE CALL
        return 0 if run_tests('test_math_*.py') else 1 # Simplified return

    elif args.weather:
        # clear_math_module() # Keep clear -> REMOVE CALL
        return 0 if run_tests('test_weather_*.py') else 1 # Simplified return

    elif args.all:
        success = True
        logger.info("Running ALL tests sequentially in separate processes...")
        
        # Run Math tests in a subprocess
        logger.info("Running Math tests...")
        math_command = [sys.executable, __file__, "--math"]
        math_result = subprocess.run(math_command, capture_output=True, text=True, check=False) # Don't check=True, handle exit code manually
        print("--- Math Test Output ---")
        print(math_result.stdout)
        print(math_result.stderr)
        print("-----------------------")
        if math_result.returncode != 0:
            logger.error("Math tests failed.")
            success = False
        else:
            logger.info("Math tests passed.")
            
        # Run Weather tests in a subprocess
        logger.info("Running Weather tests...")
        weather_command = [sys.executable, __file__, "--weather"]
        weather_result = subprocess.run(weather_command, capture_output=True, text=True, check=False)
        print("--- Weather Test Output ---")
        print(weather_result.stdout)
        print(weather_result.stderr)
        print("-------------------------")
        if weather_result.returncode != 0:
            logger.error("Weather tests failed.")
            success = False
        else:
             logger.info("Weather tests passed.")
        
        return 0 if success else 1
        # exit_code = 0 if success else 1

    # return exit_code

if __name__ == '__main__':
    # Need to get the exit code from main()
    final_exit_code = main()
    sys.exit(final_exit_code) 