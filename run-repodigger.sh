#!/bin/bash

# Script to easily run RepoDigger using uvx

# Check if GITHUB_TOKEN is set
if [ -z "${GITHUB_TOKEN}" ]; then
    echo "Error: GITHUB_TOKEN environment variable is not set."
    echo "Please set it before running this script, e.g.:"
    echo "export GITHUB_TOKEN=\"your_github_pat_here\""
    exit 1
fi

# Get user input for organization
read -p "Enter GitHub Organization name (e.g., Netflix, apache): " ORG_NAME

# Get user input for download folder
read -p "Enter path for the download folder (e.g., ./downloaded_data): " DOWNLOAD_FOLDER

# Set default minimum stars
MIN_STARS=200

echo ""
echo "Running RepoDigger with the following settings:"
echo "Organization: ${ORG_NAME}"
echo "Download Folder: ${DOWNLOAD_FOLDER}"
echo "Minimum Stars: ${MIN_STARS}"
echo "(To export git logs, run the command manually with --export-git-log)"
echo ""

# Construct and run the command
# Ensure you are in the project root directory where pyproject.toml is located when running this script,
# or adjust the path to "." for uvx accordingly if this script is placed elsewhere.

# Assuming this script is in the project root:
uvx . -- --organization "${ORG_NAME}" --download-folder "${DOWNLOAD_FOLDER}" --min-stars ${MIN_STARS}

echo ""
echo "RepoDigger run finished." 