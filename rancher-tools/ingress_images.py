import sys
from tabulate import tabulate
from .auth import RancherAuth
from .logging_utils import logger

class IngressImageLister:
    def __init__(self, api_token, rancher_url):
        self.api_token = api_token
        self.rancher_url = rancher_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_token}',
            'Accept': 'application/json'
        })

    def _get_clusters(self):
        """Fetch all clusters with their state"""
        try:
            response = self.session.get(f'{self.rancher_url}/v3/clusters')
            response.raise_for_status()
            return [
                {
                    'name': cluster['name'],
                    'id': cluster['id'],
                    'state': cluster['state']
                } 
                for cluster in response.json()['data']
            ]
        except Exception as e:
            logger.error(f"Cluster fetch failed: {str(e)}")
            raise

    def _get_ingress_images(self, cluster_id):
        """Extract images from ingress-nginx pods"""
        try:
            url = f'{self.rancher_url}/k8s/clusters/{cluster_id}/api/v1/namespaces/ingress-nginx/pods'
            response = self.session.get(url, params={
                'labelSelector': 'app.kubernetes.io/name=ingress-nginx'
            })
            response.raise_for_status()
            
            images = []
            for pod in response.json().get('items', []):
                for container in pod['spec']['containers']:
                    images.append({
                        'pod': pod['metadata']['name'],
                        'container': container['name'],
                        'image': container['image'],
                        'namespace': pod['metadata']['namespace']
                    })
            return images
        except Exception as e:
            logger.warning(f"Ingress check failed for cluster {cluster_id}: {str(e)}")
            return []

    def generate_report(self, output_format='grid'):
        """Generate formatted table report"""
        results = []
        clusters = self._get_clusters()
        
        for cluster in clusters:
            images = self._get_ingress_images(cluster['id'])
            for img in images:
                results.append([
                    cluster['name'],
                    cluster['state'],
                    img['namespace'],
                    img['pod'],
                    img['container'],
                    img['image']
                ])
        
        headers = ["Cluster", "State", "Namespace", "Pod", "Container", "Image"]
        return tabulate(
            results, 
            headers=headers,
            tablefmt=output_format,
            colalign=("left", "center", "left", "left", "left", "left")
        )

def main():
    try:
        # Initialize with interactive auth
        auth = RancherAuth('prod')
        token = auth.generate_token()
        
        # Create lister and generate report
        lister = IngressImageLister(
            api_token=token['token'],
            rancher_url=RANCHER_ENVIRONMENTS['prod']['url']
        )
        
        print("\nIngress Controller Images Report:")
        print(lister.generate_report(output_format='fancy_grid'))
        
    except Exception as e:
        logger.critical(f"Report generation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
