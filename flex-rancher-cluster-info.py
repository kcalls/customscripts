import requests
import re
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

# Region mapping (shortcode -> full)
REGION_MAP = {
    'euw1': 'eu-west-1',
    'use1': 'us-east-1',
    'aps1': 'ap-southeast-1',
    # Add more mappings as needed
}

def parse_cluster_name(cluster_name):
    """Extract appname, env, and region from cluster name format:
    eks-<appname>-<env>-<region_shortcut>-<identifier>"""
    match = re.match(r'^eks-(.+?)-(\w+)-(\w+)-\w+$', cluster_name)
    if not match:
        return None, None, None
    return match.group(1), match.group(2), match.group(3)  # appname, env, region_short

def read_clusters(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file if line.strip()]

def get_aws_account_id(rancher_url, token, cluster_id):
    """Get AWS account ID from cluster description annotations"""
    url = f"{rancher_url}/clusters/{cluster_id}"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get('annotations', {}).get('aws.accountId', 'N/A')
    return 'N/A'

def get_cluster_details(cluster_name):
    appname, env, region_short = parse_cluster_name(cluster_name)
    if not all([appname, env, region_short]):
        return {
            "cluster": cluster_name,
            "environment": "INVALID_NAME",
            "aws_account": "N/A",
            "region": "N/A"
        }

    full_region = REGION_MAP.get(region_short.lower(), f"unknown({region_short})")
    
    for rancher_env, config in RANCHER_ENVS.items():
        headers = {"Authorization": f"Bearer {config['token']}"}
        search_url = f"{config['url']}/clusters?name={cluster_name}"
        response = requests.get(search_url, headers=headers)
        
        if response.status_code == 200:
            clusters = response.json().get('data', [])
            if clusters:
                cluster_id = clusters[0]['id']
                aws_account = get_aws_account_id(config['url'], config['token'], cluster_id)
                
                return {
                    "cluster": cluster_name,
                    "environment": env.upper(),
                    "aws_account": aws_account,
                    "region": full_region,
                    "appname": appname
                }
    
    return {
        "cluster": cluster_name,
        "environment": env.upper(),
        "aws_account": "N/A",
        "region": full_region,
        "appname": appname
    }

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python rancher_cluster_info.py <clusters_file>")
        sys.exit(1)
    
    clusters = read_clusters(sys.argv[1])
    results = []
    
    for cluster in clusters:
        results.append(get_cluster_details(cluster))
    
    # Format output
    headers = ["Cluster", "App", "Environment", "AWS Account", "Region"]
    table_data = [
        [r["cluster"], r["appname"], r["environment"], r["aws_account"], r["region"]] 
        for r in results
    ]
    
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    print("\nRegion Shortcuts:", json.dumps(REGION_MAP, indent=2))
