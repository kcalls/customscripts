import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from tabulate import tabulate

private_token = '<your_pat>'
group_id = '<your_group_id>'

headers = {"PRIVATE-TOKEN": private_token}
base_url = "https://gitlab.com/api/v4"

def get_projects(group_id):
    url = f"{base_url}/groups/{group_id}/projects?per_page=100"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def get_latest_release(project_id):
    url = f"{base_url}/projects/{project_id}/releases"
    response = requests.get(url, headers=headers)
    if response.ok:
        releases = response.json()
        if releases:
            release = releases[0]
            return release['tag_name'], release.get('released_at', 'N/A')
    return None, None

def main():
    projects = get_projects(group_id)
    project_ids = {project['id']: project['name'] for project in projects}

    latest_releases = []

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(get_latest_release, pid): pid for pid in project_ids}

        for future in as_completed(futures):
            pid = futures[future]
            try:
                tag, released_at = future.result()
                latest_releases.append([project_ids[pid], pid, tag or "No releases", released_at or "N/A"])
            except Exception as e:
                latest_releases.append([project_ids[pid], pid, "Error", "N/A"])
                print(f"Error fetching release for project {project_ids[pid]}: {e}")

    # Print the results in table format
    headers = ["Project Name", "Project ID", "Latest Release", "Released At"]
    print(tabulate(latest_releases, headers=headers, tablefmt="grid"))

if __name__ == "__main__":
    main()
