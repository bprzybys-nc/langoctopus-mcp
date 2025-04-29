#!/usr/bin/env python3
import sys
import os
import unittest
import logging
import argparse
import importlib

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_tests(pattern):
    """
    Run tests matching the given pattern
    """
    logger.info(f"Running tests in tests/lambda matching {pattern}...")
    
    # Reset sys.modules to make sure we get fresh module imports
    for mod in list(sys.modules.keys()):
        if mod.startswith('app'):
            logger.debug(f"Removing module {mod} from sys.modules")
            del sys.modules[mod]
    
    # Add all lambda directories to path
    project_root = os.path.dirname(os.path.abspath(__file__))
    lambda_dirs = [
        os.path.join(project_root, 'lambda', d) 
        for d in os.listdir(os.path.join(project_root, 'lambda'))
        if os.path.isdir(os.path.join(project_root, 'lambda', d))
    ]
    
    for lambda_dir in lambda_dirs:
        if lambda_dir not in sys.path:
            logger.debug(f"Adding {lambda_dir} to sys.path")
            sys.path.insert(0, lambda_dir)
    
    # Running individual tests works, so let's do that instead of using the test runner
    if pattern == 'test_weather_*.py':
        logger.info("Running weather tests directly")
        # Import the test module
        test_module = importlib.import_module('tests.lambda.test_weather_lambda')
        # Run the tests
        result = unittest.TextTestRunner(verbosity=1).run(
            unittest.defaultTestLoader.loadTestsFromModule(test_module)
        )
        return result.wasSuccessful()
    elif pattern == 'test_math_*.py':
        logger.info("Running math tests directly")
        # Import the test module
        test_module = importlib.import_module('tests.lambda.test_math_lambda')
        # Run the tests
        result = unittest.TextTestRunner(verbosity=1).run(
            unittest.defaultTestLoader.loadTestsFromModule(test_module)
        )
        return result.wasSuccessful()
    else:
        # Discover and run tests
        loader = unittest.TestLoader()
        suite = loader.discover('tests/lambda', pattern=pattern)
        runner = unittest.TextTestRunner(verbosity=1)
        result = runner.run(suite)
        
        if not result.wasSuccessful():
            logger.error("Some tests failed")
            return False
        
        logger.info("All tests passed!")
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
    
    if args.math:
        return 0 if run_tests('test_math_*.py') else 1
    elif args.weather:
        return 0 if run_tests('test_weather_*.py') else 1
    elif args.all:
        success = True
        if not run_tests('test_math_*.py'):
            success = False
        if not run_tests('test_weather_*.py'):
            success = False
        return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main()) 