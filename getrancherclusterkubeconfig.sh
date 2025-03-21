#!/bin/bash

# Define Rancher URLs based on environment
declare -A RANCHER_URLS
RANCHER_URLS["dev"]="https://rancher-dev.example.com"
RANCHER_URLS["staging"]="https://rancher-staging.example.com"
RANCHER_URLS["prod"]="https://rancher-prod.example.com"
RANCHER_URLS["pci"]="https://rancher-pci.example.com"

# Input: Specify the environment and cluster name
ENVIRONMENT=$1
CLUSTER_NAME=$2

if [[ -z "$ENVIRONMENT" || -z "$CLUSTER_NAME" ]]; then
  echo "Usage: $0 <environment> <cluster-name>"
  echo "Available environments: ${!RANCHER_URLS[@]}"
  exit 1
fi

# Get the Rancher URL for the specified environment
RANCHER_URL=${RANCHER_URLS[$ENVIRONMENT]}

if [[ -z "$RANCHER_URL" ]]; then
  echo "Invalid environment specified. Available environments: ${!RANCHER_URLS[@]}"
  exit 1
fi

# Rancher credentials (replace with your actual username and password)
USERNAME="your-username"
PASSWORD="your-password"

# Get Rancher token
RANCHER_TOKEN=$(curl -s "$RANCHER_URL/v3-public/localProviders/local?action=login" \
  -H 'content-type: application/json' \
  --data-raw "{\"username\":\"$USERNAME\",\"password\":\"$PASSWORD\"}" \
  | jq -r .token)

if [[ -z "$RANCHER_TOKEN" ]]; then
  echo "Failed to authenticate to Rancher at $RANCHER_URL"
  exit 1
fi

# Get cluster ID
CLUSTER_ID=$(curl -s -k \
  -H "Authorization: Bearer $RANCHER_TOKEN" \
  "$RANCHER_URL/v3/clusters?name=$CLUSTER_NAME" \
  | jq -r '.data[0].id')

if [[ -z "$CLUSTER_ID" ]]; then
  echo "Cluster $CLUSTER_NAME not found in environment $ENVIRONMENT"
  exit 1
fi

# Generate and save kubeconfig
KUBECONFIG_FILE="${CLUSTER_NAME}-${ENVIRONMENT}.kubeconfig"
curl -s -k -X POST \
  -H "Authorization: Bearer $RANCHER_TOKEN" \
  "$RANCHER_URL/v3/clusters/$CLUSTER_ID?action=generateKubeconfig" \
  | jq -r .config > "$KUBECONFIG_FILE"

if [[ $? -eq 0 ]]; then
  echo "Kubeconfig for cluster $CLUSTER_NAME in environment $ENVIRONMENT has been saved to $KUBECONFIG_FILE"
else
  echo "Failed to generate kubeconfig for cluster $CLUSTER_NAME in environment $ENVIRONMENT"
fi
