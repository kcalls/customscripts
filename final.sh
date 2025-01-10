#!/bin/bash

# Configuration Parameters
NAMESPACE="cattle-impersonation-system"
MAX_RETRIES=10
RETRY_DELAY=5
BATCH_SIZE=500

# Input for age threshold
if [ -z "$1" ]; then
  echo "Usage: $0 <days>"
  exit 1
fi
AGE_THRESHOLD=$1

# Calculate the threshold date in ISO 8601 format
THRESHOLD_DATE=$(date -d "$AGE_THRESHOLD days ago" --utc +%Y-%m-%dT%H:%M:%SZ)

# Function to fetch secrets with pagination
fetch_secrets() {
  local continue_token=$1
  kubectl get secrets -n "$NAMESPACE" --chunk-size=$BATCH_SIZE ${continue_token:+--continue=$continue_token} \
    -o custom-columns='NAME:.metadata.name,CREATION:.metadata.creationTimestamp'
}

# Function to process and delete secrets
process_secrets() {
  local secrets_file=$1
  awk -v threshold="$THRESHOLD_DATE" 'NR>1 {if ($2 < threshold) print $1}' "$secrets_file" | while read -r secret; do
    echo "Deleting secret: $secret"
    kubectl delete secret "$secret" -n "$NAMESPACE" --ignore-not-found
    sleep 1  # Adding a short delay to avoid overwhelming the API server
  done
}

# Main loop to fetch and process secrets with pagination
continue_token=""
while :; do
  echo "Fetching secrets with continue token: $continue_token"
  secrets_file=$(mktemp)
  fetch_secrets "$continue_token" > "$secrets_file"

  # Check if the file contains data
  if [ ! -s "$secrets_file" ]; then
    echo "No more secrets to fetch."
    rm -f "$secrets_file"
    break
  fi

  process_secrets "$secrets_file"

  # Check for a continuation token in the output
  continue_token=$(kubectl get secrets -n "$NAMESPACE" --chunk-size=$BATCH_SIZE \
    --sort-by='.metadata.creationTimestamp' --output=jsonpath='{.metadata.continue}' 2>/dev/null)

  if [ -z "$continue_token" ]; then
    echo "No more secrets to process."
    rm -f "$secrets_file"
    break
  fi

  rm -f "$secrets_file"
done

echo "Secret deletion process completed."
