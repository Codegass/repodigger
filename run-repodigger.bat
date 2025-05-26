@echo off
REM Script to easily run RepoDigger using uvx on Windows

REM Check if GITHUB_TOKEN is set
IF NOT DEFINED GITHUB_TOKEN (
    echo Error: GITHUB_TOKEN environment variable is not set.
    echo Please set it before running this script, e.g., in PowerShell:
    echo $env:GITHUB_TOKEN = "your_github_pat_here"
    echo or in Command Prompt (for the current session only):
    echo set GITHUB_TOKEN="your_github_pat_here"
    exit /b 1
)

REM Get user input for organization
set /p ORG_NAME="Enter GitHub Organization name (e.g., Netflix, apache): "

REM Get user input for download folder
set /p DOWNLOAD_FOLDER="Enter path for the download folder (e.g., .\downloaded_data): "

REM Set default minimum stars
set MIN_STARS=200

echo.
echo Running RepoDigger with the following settings:
echo Organization: %ORG_NAME%
echo Download Folder: %DOWNLOAD_FOLDER%
echo Minimum Stars: %MIN_STARS%
echo (To export git logs, run the command manually with --export-git-log)
echo.

REM Construct and run the command
REM Ensure you are in the project root directory where pyproject.toml is located when running this script,
REM or adjust the path to "." for uvx accordingly if this script is placed elsewhere.

REM Assuming this script is in the project root:
uvx . -- --organization "%ORG_NAME%" --download-folder "%DOWNLOAD_FOLDER%" --min-stars %MIN_STARS%

echo.
echo RepoDigger run finished. 