"""Git operations service."""

import os
import git
import datetime
from github import Github
from typing import Tuple, List, Dict
from dotenv import load_dotenv

from ..core.exceptions import GitOperationError
from ..utils.validation import validate_github_url
from ..utils.logging import get_logger

# Load environment variables
load_dotenv()

# Setup logging
logger = get_logger(__name__)

# Get configuration
base_branch = os.getenv("BASE_BRANCH", "main")

def parse_github_url(github_url: str) -> Tuple[str, str]:
    """
    Extract owner and repo name from a GitHub URL.
    
    Args:
        github_url: The GitHub repository URL
        
    Returns:
        Tuple of (owner, repo_name)
        
    Raises:
        GitOperationError: If URL is invalid or can't be parsed
    """
    if not validate_github_url(github_url):
        raise GitOperationError(f"Invalid GitHub URL format: {github_url}")

    try:
        # Remove possible endings like ".git"
        cleaned_url = github_url.replace(".git", "")
        
        if "github.com/" in cleaned_url:
            parts = cleaned_url.split("github.com/")[-1]
        elif "github.com:" in cleaned_url:
            parts = cleaned_url.split("github.com:")[-1]
        else:
            raise GitOperationError(f"Cannot parse GitHub URL: {github_url}")

        if not parts or '/' not in parts:
            raise GitOperationError(f"Invalid GitHub URL format: {github_url}")

        owner, repo_name = parts.split("/", 1)
        
        if not owner or not repo_name:
            raise GitOperationError(f"Invalid GitHub URL format: {github_url}")
            
        return owner, repo_name
            
    except Exception as e:
        raise GitOperationError(f"Error parsing GitHub URL: {github_url}. Error: {str(e)}")

def clone_or_open_repo(repo_url: str, local_name: str = "default_repo") -> Tuple[git.Repo, str]:
    """
    Clone or open a GitHub repository.
    
    Args:
        repo_url: The GitHub repository URL
        local_name: Name for the local repository directory
        
    Returns:
        Tuple of (repo, repo_path)
        
    Raises:
        GitOperationError: If repository operations fail
    """
    if not validate_github_url(repo_url):
        raise GitOperationError(f"Invalid GitHub repository URL: {repo_url}")

    repo_dir = os.getenv("REPO_DIR")
    if not repo_dir:
        raise GitOperationError("REPO_DIR environment variable is not set")

    repo_path = os.path.join(repo_dir, local_name)
    
    try:
        if not os.path.exists(repo_path):
            logger.info(f"Cloning {repo_url} into {repo_path}...")
            repo = git.Repo.clone_from(repo_url, repo_path)
        else:
            logger.info(f"Opening existing repository at {repo_path}")
            repo = git.Repo(repo_path)

        # Fetch from remote to ensure we have the latest state
        logger.info("Fetching latest changes from remote...")
        repo.remotes.origin.fetch()

        # Get the default remote branch
        logger.info(f"Default branch is: {base_branch}")

        # Checkout and pull the default branch
        repo.git.checkout(base_branch)
        logger.info(f"Checked out {base_branch}")
        
        # Pull latest changes
        logger.info(f"Pulling latest changes from {base_branch}...")
        repo.remotes.origin.pull(base_branch)

        return repo, repo_path
        
    except git.exc.GitCommandError as e:
        raise GitOperationError(f"Git operation failed: {str(e)}")

def create_unique_branch_and_push(
    repo: git.Repo,
    base_branch: str,
    file_path: str,
    updated_code: str,
    commit_message: str
) -> str:
    """
    Create a unique branch, commit changes, and push to remote.
    
    Args:
        repo: GitPython Repo instance
        base_branch: Name of the base branch
        file_path: Path to the file to update
        updated_code: New content for the file
        commit_message: Commit message
        
    Returns:
        Name of the created branch
        
    Raises:
        GitOperationError: If Git operations fail
    """
    try:
        # Generate a unique branch name
        branch_suffix = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        new_branch_name = f"feature/user-story-update-{branch_suffix}"

        # Create & checkout the new branch
        try:
            repo.git.checkout('-b', new_branch_name)
        except git.exc.GitCommandError:
            repo.git.checkout(new_branch_name)

        # Write updated code
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(updated_code)

        # Stage & commit
        repo.git.add(A=True)
        if repo.is_dirty():
            repo.index.commit(commit_message)

        # Push the new branch
        origin = repo.remotes.origin
        origin.push(new_branch_name)

        return new_branch_name
        
    except Exception as e:
        raise GitOperationError(f"Failed to create and push branch: {str(e)}")

def create_pull_request(
    repo_url: str,
    branch_name: str,
    pr_title: str,
    pr_body: str,
    base_branch: str = base_branch
) -> str:
    """
    Create a pull request on GitHub.
    
    Args:
        repo_url: The GitHub repository URL
        branch_name: Name of the branch to create PR from
        pr_title: Title for the pull request
        pr_body: Body/description for the pull request
        base_branch: Target branch for the PR
        
    Returns:
        URL of the created pull request
        
    Raises:
        GitOperationError: If PR creation fails
    """
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise GitOperationError("GITHUB_TOKEN is not set. Cannot create pull request.")

    try:
        g = Github(token)
        owner, repo_name = parse_github_url(repo_url)
        gh_repo = g.get_repo(f"{owner}/{repo_name}")

        pull = gh_repo.create_pull(
            title=pr_title,
            body=pr_body,
            head=branch_name,
            base=base_branch
        )
        
        logger.info(f"Pull request created: {pull.html_url}")
        return pull.html_url
        
    except Exception as e:
        raise GitOperationError(f"Failed to create pull request: {str(e)}")

def get_user_repositories() -> List[Dict[str, str]]:
    """
    Fetch list of repositories accessible to the authenticated user.
    Includes both user's repositories and those they have access to.
    
    Returns:
        List of dictionaries containing repository information:
        [{"name": "repo-name", "full_name": "owner/repo", "url": "https://github.com/owner/repo"}]
        
    Raises:
        GitOperationError: If unable to fetch repositories
    """
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        raise GitOperationError("GITHUB_TOKEN environment variable is not set")
        
    try:
        # Initialize GitHub client
        gh = Github(github_token)
        user = gh.get_user()
        
        # Get repositories the user has access to
        repos = []
        logger.info("Fetching user repositories...")
        
        # Add user's own repositories
        for repo in user.get_repos():
            repos.append({
                "name": repo.name,
                "full_name": repo.full_name,
                "url": repo.html_url,
                "description": repo.description or "",
                "private": repo.private,
                "fork": repo.fork,
                "updated_at": repo.updated_at.isoformat() if repo.updated_at else None
            })
            
        # Sort repositories by name
        repos.sort(key=lambda x: x["full_name"].lower())
        
        logger.info(f"Found {len(repos)} repositories")
        return repos
        
    except Exception as e:
        raise GitOperationError(f"Failed to fetch repositories: {str(e)}")
