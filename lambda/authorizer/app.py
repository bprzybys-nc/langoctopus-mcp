import os
import json
import logging

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Lambda authorizer for SAML authentication (placeholder).
    Currently returns success in development mode.
    
    When SAML authentication is implemented, this function will validate
    SAML assertions from the request headers.
    """
    # For development with no auth as specified in requirements
    if os.environ.get('NOAUTH') == 'true':
        logger.info("NoAuth mode: Authorization bypassed")
        return {
            'isAuthorized': True,
            'context': {
                'user': 'development-user',
                'roles': 'development'
            }
        }
    
    # This would be implemented when SAML auth is needed
    logger.info("This is a placeholder for SAML authorization")
    return {
        'isAuthorized': True,
        'context': {
            'user': 'placeholder-user',
            'roles': 'placeholder-roles'
        }
    } 