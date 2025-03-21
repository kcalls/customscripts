#!/bin/bash

RANCHER_URL="https://your-rancher-url.com"
USERNAME="your-username"
PASSWORD="your-password"
CLUSTER_NAME="your-cluster-name"

# Get Rancher token
RANCHER_TOKEN=$(curl -s "$RANCHER_URL/v3-public/localProviders/local?action=login" \
  -H 'content-type: application/json' \
  --data-raw "{\"username\":\"$USERNAME\",\"password\":\"$PASSWORD\"}" \
  | jq -r .token)

# Get cluster ID
CLUSTER_ID=$(curl -s -k \
  -H "Authorization: Bearer $RANCHER_TOKEN" \
  "$RANCHER_URL/v3/clusters?name=$CLUSTER_NAME" \
  | jq -r '.data[0].id')

# Generate and save kubeconfig
curl -s -k -X POST \
  -H "Authorization: Bearer $RANCHER_TOKEN" \
  "$RANCHER_URL/v3/clusters/$CLUSTER_ID?action=generateKubeconfig" \
  | jq -r .config > "$CLUSTER_NAME.kubeconfig"

echo "Kubeconfig for $CLUSTER_NAME has been saved to $CLUSTER_NAME.kubeconfig"
