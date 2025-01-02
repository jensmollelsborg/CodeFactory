import git
import os
from dotenv import load_dotenv
from github import Github
import datetime
import re

load_dotenv()

base_branch = os.getenv("BASE_BRANCH")

def validate_github_url(url: str) -> bool:
    """
    Validates if the given URL is a valid GitHub repository URL.
    Supports both HTTPS and SSH formats.
    """
    if not url:
        return False
        
    # HTTPS format: https://github.com/owner/repo[.git]
    https_pattern = r'^https?://github\.com/[\w.-]+/[\w.-]+(?:\.git)?$'
    
    # SSH format: git@github.com:owner/repo[.git]
    ssh_pattern = r'^git@github\.com:[\w.-]+/[\w.-]+(?:\.git)?$'
    
    return bool(re.match(https_pattern, url) or re.match(ssh_pattern, url))

def parse_github_url(github_url: str) -> (str, str):
    """
    Extract 'owner' and 'repo_name' from a GitHub URL.
    Supports HTTPS format: https://github.com/owner/repo_name.git
    and SSH format: git@github.com:owner/repo_name.git

    Args:
        github_url (str): The GitHub repository URL

    Returns:
        tuple: (owner, repo_name_without_dotgit)

    Raises:
        ValueError: If the URL is invalid or cannot be parsed
    """
    if not validate_github_url(github_url):
        raise ValueError(f"Invalid GitHub URL format: {github_url}")

    # Remove possible endings like ".git"
    cleaned_url = github_url.replace(".git", "")
    
    try:
        # The core part might be after "github.com/" or "github.com:"
        if "github.com/" in cleaned_url:
            parts = cleaned_url.split("github.com/")[-1]
        elif "github.com:" in cleaned_url:
            parts = cleaned_url.split("github.com:")[-1]
        else:
            raise ValueError(f"Cannot parse GitHub URL: {github_url}")

        if not parts or '/' not in parts:
            raise ValueError(f"Invalid GitHub URL format: {github_url}")

        owner, repo_name = parts.split("/", 1)
        
        if not owner or not repo_name:
            raise ValueError(f"Invalid GitHub URL format: {github_url}")
            
        return owner, repo_name
    except Exception as e:
        raise ValueError(f"Error parsing GitHub URL: {github_url}. Error: {str(e)}")

def clone_or_open_repo(repo_url: str, local_name: str = "default_repo"):
    """
    Clones a GitHub repository if not present locally,
    otherwise opens the existing one. Ensures the repository
    is on the default branch.

    Args:
        repo_url (str): The GitHub repository URL
        local_name (str): Name for the local repository directory

    Returns:
        tuple: (repo, repo_path)

    Raises:
        ValueError: If the repository URL is invalid
        git.exc.GitCommandError: If there's an error with Git operations
    """
    if not validate_github_url(repo_url):
        raise ValueError(f"Invalid GitHub repository URL: {repo_url}")

    repo_dir = os.getenv("REPO_DIR")
    if not repo_dir:
        raise ValueError("REPO_DIR environment variable is not set")

    repo_path = os.path.join(repo_dir, local_name)
    
    try:
        if not os.path.exists(repo_path):
            print(f"Cloning {repo_url} into {repo_path}...")
            repo = git.Repo.clone_from(repo_url, repo_path)
        else:
            print(f"Repository already exists at {repo_path}.")
            repo = git.Repo(repo_path)

        # Fetch from remote to ensure we have the latest state
        print("Fetching latest changes from remote...")
        repo.remotes.origin.fetch()

        # Get the default remote branch
        print(f"Default branch is: {base_branch}")

        # Checkout the default branch
        repo.git.checkout(base_branch)
        print(f"Checked out {base_branch}")

        return repo, repo_path
    except git.exc.GitCommandError as e:
        raise ValueError(f"Git operation failed: {str(e)}")

def commit_changes(repo, commit_message="Update code for user story"):
    """
    Stages and commits changes to the cloned or opened repository.
    """
    repo.git.add(A=True)
    if repo.is_dirty():
        repo.index.commit(commit_message)
        print(f"Committed changes: {commit_message}")
    else:
        print("No changes to commit.")

def create_unique_branch_and_push(
    repo,
    base_branch: str,
    file_path: str,
    updated_code: str,
    commit_message: str
) -> str:
    """
    1. Checks out the base_branch (default branch, e.g., 'main').
    2. Creates a unique feature branch name (timestamp-based).
    3. Writes 'updated_code' to 'file_path', commits, and pushes changes.
    4. Returns the newly created branch name.
    """
    # 1. Checkout the default branch and pull the latest
    repo.git.checkout(base_branch)
    try:
        repo.remotes.origin.pull()
    except:
        print(f"Could not pull from origin/{base_branch}; continuing anyway.")

    # 2. Generate a unique branch name (timestamp)
    branch_suffix = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    new_branch_name = f"feature/user-story-update-{branch_suffix}"

    # 3. Create & checkout the new branch
    try:
        repo.git.checkout('-b', new_branch_name)
    except git.exc.GitCommandError:
        # If branch somehow already exists, check it out
        repo.git.checkout(new_branch_name)

    # 4. Write updated code
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(updated_code)

    # 5. Stage & commit
    repo.git.add(A=True)
    if repo.is_dirty():
        repo.index.commit(commit_message)

    # 6. Push the new branch
    origin = repo.remotes.origin
    origin.push(new_branch_name)

    return new_branch_name

def create_pull_request(
    repo_url: str,
    branch_name: str,
    pr_title: str,
    pr_body: str,
    base_branch=base_branch
):
    """
    Creates a pull request on GitHub from 'branch_name' to 'base_branch'.
    Requires GITHUB_TOKEN in the environment with 'repo' scopes.
    """
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN is not set. Cannot create pull request.")

    g = Github(token)
    owner, repo_name = parse_github_url(repo_url)
    gh_repo = g.get_repo(f"{owner}/{repo_name}")

    pull = gh_repo.create_pull(
        title=pr_title,
        body=pr_body,
        head=branch_name,
        base=base_branch
    )
    print(f"Pull request created: {pull.html_url}")
    return pull.html_url
