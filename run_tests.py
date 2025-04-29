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
    
    # Reset sys.modules
    modules_to_remove = []
    for mod in sys.modules.keys():
        if mod.startswith('app') or mod.startswith('lambda.') or mod.startswith('tests.lambda.'):
            modules_to_remove.append(mod)
    
    # # Commented out the generic removal for now to rely on specific reload/clear
    # for mod in modules_to_remove:
    #     logger.debug(f"Removing module {mod} from sys.modules")
    #     if mod in sys.modules: # Check if it exists before deleting
    #         del sys.modules[mod]

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
    
    # Discover and run tests using discover consistently
    loader = unittest.TestLoader()
    suite = loader.discover('tests/lambda', pattern=pattern)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if not result.wasSuccessful():
        logger.error(f"Some tests matching '{pattern}' failed")
        return False
    
    logger.info(f"All tests matching '{pattern}' passed!")
    return True

def clear_math_module():
    """Specifically removes the math lambda module from cache."""
    modules_to_clear = ['lambda.math.app', 'app'] # Also clear plain 'app'
    for module_name in modules_to_clear:
        if module_name in sys.modules:
            logger.debug(f"Specifically removing module {module_name} from sys.modules")
            del sys.modules[module_name]

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
    project_root = os.path.dirname(os.path.abspath(__file__))
    math_lambda_path = os.path.join(project_root, 'lambda', 'math')
    if math_lambda_path not in sys.path:
        logger.debug(f"Adding {math_lambda_path} to sys.path for main")
        sys.path.insert(0, math_lambda_path)

    if args.math:
        clear_math_module()
        # Explicitly reload app before running math tests
        try:
            import app # Ensure app is loaded if not already
            importlib.reload(app)
            logger.info("Reloaded 'app' module for math tests.")
        except ImportError:
            logger.error("Could not import 'app' to reload for math tests.")
        except KeyError:
            logger.warning("'app' module not in sys.modules, cannot reload.") # Should not happen if imported
        return 0 if run_tests('test_math_*.py') else 1
    elif args.weather:
        # Clear math module even when running only weather tests, just in case
        clear_math_module()
        return 0 if run_tests('test_weather_*.py') else 1
    elif args.all:
        success = True
        clear_math_module()
        # Explicitly reload app before running math tests
        try:
            import app # Ensure app is loaded if not already
            importlib.reload(app)
            logger.info("Reloaded 'app' module for math tests run in --all.")
        except ImportError:
            logger.error("Could not import 'app' to reload for math tests.")
        except KeyError:
            logger.warning("'app' module not in sys.modules, cannot reload.") # Should not happen if imported
            
        if not run_tests('test_math_*.py'):
            success = False
            
        # Clear math module again before weather tests, just to be safe
        clear_math_module() 
        
        if not run_tests('test_weather_*.py'):
            success = False
        return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main()) 