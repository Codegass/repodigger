<div align="center">

# RepoDigger

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Project Status: Maintained](https://img.shields.io/badge/status-maintained-brightgreen.svg)](https://github.com/codegass/repodigger/) 
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

<img src="./image.png" alt="RepoDigger Icon" width="33%"/>

</div>

RepoDigger is a Python command-line tool designed to selectively download and optionally analyze repositories from specified GitHub organizations. It allows users to filter repositories based on criteria such as minimum star count, primary programming language (default is Java), archive status, and build system (Maven or Gradle, excluding Ant and Bazel).

## Quick Start: Install and Run `rd` Globally (Recommended)

This project is designed to be installed as a command-line tool using `uv`.

1.  **Install `uv`**:
    If you haven't already, install `uv` by following the [official instructions](https://github.com/astral-sh/uv#installation).

2.  **Set up GitHub Token**:
    RepoDigger requires a GitHub Personal Access Token.
    
> [!IMPORTANT]
> For the global `rd` command to work, you **MUST** set the `GITHUB_TOKEN` environment variable.
>
> **macOS / Linux** (bash/zsh - add to your `.bashrc` or `.zshrc` for persistence):
> ```bash
> export GITHUB_TOKEN="your_github_pat_here"
> ```
> **Windows (PowerShell)** (to set permanently, search for "environment variables" in system settings):
>
> ```powershell
> $env:GITHUB_TOKEN = "your_github_pat_here"
> ```



For local development or running the script directly (e.g., `python repodigger.py` or `uvx . --`), if the `GITHUB_TOKEN` environment variable is not set, the script will alternatively look for a `SECRET.py` file in the project root. This file should contain `GITHUB_TOKEN = "your_github_pat_here"` and is gitignored.

3.  **Install `rd` (RepoDigger command)**:
    Navigate to the project's root directory (where `pyproject.toml` is located) and run:
    ```bash
    uv tool install .
    ```
    
> [!TIP]
> This command installs `rd` and its dependencies into an isolated environment managed by `uv`. It also adds `rd` to a directory that should be part of your system's PATH (usually `~/.uv/bin` or similar). If the `rd` command is not found after installation, ensure this directory is in your PATH or run `uv tool update-shell` and restart your terminal.

4.  **Run `rd` from anywhere**:
    Once installed, you can run RepoDigger using the `rd` command from any directory in your terminal. The following command downloads repositories from the specified organization with at least 200 stars (default) into the specified download folder.

    **Replace `<ORG_NAME>` and `<PATH_TO_DOWNLOAD_FOLDER>`:**
    ```bash
    rd --organization <ORG_NAME> --download-folder <PATH_TO_DOWNLOAD_FOLDER> --min-stars 200 --language Java
    ```
    <details>
        <summary>Examples:</summary>
        
    ```bash
    rd --organization Netflix --download-folder ./netflix_data # Defaults to Java, 200 stars
    rd --organization google --download-folder ./google_python_data --language Python
    rd --organization Netflix --download-folder ./netflix_data_no_build_check --language Java --disable-build-system-check
    rd --organization <ORG_NAME> --download-folder <PATH_TO_DOWNLOAD_FOLDER> --export-git-log # For Java logs
    ```
    
    </details>
      
-----

### One-Click Run Scripts (Experimental - for local execution)

<details>
<summary>If you want to quick running without `uvx`:</summary>    

If you have the project code locally (e.g., cloned) but haven't installed `rd` globally, these scripts offer a convenient way to run the local version using `uvx`. Ensure your `GITHUB_TOKEN` environment variable is set.

*   These scripts prompt for the organization and download folder, and use default settings (200 stars, Java language).
*   **macOS/Linux**: `cd path/to/project && ./run-repodigger.sh`
      You might need to make the script executable first: `chmod +x run-repodigger.sh`
*   **Windows**: `cd path\to\project && run-repodigger.bat`.
</details>

### Alternative: Running Local Version with `uvx` (for development/testing)
<details>
    
<summary>If you are in the project's root directory and want to run the local code without installing it globally:</summary>

1.  Ensure `uv` is installed and `GITHUB_TOKEN` is set (see Quick Start steps 1 & 2).
2.  Run using `uvx . --` followed by the script arguments:
    
    > [!TIP]
    > `uvx . --` executes the local project from the current directory. The one-click scripts above use this method.

    ```bash
    uvx . -- --organization <ORG_NAME> --download-folder <PATH_TO_DOWNLOAD_FOLDER> [OPTIONS]
    ```
    Example:
    ```bash
    uvx . -- --organization Netflix --download-folder ./dev_test_netflix --min-stars 100
    ```
</details>

### For Development (Setting up a local virtual environment)
<details>
<summary>If you plan to modify the RepoDigger code itself:</summary>

    Follow these steps to set up a dedicated development environment:
    1. Ensure `uv` is installed.
    2. Set up GitHub Token (environment variableตำรวจ `GITHUB_TOKEN` or a local `SECRET.py` file, see Quick Start step 2).
    3. Clone the repository and navigate to the project directory.
    4. Create and activate a virtual environment:
        ```bash
        uv venv
        source .venv/bin/activate  # macOS/Linux
        # .venv\Scripts\activate.bat  # Windows CMD
        # .venv\Scripts\Activate.ps1 # Windows PowerShell
        ```
     5. Install the project in editable mode with its dependencies:
        ```bash
        uv pip install -e .
        ```
     6. Now you can run the script directly:
        ```bash
        python repodigger.py --organization <ORG_NAME> --download-folder <PATH_TO_DOWNLOAD_FOLDER> [OPTIONS]
        ```
</details>

-----

## Features

-   **Targeted Repository Downloading**: Downloads repositories from a specific GitHub organization.
-   **Flexible Filtering**:
    -   Filters for public, non-archived projects (defaults to Java via `--language` flag).
    -   Filters by a minimum number (or greater/equal) of GitHub stars.
    -   Optional Build System Check (for Java projects by default, can be disabled with `--disable-build-system-check`; automatically disabled for non-Java languages): Filters by projects managed with Maven or Gradle, automatically excluding those managed by Ant or Bazel. 
    -   Filters for projects updated within the last three years.
-   **Custom Download Location**: Allows users to specify a directory where repositories and associated files will be saved.
-   **Optional Git Log Analysis**: (If `--export-git-log` is used, most relevant for Java projects)
    -   Exports the git log for each downloaded repository into a CSV file.
    -   Filters these logs to identify commits related to test files (`src/test/.*Test.*\.java`).
    -   Merges individual test commit logs into a single comprehensive CSV file.
    -   Provides basic statistics, such as the number of unique authors for test commits per project.
-   **Detailed Logging**: Maintains a log file (`repodigger.log`) capturing the script's operations, warnings, and errors.

## Command-Line Arguments

-   `--organization <ORG_NAME>`: (Required) Specifies the GitHub organization.
-   `--download-folder <PATH_TO_DOWNLOAD_FOLDER>`: (Required) Base directory for downloads.
-   `--min-stars <NUMBER>`: Minimum stars (>=). Default: `200`.
-   `--language <LANGUAGE>`: Programming language. Default: `Java`.

    > [!TIP]
    > While you can specify other languages (e.g., Python), the build system check and git log analysis for test commits are primarily tailored for Java projects and will be less effective or automatically disabled for other languages.

-   `--disable-build-system-check`: Disable build system check (active by default for Java, always off for others).

    > [!TIP]
    > This flag allows you to download Java projects without filtering them by Maven/Gradle vs. Ant/Bazel. For non-Java languages, the build system check is always disabled regardless of this flag.

-   `--export-git-log`: Optional: Export git logs (most relevant for Java).

### Examples (using the global `rd` command):

1.  **Download from Netflix, default settings (Java, 200+ stars):**
    ```bash
    rd --organization Netflix --download-folder ./netflix_repos
    ```

2.  **Download Python projects from Google, 500+ stars, export logs (though log export is less relevant for Python):**
    ```bash
    rd --organization google --download-folder /data/google_python_projects --min-stars 500 --language Python --export-git-log
    ```

## Output Structure

All downloaded data and logs are organized within the specified download folder, under a subdirectory named after the organization:

```
<download_folder>/
|-- <ORG_NAME>-projects/
|   |-- repodigger.log                # Main log file for the script's operations.
|   |-- failed_or_skipped_projects.txt # Lists projects that failed to clone or were skipped.
|   |-- <repo_name_1>/                # Cloned repository 1
|   |-- <repo_name_2>/                # Cloned repository 2
|   |-- ...
|   |-- git_log/                      # (Only if --export-git-log is used)
|   |   |-- <repo_name_1>_git_log.csv
|   |   |-- <repo_name_2>_git_log.csv
|   |   |-- ...
|   |   |-- c4t/                      # Commits for Test analysis
|   |   |   |-- <repo_name_1>_test_commit_log.csv
|   |   |   |-- ...
|   |   |   |-- all_test_commit_log.csv
|   |   |   |-- no_test_commit_repos.txt # Repos with no identified test-related commits.
```

## How Build System Detection Works

> [!IMPORTANT]
> RepoDigger's build system detection (Maven/Gradle vs. Ant/Bazel) is primarily designed for **Java projects**.
>
> *   It is **enabled by default** for Java projects.
> *   It is **always disabled** for non-Java languages.

-   **For Java projects (if not disabled by `--disable-build-system-check`):**
    1.  After a repository is cloned, the script traverses its entire directory structure (ignoring `.git`).
    2.  It looks for: Maven (`pom.xml`), Gradle (`build.gradle`, `build.gradle.kts`), Ant (`build.xml`), Bazel (`WORKSPACE`, `BUILD`, `BUILD.bazel`).
    3.  A repository qualifies if it contains Maven/Gradle build files AND NOT Ant/Bazel files.
    4.  Non-qualifying Java repositories are logged and their cloned directory is removed.
-   **For non-Java projects, or if `--disable-build-system-check` is used for Java projects:**
    -   The build system check is skipped. All cloned repositories that meet other criteria are kept.

## Logging

> [!TIP]
> Detailed logs are saved to `<download_folder>/<ORG_NAME>-projects/repodigger.log`.
> Check this file for script progress, warnings, errors, and details about excluded repositories.

---

Feel free to suggest improvements or report issues! 
