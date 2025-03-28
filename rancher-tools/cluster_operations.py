# cluster_operations.py
from rancher_tools.auth import RancherAuth
from rancher_tools.logging_utils import logger

def fetch_cluster_images(api_token: str, environment: str):
    logger.info(f"Fetching images from {environment} clusters")
    # Implement your cluster operations here
    # Example:
    # 1. List all clusters
    # 2. For each cluster, get ingress controller pods
    # 3. Extract image names
    
if __name__ == "__main__":
    try:
        # Get token for test environment
        auth = RancherAuth('test')
        token_info = auth.generate_token(ttl_seconds=1800)  # 30 min token
        
        # Use the token for operations
        fetch_cluster_images(token_info['token'], token_info['environment'])
        
    except Exception as e:
        logger.error(f"Operation failed: {str(e)}")
        raise
