import argparse
from datetime import datetime, timedelta
from git import Repo
import pandas as pd
import os
import csv
import subprocess
import logging
import shutil
import glob
import sys

import requests

# Attempt to get GITHUB_TOKEN from environment variable first
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')

# If not found in environment, try to import from SECRET.py
if GITHUB_TOKEN is None:
    try:
        from SECRET import GITHUB_TOKEN as SECRET_GITHUB_TOKEN
        GITHUB_TOKEN = SECRET_GITHUB_TOKEN
    except ImportError:
        # Log an error and exit if GITHUB_TOKEN is not found in either location
        # We need logging to be configured to see this if it happens early
        # For now, print to stderr and raise an exception for immediate feedback
        # This part will be more effective once logging is initialized, 
        # but an early exit is crucial if the token is missing.
        print("ERROR: GITHUB_TOKEN not found. Please set the GITHUB_TOKEN environment variable or create a SECRET.py file with GITHUB_TOKEN defined.", file=sys.stderr) # Added sys import for stderr
        raise ImportError("GITHUB_TOKEN not found in environment or SECRET.py")

# Check if GITHUB_TOKEN is still None or empty after attempts, and if so, handle error.
if not GITHUB_TOKEN:
    # This case might be redundant if the try-except block for SECRET.py handles it, 
    # but it's a safeguard for an empty token from env or SECRET.py.
    print("ERROR: GITHUB_TOKEN is empty. Please ensure it has a value in the environment variable or SECRET.py.", file=sys.stderr)
    raise ValueError("GITHUB_TOKEN is empty.")

# Main script execution
def main(org_name, min_stars, download_folder_base, export_git_log):
    # Create the base download dir if it doesn't exist
    if not os.path.exists(download_folder_base):
        os.makedirs(download_folder_base)

    # Create the specific dir for the organization within the download folder
    org_projects_dir = os.path.join(download_folder_base, org_name + "-projects")
    if not os.path.exists(org_projects_dir):
        os.makedirs(org_projects_dir)

    # Set log level and file path
    log_file_path = os.path.join(org_projects_dir, 'repodigger.log')
    logging.basicConfig(level=logging.INFO,
                        filename=log_file_path,
                        filemode='a',  # Append to the log file if it exists
                        format='%(asctime)s - %(levelname)s - %(message)s')

    # Additional configuration to enable console output
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

    logging.info(f"Starting repodigger for organization: {org_name}")
    logging.info(f"Minimum stars: {min_stars}")
    logging.info(f"Download folder: {org_projects_dir}")


    # Get the project list from the GitHub API
    logging.info("=== Getting the project list from the GitHub API ===")
    # Calculate three years ago for the pushed date query
    three_years_ago = (datetime.now() - timedelta(days=3*365)).strftime('%Y-%m-%d') # Approximate 3 years
    # Updated query to include stars>=min_stars and pushed date within last 3 years
    base_url = f"https://api.github.com/search/repositories?q=org:{org_name}+language:Java+archived:false+pushed:>{three_years_ago}+stars:>={min_stars}&sort=updated&order=desc"

    headers = {'Authorization': f'token {GITHUB_TOKEN}'}

    def get_repos_from_api(url):
        all_repos_details = []
        page = 1
        while True:
            paginated_url = f"{url}&page={page}&per_page=100" # Max 100 per page
            response = requests.get(paginated_url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                current_page_repos = data['items']
                if not current_page_repos: # No more repos
                    break
                all_repos_details.extend(current_page_repos)
                if len(current_page_repos) < 100: # Last page
                    break
                page += 1
            else:
                logging.error(f"Failed to retrieve repositories (page {page}): {response.status_code} - {response.text}")
                break
        return all_repos_details

    repos_with_details = get_repos_from_api(base_url)
    logging.info(f"Retrieved {len(repos_with_details)} repositories from API before build system check.")

    # Filtered list of repo names that meet all criteria including build system
    final_repos_to_process = []
    
    # Temporarily store repos that are cloned but fail build check, to be deleted
    repos_to_delete_after_check = []

    # Function to check build system
    def check_build_system(repo_clone_path, repo_name_for_log):
        # Traverse the directory tree to find build files
        found_maven = False
        found_gradle = False
        found_ant = False
        found_bazel = False

        for root, dirs, files in os.walk(repo_clone_path):
            # Skip .git directory to avoid issues and speed up search
            if ".git" in dirs:
                dirs.remove(".git")
            
            if "pom.xml" in files:
                found_maven = True
            if "build.gradle" in files or "build.gradle.kts" in files:
                found_gradle = True
            if "build.xml" in files:
                found_ant = True
            if "WORKSPACE" in files or "BUILD" in files or "BUILD.bazel" in files:
                found_bazel = True
        
        # Decision logic based on found files
        if (found_maven or found_gradle) and not (found_ant or found_bazel):
            build_system = []
            if found_maven:
                build_system.append("Maven")
            if found_gradle:
                build_system.append("Gradle")
            logging.info(f"Repo {repo_name_for_log}: Found {' and '.join(build_system)}. Qualifying build system.")
            return True
        else:
            reasons = []
            if not (found_maven or found_gradle):
                reasons.append("Neither Maven nor Gradle found anywhere in the project")
            if found_ant:
                reasons.append("Ant build file (build.xml) detected")
            if found_bazel:
                reasons.append("Bazel build file (WORKSPACE, BUILD, or BUILD.bazel) detected")
            
            # More specific logging if both desired and undesired systems are found
            if (found_maven or found_gradle) and (found_ant or found_bazel):
                 reasons.append("Project contains a mix of desired (Maven/Gradle) and undesired (Ant/Bazel) build systems.")

            logging.warning(f"Repo {repo_name_for_log}: Build system check failed. Reasons: {'; '.join(reasons)}. Excluding.")
            return False

    logging.info("=== Cloning repositories and checking build systems ===")
    failed_clones = [] # Repos that failed to clone for other reasons

    for repo_detail in repos_with_details:
        repo_name = repo_detail['name']
        repo_clone_url = repo_detail['clone_url']
        repo_path_in_org_dir = os.path.join(org_projects_dir, repo_name)

        try:
            if os.path.exists(repo_path_in_org_dir):
                # If already exists, check its build system if not already processed
                # This scenario implies a previous run might have been interrupted
                # or the repo was manually placed. We re-check build system.
                logging.info(f"Repo {repo_name} already exists. Checking build system...")
                if check_build_system(repo_path_in_org_dir, repo_name):
                    final_repos_to_process.append(repo_name)
                    logging.info(f"Repo {repo_name} (existing) meets criteria.")
                else:
                    # If it exists but doesn't meet build criteria, we might not delete it here
                    # as it could be intentionally there. We just log and exclude.
                    logging.warning(f"Repo {repo_name} (existing) does not meet build system criteria. Excluding from this run.")
                continue

            logging.info(f"Cloning {repo_name} from {repo_clone_url}...")
            Repo.clone_from(repo_clone_url, repo_path_in_org_dir)
            logging.info(f"Successfully cloned {repo_name} to {repo_path_in_org_dir}")

            if check_build_system(repo_path_in_org_dir, repo_name):
                final_repos_to_process.append(repo_name)
                # Disk usage check only for successfully qualified and cloned repos
                total, used, free = shutil.disk_usage(download_folder_base) # Check usage of the base download folder
                used_percentage = (used / total) * 100
                logging.info(f"Disk usage of {download_folder_base}: {used_percentage:.2f}%")
                if used_percentage > 90:
                    logging.warning(f"Disk usage exceeded 90% ({used_percentage:.2f}% used). Stopping the cloning process.")
                    # Identify remaining repos from the original API list to mark as "not attempted due to disk space"
                    current_index = repos_with_details.index(repo_detail)
                    remaining_api_repos = [r['name'] for r in repos_with_details[current_index+1:]]
                    failed_clones.extend(remaining_api_repos) # Add them to failed_clones with a note or different list
                    logging.info(f"The following repos were not attempted due to disk space: {remaining_api_repos}")
                    break 
            else:
                # Build system check failed, so schedule for deletion
                repos_to_delete_after_check.append(repo_path_in_org_dir)
        
        except Exception as e:
            logging.warning(f"Failed to clone or process {repo_name}. Reason: {e}")
            failed_clones.append(repo_name)
            # If cloning failed, the path might not exist or be partial.
            # Ensure we don't try to delete a non-existent/problematic path.
            if os.path.exists(repo_path_in_org_dir) and repo_path_in_org_dir not in repos_to_delete_after_check:
                 repos_to_delete_after_check.append(repo_path_in_org_dir)


    # Delete repos that were cloned but failed build system check
    if repos_to_delete_after_check:
        logging.info(f"Cleaning up {len(repos_to_delete_after_check)} repos that failed build system check...")
        for repo_path_to_delete in repos_to_delete_after_check:
            try:
                shutil.rmtree(repo_path_to_delete)
                logging.info(f"Successfully deleted {repo_path_to_delete}")
            except Exception as e:
                logging.error(f"Failed to delete directory {repo_path_to_delete}. Reason: {e}")
    
    # Save list of genuinely failed clones (network issues, git errors, disk full partway, etc.)
    if failed_clones:
        logging.info(f"Failed to clone or process {len(failed_clones)} repos: {failed_clones}")
        unfinished_projects_file = os.path.join(org_projects_dir, "failed_or_skipped_projects.txt")
        with open(unfinished_projects_file, "w") as file:
            for repo_name in failed_clones:
                file.write(f"{repo_name}\n")
        logging.info(f"List of failed/skipped projects saved to {unfinished_projects_file}")

    if not final_repos_to_process:
        logging.info("No repositories met all criteria to proceed with log export and analysis.")
        logging.info(f"Repodigger finished processing for {org_name}. No projects to analyze further.")
        return # Exit if no repos to process

    # Conditionally execute git log export and analysis
    if export_git_log: 
        logging.info(f"Proceeding with {len(final_repos_to_process)} qualified repositories: {final_repos_to_process}")
        # Start to export the git log from the cloned repos
        logging.info("=== Exporting the git log ===")
        # create the folder to store the git log
        # Path adjustments: log_dir is now relative to org_projects_dir
        git_log_export_dir = os.path.join(org_projects_dir, "git_log")
        if not os.path.exists(git_log_export_dir):
            logging.info(f"Creating git log export directory {git_log_export_dir}")
            os.makedirs(git_log_export_dir)

        # Export the git log with the diff information as a CSV file
        def export_git_log_to_csv(repo_name, cloned_repos_container_dir, target_log_dir):
            # repo_path is the full path to the specific repo inside org_projects_dir
            repo_full_path = os.path.join(cloned_repos_container_dir, repo_name)
            log_file_path = os.path.join(target_log_dir, f"{repo_name}_git_log.csv")

            # Ensure git commands run from within the repo's directory or use -C
            # Using -C is safer
            git_command = [
                'git', '-C', repo_full_path, 'log',
                '--date=short',
                '--numstat',
                '--pretty=format:%H,%ad,%aN,%ae' # Removed "commit " prefix from here
            ]

            try:
                # Check if log file already exists
                if os.path.exists(log_file_path):
                    logging.info(f"Git log for {repo_name} already exists at {log_file_path}. Skipping export.")
                    return

                result = subprocess.run(git_command, capture_output=True, text=True, check=True, encoding='utf-8') # Added encoding
                output = result.stdout

                with open(log_file_path, mode='w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(["Commit Hash", "Date", "Author Name", "Author Email", "Added Lines", "Deleted Lines", "File Path"])

                    current_commit_info = [] # Renamed from commit_info
                    for line in output.splitlines(): # use splitlines()
                        if not line.strip(): # Skip empty lines that might occur between commit blocks
                            continue
                        
                        # Check if the line is a commit metadata line (Hash,Date,Author,Email)
                        # This regex is more robust for parsing the commit metadata line.
                        # It expects 4 comma-separated values.
                        parts = line.split(',', 3)
                        if len(parts) == 4 and len(parts[0]) == 40 and all(c in '0123456789abcdef' for c in parts[0]): # Heuristic for commit hash
                            current_commit_info = parts
                        elif current_commit_info and '\t' in line:  # Assumed numstat line associated with current_commit_info
                            stats = line.split('\t')
                            if len(stats) == 3:  # Added, Deleted, Path
                                # Handle cases where added/deleted might be '-'
                                added = stats[0] if stats[0] != '-' else '0'
                                deleted = stats[1] if stats[1] != '-' else '0'
                                writer.writerow(current_commit_info + [added, deleted, stats[2]])
                        # else:
                            # logging.debug(f"Skipping unparsed line for {repo_name}: {line}")


                logging.info(f"Successfully exported git log for {repo_name} to {log_file_path}")
            except subprocess.CalledProcessError as e:
                logging.warning(f"Failed to export git log for {repo_name}. Reason: {e.stdout} {e.stderr}")
            except Exception as ex: # Catch other potential errors like file writing issues
                logging.warning(f"An unexpected error occurred during git log export for {repo_name}. Reason: {ex}")


        for repo_name in final_repos_to_process: # Use the filtered list
            logging.info(f"Exporting git log for {repo_name}...")
            export_git_log_to_csv(repo_name, org_projects_dir, git_log_export_dir)


        # start to analyze the git log
        logging.info("=== Analyzing the git log ===")
        # Path adjustments: c4t_dir is relative to git_log_export_dir
        c4t_dir = os.path.join(git_log_export_dir, "c4t") # c4t: commit for test

        if not os.path.exists(c4t_dir):
            logging.info(f"Creating c4t directory {c4t_dir}")
            os.makedirs(c4t_dir)

        all_test_commits_csv = os.path.join(c4t_dir, "all_test_commit_log.csv")
        if os.path.exists(all_test_commits_csv):
            logging.info(f"Deleting old merged test commit log: {all_test_commits_csv}")
            os.remove(all_test_commits_csv)

        # Use git_log_export_dir to find log files, not log_dir from before
        log_files = glob.glob(os.path.join(git_log_export_dir, "*.csv"))


        no_test_commit_repos = []

        for log_file in log_files:
            # Ensure we are not processing the merged file itself if it's in the same directory
            if os.path.basename(log_file) == "all_test_commit_log.csv":
                continue
            try:
                df = pd.read_csv(log_file)
                
                # Ensure 'File Path' column exists
                if 'File Path' not in df.columns:
                    project_name_from_file = os.path.basename(log_file).replace('_git_log.csv', '')
                    logging.warning(f"Skipping {project_name_from_file}: 'File Path' column missing in {log_file}.")
                    continue

                # Filter records: .java files with 'Test' in name and 'src/test/' in file path
                # Make sure File Path is string type before using .str.contains
                df['File Path'] = df['File Path'].astype(str)
                filtered_df = df[df['File Path'].str.contains(r'src/test/.*Test.*\.java', regex=True, na=False)]


                project_name = os.path.basename(log_file).replace('_git_log.csv', '')
                if not filtered_df.empty:
                    filtered_df.to_csv(os.path.join(c4t_dir, f"{project_name}_test_commit_log.csv"), index=False)
                    logging.info(f"Saved test commit log for {project_name}")
                else:
                    logging.warning(f"No test-related commits found for {project_name}")
                    no_test_commit_repos.append(project_name)
            except pd.errors.EmptyDataError:
                project_name_from_file = os.path.basename(log_file).replace('_git_log.csv', '')
                logging.warning(f"Log file {log_file} for project {project_name_from_file} is empty or not valid CSV. Skipping.")
            except Exception as e:
                project_name_from_file = os.path.basename(log_file).replace('_git_log.csv', '')
                logging.error(f"Error processing log file {log_file} for {project_name_from_file}. Reason: {e}")


        if no_test_commit_repos:
            logging.info(f"No test-related commits found for {len(no_test_commit_repos)} repos: {no_test_commit_repos}")
            no_test_commit_repos_file = os.path.join(c4t_dir, "no_test_commit_repos.txt")
            with open(no_test_commit_repos_file, "w") as file:
                for repo_name in no_test_commit_repos:
                    file.write(f"{repo_name}\n")
            logging.info(f"No test commit repos list saved to {no_test_commit_repos_file}")


        logging.info("=== Merging the test commit log ===")
        # merge all the test commit log files into one dataframe
        # Use c4t_dir to find individual test log csv files
        test_log_files = glob.glob(os.path.join(c4t_dir, "*_test_commit_log.csv"))
        # Exclude the all_test_commit_log.csv itself if somehow it matches the pattern above, though unlikely with suffix
        test_log_files = [f for f in test_log_files if os.path.basename(f) != "all_test_commit_log.csv"]


        if not test_log_files:
            logging.info("No individual test commit logs found to merge.")
        else:
            merged_df = pd.DataFrame()
            for log_file in test_log_files:
                try:
                    df = pd.read_csv(log_file)
                    project_name = os.path.basename(log_file).replace('_test_commit_log.csv', '')
                    df['Project'] = project_name
                    merged_df = pd.concat([merged_df, df], ignore_index=True)
                except pd.errors.EmptyDataError:
                    logging.warning(f"Test commit log file {log_file} is empty. Skipping from merge.")
                except Exception as e:
                    logging.error(f"Error merging file {log_file}. Reason: {e}")


            if not merged_df.empty:
                merged_df.to_csv(all_test_commits_csv, index=False)
                logging.info(f"Saved merged test commit log to {all_test_commits_csv}")

                # Log the statistics of the test commit
                logging.info("=== Test commit statistics ===")
                # Ensure 'Author Email' column exists before grouping
                if 'Author Email' in merged_df.columns:
                    author_stats = merged_df.groupby('Project')['Author Email'].nunique()
                    logging.info("Number of unique authors per project (with test commits):")
                    for project, count in author_stats.items():
                        logging.info(f"{project}: {count}")
                else:
                    logging.warning("Could not generate author statistics: 'Author Email' column not found in merged data.")
            else:
                logging.info("Merged DataFrame is empty. No overall test commit log generated.")
    else: # This else corresponds to if export_git_log is False
        logging.info("Git log export and analysis skipped as per --export-git-log flag.")

    logging.info(f"Repodigger finished processing for {org_name}.")


def main_cli():
    parser = argparse.ArgumentParser(description="RepoDigger: Download and analyze GitHub repositories.")
    parser.add_argument("--organization", type=str, required=True, help="GitHub organization name (e.g., Netflix, apache).")
    parser.add_argument("--min-stars", type=int, default=200, help="Minimum number of stars for a repository to be included.")
    parser.add_argument("--download-folder", type=str, required=True, help="Base folder to download repositories and store logs/results.")
    parser.add_argument("--export-git-log", action='store_true', help="Optional: Export git log for each repository and analyze test commits. Disabled by default.")
    
    args = parser.parse_args()
    
    # Pass the new argument to main
    main(args.organization, args.min_stars, args.download_folder, args.export_git_log)

if __name__ == "__main__":
    main_cli()


