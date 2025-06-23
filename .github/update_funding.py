# scripts/update_funding.py
from pathlib import Path
import requests
import sys

# Define the URL of your central FUNDING.md file on GitHub
FUNDING_REPO_URL = "https://raw.githubusercontent.com/pamagister/FUNDING/main/README.md"

# Define the destination path within the current repository
# This will create 'docs/funding/funding.md'
DST_THIS_REPO = Path("docs/funding/funding.md")


def update_funding_file():
    """
    Downloads the FUNDING.md file from the central repository
    and saves it to the specified path within the current repository.
    """
    print(f"Attempting to download FUNDING.md from: {FUNDING_REPO_URL}")

    try:
        # Send a GET request to the URL
        response = requests.get(FUNDING_REPO_URL)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)

        # Ensure the parent directory (e.g., 'docs/funding/') exists
        DST_THIS_REPO.parent.mkdir(parents=True, exist_ok=True)

        # Write the content to the destination file
        with open(DST_THIS_REPO, "wb") as f:
            f.write(response.content)

        print(f"Successfully updated FUNDING.md at: {DST_THIS_REPO}")

    except requests.exceptions.RequestException as e:
        print(f"Error downloading FUNDING.md: {e}", file=sys.stderr)
        sys.exit(1)  # Exit with an error code
    except IOError as e:
        print(f"Error writing FUNDING.md to file: {e}", file=sys.stderr)
        sys.exit(1)  # Exit with an error code


if __name__ == "__main__":
    # Ensure the 'requests' library is installed for this script to run.
    # If not, install it using: pip install requests
    update_funding_file()
