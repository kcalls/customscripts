#!/bin/bash

# Variables - replace these with your values
GITLAB_URL="https://gitlab.com"                 # GitLab base URL (adjust if self-hosted)
PRIVATE_TOKEN="YOUR_PRIVATE_ACCESS_TOKEN"       # Your GitLab API token
GROUP_ID="your-group-id"                         # ID or URL-encoded path of the group

# Print table header
printf "%-30s %-25s %-25s\n" "Project Name" "Latest Release Tag" "Released At"
printf "%-30s %-25s %-25s\n" "------------" "------------------" "-----------"

# Get all projects in the group
projects=$(curl -s --header "PRIVATE-TOKEN: $PRIVATE_TOKEN" \
  "$GITLAB_URL/api/v4/groups/$GROUP_ID/projects?per_page=100")

# Iterate over each project to get latest release
echo "$projects" | jq -c '.[] | {id: .id, name: .name}' | while read -r project; do
  project_id=$(echo "$project" | jq -r '.id')
  project_name=$(echo "$project" | jq -r '.name')

  # Get latest release using permalink/latest endpoint
  latest_release=$(curl -s --header "PRIVATE-TOKEN: $PRIVATE_TOKEN" \
    "$GITLAB_URL/api/v4/projects/$project_id/releases/permalink/latest")

  # Extract release data
  tag_name=$(echo "$latest_release" | jq -r '.tag_name // "No release"')
  released_at=$(echo "$latest_release" | jq -r '.released_at // "-"')

  # Print data in a table row
  printf "%-30s %-25s %-25s\n" "$project_name" "$tag_name" "$released_at"
done
