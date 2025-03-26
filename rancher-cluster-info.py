import requests
import json
from tabulate import tabulate

# Configuration
RANCHER_ENVS = {
    "UAT": {
        "url": "https://rancher.uat.example.com/v3",
        "token": "token-xyz123"
    },
    "PROD": {
        "url": "https://rancher.prod.example.com/v3",
        "token": "token-abc456"
    }
}

# Read cluster names from file
def read_clusters(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file if line.strip()]

# Get cluster details from Rancher API
def get_cluster_details(cluster_name):
    for env, config in RANCHER_ENVS.items():
        headers = {"Authorization": f"Bearer {config['token']}"}
        
        # Search for cluster
        cluster_url = f"{config['url']}/clusters?name={cluster_name}"
        response = requests.get(cluster_url, headers=headers)
        
        if response.status_code == 200:
            clusters = response.json().get('data', [])
            if clusters:
                cluster_data = clusters[0]
                region = cluster_data.get('eksConfig', {}).get('region', 'N/A')
                
                # Get AWS account ID from cloud credential
                cred_id = cluster_data.get('eksConfig', {}).get('cloudCredentialId')
                aws_account = 'N/A'
                if cred_id:
                    cred_url = f"{config['url']}/cloudcredentials/{cred_id}"
                    cred_response = requests.get(cred_url, headers=headers)
                    if cred_response.status_code == 200:
                        aws_account = cred_response.json().get('annotations', {}).get('aws.accountId', 'N/A')
                
                return {
                    "cluster": cluster_name,
                    "environment": env,
                    "aws_account": aws_account,
                    "region": region
                }
    
    return {
        "cluster": cluster_name,
        "environment": "NOT FOUND",
        "aws_account": "N/A",
        "region": "N/A"
    }

# Main execution
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python rancher_cluster_info.py <clusters_file>")
        sys.exit(1)
    
    clusters_file = sys.argv[1]
    clusters = read_clusters(clusters_file)
    
    results = []
    for cluster in clusters:
        results.append(get_cluster_details(cluster))
    
    # Format output
    headers = ["Cluster", "Environment", "AWS Account", "Region"]
    table_data = [
        [r["cluster"], r["environment"], r["aws_account"], r["region"]] 
        for r in results
    ]
    
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
