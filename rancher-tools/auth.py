import getpass
from typing import Dict
import requests
from datetime import datetime, timedelta
from .logging_utils import logger
from .config import RANCHER_ENVIRONMENTS

class RancherAuth:
    def __init__(self, environment: str):
        self.environment = environment.lower()
        self.base_url = self._get_environment_url()
        self.session_token = None
        self.token_expiry = None
        
    def _get_environment_url(self) -> str:
        """Validate and return environment URL"""
        if self.environment not in RANCHER_ENVIRONMENTS:
            logger.error(f"Invalid environment: {self.environment}")
            raise ValueError(f"Unknown environment. Available: {list(RANCHER_ENVIRONMENTS.keys())}")
        return RANCHER_ENVIRONMENTS[self.environment]['url']
    
    def _get_credentials(self) -> Dict[str, str]:
        """Securely prompt for credentials without logging"""
        username = input("Enter Rancher username: ")
        password = getpass.getpass("Enter Rancher password: ")
        return {'username': username, 'password': password}
    
    def _make_request(self, endpoint: str, method: str = 'POST', data: Dict = None):
        """Generic request handler"""
        url = f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if self.session_token:
            headers['Authorization'] = f'Bearer {self.session_token}'
            
        try:
            response = requests.request(
                method=method,
                url=url,
                json=data,
                headers=headers,
                verify=True
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            raise
            
    def generate_token(self, ttl_seconds: int = 3600) -> Dict:
        """Generate short-lived API token"""
        try:
            # Get credentials interactively
            creds = self._get_credentials()
            
            # First authenticate
            login_data = {
                **creds,
                'ttl': 300  # Short session TTL
            }
            
            logger.info(f"Authenticating to {self.environment} environment")
            login_resp = self._make_request(
                '/v3-public/localProviders/local?action=login',
                data=login_data
            )
            
            self.session_token = login_resp['token']
            
            # Then create API token
            token_data = {
                'type': 'token',
                'description': f"Automated token for {self.environment}",
                'ttl': ttl_seconds
            }
            
            logger.info("Generating API token")
            api_token = self._make_request(
                '/v3/tokens',
                data=token_data
            )
            
            return {
                'token': api_token['tokenId'],
                'expires_at': api_token['expiresAt'],
                'environment': self.environment
            }
            
        finally:
            if self.session_token:
                self._make_request('/v3/tokens?action=logout', method='POST')
                self.session_token = None

# Example standalone usage
if __name__ == "__main__":
    import sys
    from pprint import pprint
    
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <environment>")
        print(f"Available environments: {list(RANCHER_ENVIRONMENTS.keys())}")
        sys.exit(1)
        
    try:
        auth = RancherAuth(sys.argv[1])
        token_info = auth.generate_token()
        print("\nGenerated Token Info:")
        pprint(token_info)
        
    except Exception as e:
        logger.error(f"Token generation failed: {str(e)}")
        sys.exit(1)
