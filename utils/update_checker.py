import requests
import json
from packaging import version
from rich.console import Console
from rich.text import Text
from rich.align import Align
from rich.progress import Progress, SpinnerColumn, TextColumn # For potential use in UI

# Use console from helpers if needed, or create a local one
# from utils.helpers import console
console = Console(color_system="auto", highlight=False)

# --- Configuration ---
# TODO: Replace with your actual GitHub username and repository name
GITHUB_USERNAME = "nottherealtar"
GITHUB_REPONAME = "Tars-Mega-Tool"
# --- End Configuration ---

GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPONAME}/releases/latest"

def check_for_updates(current_v_str):
    """Check for updates to the application on GitHub."""
    update_info = {'update_available': False, 'current_version': current_v_str}

    try:
        response = requests.get(GITHUB_API_URL, headers={'User-Agent': 'Tars-Utilities-Tool-Update-Checker'}, timeout=5)
        if response.status_code == 200:
            data = response.json()
            latest_version = data.get('tag_name', '').lstrip('v')

            if latest_version and version.parse(latest_version) > version.parse(current_v_str):
                download_url = None
                # Find the asset with a name starting with 'TarsUtilitiesTool' and ending with '.exe'
                asset_name_expected_prefix = 'TarsUtilitiesTool'
                asset_name_expected_suffix = '.exe'
                for asset in data.get('assets', []):
                    asset_name = asset.get('name', '')
                    if asset_name.startswith(asset_name_expected_prefix) and asset_name.endswith(asset_name_expected_suffix):
                        download_url = asset.get('browser_download_url')
                        break
                for asset in data.get('assets', []):
                    if asset.get('name') == asset_name:
                        download_url = asset.get('browser_download_url')
                        break

                update_info.update({
                    'update_available': True,
                    'latest_version': latest_version,
                    'download_url': download_url,
                    'release_notes': data.get('body', 'No release notes provided.'),
                    'release_page_url': data.get('html_url') # URL to the release page
                })
        elif response.status_code == 404:
            # Repo or releases not found, treat as no update
            pass # Or log this specific case
        else:
            # Handle other HTTP errors if necessary
            update_info['error'] = f"HTTP Error {response.status_code}"

    except requests.exceptions.RequestException as e:
        # Handle network errors (DNS, connection refused, etc.)
        update_info['error'] = f"Network error: {str(e)}"
    except json.JSONDecodeError:
        update_info['error'] = "Error decoding update information"
    except Exception as e:
        # Catch any other unexpected errors
        update_info['error'] = f"Unexpected error: {str(e)}"

    return update_info

# Removed display_update_status - UI module handles display based on returned info
