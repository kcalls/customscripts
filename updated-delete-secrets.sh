#!/bin/bash

# Configuration Parameters
NAMESPACE="cattle-impersonation-system"
MAX_RETRIES=10
RETRY_DELAY=5
BATCH_SIZE=1000

# Input for age threshold
if [ -z "$1" ]; then
  echo "Usage: $0 <days>"
  exit 1
fi
AGE_THRESHOLD=$1

export NAMESPACE

# Calculate the threshold date in ISO 8601 format
THRESHOLD_DATE=$(date -d "$AGE_THRESHOLD days ago" --utc +%Y-%m-%dT%H:%M:%SZ)

# Function to fetch secrets older than the threshold in chunks
fetch_secrets_batch() {
  local continue_token=$1
  kubectl get secrets -n "$NAMESPACE" --sort-by='.metadata.creationTimestamp' \
    -o custom-columns='NAME:.metadata.name,CREATION:.metadata.creationTimestamp' \
    ${continue_token:+--continue=$continue_token} | awk -v threshold="$THRESHOLD_DATE" 'NR>1 {if ($2 < threshold) print $1}'
}

# Fetch and delete secrets incrementally
continue_token=""
while :; do
  echo "Fetching a batch of up to $BATCH_SIZE secrets older than $AGE_THRESHOLD days..."
  secrets=$(fetch_secrets_batch "$continue_token")
  
  # If no secrets are returned, exit the loop
  if [ -z "$secrets" ]; then
    echo "No more secrets to process."
    break
  fi

  # Save secrets to temporary file and split into smaller chunks
  echo "$secrets" > secrets-list.txt
  split -l $BATCH_SIZE secrets-list.txt secret_chunk_

  # Process each batch of secrets
  for file in secret_chunk_*; do
    attempt=0
    echo "Processing batch: $file"
    while [ $attempt -lt $MAX_RETRIES ]; do
      while read -r secret; do
        kubectl delete secret "$secret" -n "$NAMESPACE" --ignore-not-found || true
      done < "$file"
      break
      attempt=$((attempt + 1))
      echo "Retrying batch $file (Attempt: $attempt)..."
      sleep $RETRY_DELAY
    done
    if [ $attempt -eq $MAX_RETRIES ]; then
      echo "Failed to delete secrets in batch $file after $MAX_RETRIES attempts."
    fi
    rm -f "$file"  # Cleanup processed batch file
  done

  # Cleanup temporary files
  rm -f secrets-list.txt secret_chunk_*

  # Check for continuation token
  continue_token=$(kubectl get secrets -n "$NAMESPACE" --sort-by='.metadata.creationTimestamp' \
    -o jsonpath='{.metadata.continue}' ${continue_token:+--continue=$continue_token})
  if [ -z "$continue_token" ]; then
    break
  fi
done

echo "Cleanup completed."
