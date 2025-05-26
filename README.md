# RepoDigger

RepoDigger is a Python command-line tool designed to selectively download and optionally analyze Java repositories from specified GitHub organizations. It allows users to filter repositories based on criteria such as minimum star count, primary programming language (Java), archive status, and build system (Maven or Gradle, excluding Ant and Bazel).

## Quick Start with UV

This project is configured for use with `uv`, an extremely fast Python package and project manager.

1.  **Install `uv`**:
    If you don't have `uv` installed, follow the official instructions (e.g., `curl -LsSf https://astral.sh/uv/install.sh | sh` for macOS/Linux).

2.  **Set up GitHub Token**:
    RepoDigger requires a GitHub Personal Access Token.
    *   **Recommended**: Set an environment variable `GITHUB_TOKEN`:
        ```bash
        export GITHUB_TOKEN="your_actual_github_token_here"
        ```
    *   Alternatively, create a `SECRET.py` file in the project root with `GITHUB_TOKEN = "your_token"`.

3.  **Run with `uvx` (execute in a temporary environment)**:
    Navigate to the project's root directory (where `pyproject.toml` is located) and run:
    ```bash
    uvx . -- --organization <ORG_NAME> --download-folder <PATH> [OPTIONS]
    ```
    Example:
    ```bash
    uvx . -- --organization Netflix --min-stars 100 --download-folder ./netflix_data
    ```
    *(Note the `--` before script arguments when running local projects with `uvx`)*

4.  **Or, Install as a Tool with `uv tool install` (for global access)**:
    In the project root:
    ```bash
    uv tool install .
    ```
    This makes the `repodigger` command available globally (ensure `uv`'s tool bin directory is in your PATH). Then run:
    ```bash
    repodigger --organization <ORG_NAME> --download-folder <PATH> [OPTIONS]
    ```
    Example:
    ```bash
    repodigger --organization apache --min-stars 500 --download-folder ./apache_data --export-git-log
    ```

5.  **(For Development) Create a Local Virtual Environment**:
    If you plan to modify the code or work on it locally:
    ```bash
    cd path/to/repodigger_project
    uv venv  # Creates a .venv virtual environment
    source .venv/bin/activate  # Or relevant activation script for your shell
    uv pip install -e . # Installs the project in editable mode with its dependencies
    # Now you can run it directly
    python repodigger.py --organization <ORG_NAME> --download-folder <PATH> [OPTIONS]
    ```

## Features

-   **Targeted Repository Downloading**: Downloads repositories from a specific GitHub organization.
-   **Flexible Filtering**:
    -   Filters for public, non-archived Java projects.
    -   Filters by a minimum number (or greater/equal) of GitHub stars.
    -   Filters by projects managed with Maven or Gradle, automatically excluding those managed by Ant or Bazel. The tool inspects the entire repository structure to detect these build systems.
    -   Filters for projects updated within the last three years.
-   **Custom Download Location**: Allows users to specify a directory where repositories and associated files will be saved.
-   **Optional Git Log Analysis**: (If `--export-git-log` is used)
    -   Exports the git log for each downloaded repository into a CSV file.
    -   Filters these logs to identify commits related to test files (`src/test/.*Test.*\.java`).
    -   Merges individual test commit logs into a single comprehensive CSV file.
    -   Provides basic statistics, such as the number of unique authors for test commits per project.
-   **Detailed Logging**: Maintains a log file (`repodigger.log`) capturing the script's operations, warnings, and errors.

## Prerequisites

1.  **Python 3.8+**: As defined in `pyproject.toml`.
2.  **`uv` (Recommended)**: For environment and package management. Installation instructions above.
3.  **Git**: The script uses `git` command-line tool to clone repositories and export logs. Make sure Git is installed and accessible in your system's PATH.
4.  **GitHub Personal Access Token**:
    -   The script requires a GitHub Personal Access Token (PAT) to interact with the GitHub API.
    -   **Priority is given to the `GITHUB_TOKEN` environment variable.**
    -   If the environment variable is not set, the script will attempt to import it from a `SECRET.py` file located in the project root (e.g., `GITHUB_TOKEN = "your_actual_github_token_here"`).
    -   Create a token with the `repo` scope (or at least `public_repo`).
    -   **Important**: If using `SECRET.py`, do not commit it or your token to version control. It is already included in the `.gitignore` file.

## Usage (if not using Quick Start `uvx` or `uv tool install` methods)

If you have set up a local development environment (e.g., using `uv venv` and `uv pip install -e .` as shown in Quick Start step 5):

```bash
python repodigger.py --organization <ORG_NAME> --download-folder <PATH_TO_DOWNLOAD_FOLDER> [OPTIONS]
```

### Command-Line Arguments (for `repodigger` or `python repodigger.py`):

-   `--organization <ORG_NAME>`: (Required) Specifies the GitHub organization (e.g., `Netflix`, `apache`, `google`).
-   `--download-folder <PATH_TO_DOWNLOAD_FOLDER>`: (Required) Defines the base directory where the organization-specific subfolder will be created.
-   `--min-stars <NUMBER>`: Minimum stars a repository must have (>=). Defaults to `200`.
-   `--export-git-log`: Optional flag to export git logs and analyze test commits. Disabled by default.

### Examples (using direct script execution in an active virtual environment):

1.  **Download from Netflix, >=500 stars, to `./downloaded_repos` (no git log):**
    ```bash
    python repodigger.py --organization Netflix --min-stars 500 --download-folder ./downloaded_repos
    ```

2.  **Download from Apache, default stars, to `/data/gh_projects`, export git logs:**
    ```bash
    python repodigger.py --organization apache --download-folder /data/gh_projects --export-git-log
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

RepoDigger attempts to identify projects using Maven or Gradle:

1.  After a repository is cloned, the script traverses its entire directory structure (ignoring `.git`).
2.  It looks for: Maven (`pom.xml`), Gradle (`build.gradle`, `build.gradle.kts`), Ant (`build.xml`), Bazel (`WORKSPACE`, `BUILD`, `BUILD.bazel`).
3.  A repository qualifies if it contains Maven/Gradle build files AND NOT Ant/Bazel files.
4.  Non-qualifying repositories are logged and their cloned directory is removed.

## Logging

Detailed logs are saved to `<download_folder>/<ORG_NAME>-projects/repodigger.log`.

---

Feel free to suggest improvements or report issues! 