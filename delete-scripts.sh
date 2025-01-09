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

# Get the list of secrets older than the specified age
echo "Fetching secrets older than $AGE_THRESHOLD days..."
kubectl get secrets -n "$NAMESPACE" --sort-by='.metadata.creationTimestamp' -o custom-columns='NAME:.metadata.name,CREATION:.metadata.creationTimestamp' | \
awk -v threshold="$THRESHOLD_DATE" 'NR>1 {if ($2 < threshold) print $1}' > secrets-list.txt

# Split the list of secrets into batches
split -l $BATCH_SIZE secrets-list.txt secret_chunk_

# Delete secrets in batches with retries
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
done

# Cleanup temporary files
rm -f secrets-list.txt secret_chunk_*

echo "Cleanup completed."
