import git
import os
from dotenv import load_dotenv
from github import Github
import datetime

load_dotenv()

base_branch = os.getenv("BASE_BRANCH")

def parse_github_url(github_url: str) -> (str, str):
    """
    Extract 'owner' and 'repo_name' from a GitHub URL like:
    https://github.com/owner/repo_name.git
    or
    git@github.com:owner/repo_name.git

    Returns (owner, repo_name_without_dotgit)
    """
    # Remove possible endings like ".git"
    cleaned_url = github_url.replace(".git", "")
    # The core part might be after "github.com/" or "github.com:"
    # e.g. "https://github.com/owner/repo" -> segments after github.com/ is "owner/repo"
    # or "git@github.com:owner/repo" -> after "github.com:" is "owner/repo"
    if "github.com/" in cleaned_url:
        parts = cleaned_url.split("github.com/")[-1]
    elif "github.com:" in cleaned_url:
        parts = cleaned_url.split("github.com:")[-1]
    else:
        # If your URL doesn't match these patterns, adapt as needed
        raise ValueError(f"Cannot parse GitHub URL: {github_url}")

    owner, repo_name = parts.split("/", 1)
    return owner, repo_name

def clone_or_open_repo(repo_url: str, local_name: str = "default_repo"):
    """
    Clones a GitHub repository if not present locally,
    otherwise opens the existing one.
    Returns (repo, repo_path).
    """
    repo_dir = os.getenv("REPO_DIR")
    repo_path = os.path.join(repo_dir, local_name)
    if not os.path.exists(repo_path):
        print(f"Cloning {repo_url} into {repo_path}...")
        git.Repo.clone_from(repo_url, repo_path)
    else:
        print(f"Repository already exists at {repo_path}.")

    repo = git.Repo(repo_path)
    return repo, repo_path

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
