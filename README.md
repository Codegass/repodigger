# RepoDigger

RepoDigger is a Python command-line tool designed to selectively download and optionally analyze Java repositories from specified GitHub organizations. It allows users to filter repositories based on criteria such as minimum star count, primary programming language (Java), archive status, and build system (Maven or Gradle, excluding Ant and Bazel).

## Features

-   **Targeted Repository Downloading**: Downloads repositories from a specific GitHub organization.
-   **Flexible Filtering**:
    -   Filters for public, non-archived Java projects.
    -   Filters by a minimum number of GitHub stars.
    -   Filters by projects managed with Maven or Gradle, automatically excluding those managed by Ant or Bazel. The tool inspects the entire repository structure to detect these build systems.
    -   Filters for projects updated within the last year.
-   **Custom Download Location**: Allows users to specify a directory where repositories and associated files will be saved.
-   **Optional Git Log Analysis**:
    -   If enabled, exports the git log for each downloaded repository into a CSV file.
    -   Filters these logs to identify commits related to test files (`src/test/.*Test.*\.java`).
    -   Merges individual test commit logs into a single comprehensive CSV file.
    -   Provides basic statistics, such as the number of unique authors પાણી test commits per project.
-   **Detailed Logging**: Maintains a log file (`repodigger.log`) capturing the script's operations, warnings, and errors.

## Prerequisites

1.  **Python 3.x**: Ensure you have Python 3.x installed.
2.  **Required Python Libraries**: Install the necessary libraries using pip:
    ```bash
    pip install GitPython pandas requests
    ```
3.  **Git**: The script uses `git` command-line tool to clone repositories and export logs. Make sure Git is installed and accessible in your system's PATH.
4.  **GitHub Personal Access Token**:
    -   The script requires a GitHub Personal Access Token (PAT) to interact with the GitHub API, especially to avoid rate limiting and access repository details.
    -   Create a token with the `repo` scope (or at least `public_repo`).
    -   Create a file named `SECRET.py` in the same directory as `repodigger.py`.
    -   Add your token to `SECRET.py` like this:
        ```python
        GITHUB_TOKEN = "your_actual_github_token_here"
        ```
        **Important**: Do not commit `SECRET.py` or your token to version control if you are managing this project with Git. Add `SECRET.py` to your `.gitignore` file.

## Usage

The script is run from the command line with several arguments:

```bash
python repodigger.py --organization <ORG_NAME> --download-folder <PATH_TO_DOWNLOAD_FOLDER> [OPTIONS]
```

### Required Arguments:

-   `--organization <ORG_NAME>`: Specifies the GitHub organization from which to download repositories (e.g., `Netflix`, `apache`, `google`).
-   `--download-folder <PATH_TO_DOWNLOAD_FOLDER>`: Defines the base directory where the organization-specific subfolder (e.g., `<PATH_TO_DOWNLOAD_FOLDER>/<ORG_NAME>-projects/`) will be created to store downloaded repositories, logs, and analysis results.

### Optional Arguments:

-   `--min-stars <NUMBER>`: Sets the minimum number of stars a repository must have to be included. Defaults to `200`.
-   `--export-git-log`: If this flag is present, the script will export git logs for each qualified repository and perform an analysis of test-related commits. This is disabled by default.

### Examples:

1.  **Download Java repositories from Netflix with at least 500 stars to `./downloaded_repos` (without git log export):**
    ```bash
    python repodigger.py --organization Netflix --min-stars 500 --download-folder ./downloaded_repos
    ```

2.  **Download Java repositories from Apache (default 200 stars) to `/data/github_projects` and export git logs:**
    ```bash
    python repodigger.py --organization apache --download-folder /data/github_projects --export-git-log
    ```

## Output Structure

All downloaded data and logs are organized within the specified download folder, under a subdirectory named after the organization:

```
<download_folder>/
|-- <ORG_NAME>-projects/
|   |-- repodigger.log                # Main log file for the script's operations.
|   |-- failed_or_skipped_projects.txt # Lists projects that failed to clone or were skipped (e.g., disk full).
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
|   |   |   |-- no_test_commit_repos.txt # Lists repos with no identified test-related commits.
```

## How Build System Detection Works

RepoDigger attempts to identify projects using Maven or Gradle:

1.  After a repository is cloned, the script traverses its entire directory structure (ignoring the `.git` folder).
2.  It looks for the presence of:
    -   Maven: `pom.xml`
    -   Gradle: `build.gradle` or `build.gradle.kts`
    -   Ant: `build.xml`
    -   Bazel: `WORKSPACE`, `BUILD`, `BUILD.bazel`
3.  A repository is considered to have a "qualifying" build system if:
    -   It contains at least one Maven or Gradle build file.
    -   AND it does NOT contain any Ant or Bazel build files.
4.  Repositories that do not meet these criteria (e.g., only Ant/Bazel found, no recognized Java build system found, or a mix of desired and undesired systems) are logged and the cloned directory is removed to save space.

## Logging

Detailed logs are saved to `<download_folder>/<ORG_NAME>-projects/repodigger.log`. This includes:
-   Script startup and parameters used.
-   Repositories retrieved from GitHub API.
-   Cloning progress and success/failure for each repository.
-   Build system check results for each repository.
-   Disk usage warnings.
-   Git log export and analysis steps (if enabled).
-   Errors encountered during the process.

It is recommended to check this log file, especially if the script doesn't behave as expected or if you want to see details about excluded repositories.

---

Feel free to suggest improvements or report issues! 