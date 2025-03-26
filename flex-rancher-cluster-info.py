import requests
import re
from tabulate import tabulate
import json

# Complete AWS region mapping based on search results
REGION_MAP = {
    # Standard AWS region abbreviations
    'use1': 'us-east-1',        # US East (N. Virginia)
    'use2': 'us-east-2',        # US East (Ohio)
    'usw1': 'us-west-1',        # US West (N. California)
    'usw2': 'us-west-2',        # US West (Oregon)
    'cac1': 'ca-central-1',     # Canada (Central)
    'euw1': 'eu-west-1',        # EU (Ireland)
    'euw2': 'eu-west-2',        # EU (London)
    'euw3': 'eu-west-3',        # EU (Paris)
    'euc1': 'eu-central-1',     # EU (Frankfurt)
    'eun1': 'eu-north-1',       # EU (Stockholm)
    'aps1': 'ap-southeast-1',   # Asia Pacific (Singapore)
    'aps2': 'ap-southeast-2',   # Asia Pacific (Sydney)
    'aps3': 'ap-southeast-3',   # Asia Pacific (Jakarta)
    'apn1': 'ap-northeast-1',   # Asia Pacific (Tokyo)
    'apn2': 'ap-northeast-2',   # Asia Pacific (Seoul)
    'apn3': 'ap-northeast-3',   # Asia Pacific (Osaka)
    'aps0': 'ap-south-1',       # Asia Pacific (Mumbai)
    'aps4': 'ap-south-2',       # Asia Pacific (Hyderabad)
    'sae1': 'sa-east-1',        # South America (São Paulo)
    'mes1': 'me-south-1',       # Middle East (Bahrain)
    'mec1': 'me-central-1',     # Middle East (UAE)
    'afs1': 'af-south-1',       # Africa (Cape Town)
    'ilc1': 'il-central-1',     # Israel (Tel Aviv)
    
    # CloudPosse-style abbreviations (from search results)
    'as0': 'ap-south-1',        # Alternative for ap-south-1
    'nn0': 'cn-north-1',        # China (Beijing)
    'nn1': 'cn-northwest-1',    # China (Ningxia)
}

# Rancher configuration
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

def parse_cluster_name(cluster_name):
    """Enhanced parser for EKS cluster names following pattern:
    eks-<appname>-<env>-<region_short>-<identifier>"""
    pattern = r'^eks-(?P<app>[a-z0-9]+)-(?P<env>[a-z]{2,4})-(?P<region>[a-z]{3,4}\d?)-\w+$'
    match = re.match(pattern, cluster_name, re.IGNORECASE)
    if not match:
        return None, None, None
    return match.group('app'), match.group('env'), match.group('region')

def get_aws_account_from_description(rancher_url, token, cluster_id):
    """Extract AWS account from cluster description annotations"""
    url = f"{rancher_url}/clusters/{cluster_id}"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json().get('annotations', {}).get('aws.accountId', 'N/A')
    except (requests.RequestException, json.JSONDecodeError):
        return 'N/A'

def get_cluster_details(cluster_name):
    app, env, region_short = parse_cluster_name(cluster_name)
    if not all([app, env, region_short]):
        return {
            "cluster": cluster_name,
            "app": "INVALID_NAME",
            "environment": "INVALID_NAME",
            "aws_account": "N/A",
            "region": "N/A",
            "region_short": "N/A"
        }

    # Normalize region code (case-insensitive)
    region_code = region_short.lower()
    full_region = REGION_MAP.get(region_code, f"unknown({region_short})")
    
    # Search in all Rancher environments
    for rancher_env, config in RANCHER_ENVS.items():
        try:
            search_url = f"{config['url']}/clusters?name={cluster_name}"
            headers = {"Authorization": f"Bearer {config['token']}"}
            response = requests.get(search_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            clusters = response.json().get('data', [])
            if clusters:
                aws_account = get_aws_account_from_description(
                    config['url'], 
                    config['token'], 
                    clusters[0]['id']
                )
                
                return {
                    "cluster": cluster_name,
                    "app": app,
                    "environment": env.upper(),
                    "aws_account": aws_account,
                    "region": full_region,
                    "region_short": region_short.upper()
                }
                
        except (requests.RequestException, json.JSONDecodeError):
            continue
    
    return {
        "cluster": cluster_name,
        "app": app,
        "environment": env.upper(),
        "aws_account": "N/A",
        "region": full_region,
        "region_short": region_short.upper()
    }

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python eks_cluster_info.py <clusters_file>")
        sys.exit(1)
    
    with open(sys.argv[1], 'r') as f:
        clusters = [line.strip() for line in f if line.strip()]
    
    results = [get_cluster_details(cluster) for cluster in clusters]
    
    # Format output
    headers = ["Cluster", "App", "Environment", "AWS Account", "Region", "Region Code"]
    table_data = [
        [r["cluster"], r["app"], r["environment"], r["aws_account"], r["region"], r["region_short"]]
        for r in results
    ]
    
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    print("\nFull region mapping:")
    print(json.dumps(
        {v: k for k, v in REGION_MAP.items()}, 
        indent=2, 
        sort_keys=True
    ))
