"""Git provider factory and implementations."""

from abc import ABC, abstractmethod
import os
from typing import Dict, List, Tuple, Optional
import git
from github import Github
from bitbucket.client import Client as BitbucketClient
from requests_oauthlib import OAuth2Session
import requests
import logging

logger = logging.getLogger(__name__)

class GitProvider(ABC):
    @abstractmethod
    def get_oauth_session(self) -> OAuth2Session:
        pass

    @abstractmethod
    def get_authorize_url(self) -> str:
        pass

    @abstractmethod
    def get_token_url(self) -> str:
        pass

    @abstractmethod
    def fetch_token(self, code: str, callback_url: str) -> Dict:
        pass

    @abstractmethod
    def get_user_info(self, token: str) -> Dict:
        pass

    @abstractmethod
    def get_repositories(self, token: str) -> List[Dict]:
        pass

    @abstractmethod
    def create_pull_request(self, token: str, repo_url: str, branch: str, title: str, body: str) -> str:
        pass

class GitHubProvider(GitProvider):
    def __init__(self):
        self.client_id = os.getenv('GITHUB_CLIENT_ID')
        self.client_secret = os.getenv('GITHUB_CLIENT_SECRET')
        self.authorize_url = 'https://github.com/login/oauth/authorize'
        self.token_url = 'https://github.com/login/oauth/access_token'
        self.callback_url = os.getenv('GITHUB_CALLBACK_URL')

    def get_oauth_session(self) -> OAuth2Session:
        return OAuth2Session(
            self.client_id,
            redirect_uri=self.callback_url,
            scope=['repo,user']
        )

    def get_authorize_url(self) -> str:
        return self.authorize_url

    def get_token_url(self) -> str:
        return self.token_url

    def fetch_token(self, code: str, callback_url: str) -> Dict:
        oauth = self.get_oauth_session()
        return oauth.fetch_token(
            self.token_url,
            client_secret=self.client_secret,
            authorization_response=callback_url
        )

    def get_user_info(self, token: str) -> Dict:
        gh = Github(token)
        user = gh.get_user()
        return {
            'login': user.login,
            'name': user.name,
            'avatar_url': user.avatar_url
        }

    def get_repositories(self, token: str) -> List[Dict]:
        gh = Github(token)
        return [{
            'name': repo.name,
            'full_name': repo.full_name,
            'url': repo.html_url,
            'description': repo.description,
            'private': repo.private,
            'provider': 'github'
        } for repo in gh.get_user().get_repos()]

    def create_pull_request(self, token: str, repo_url: str, branch: str, title: str, body: str) -> str:
        """Create a pull request on GitHub.
        
        Args:
            token: GitHub access token
            repo_url: Repository URL
            branch: Source branch name
            title: Pull request title
            body: Pull request description
            
        Returns:
            URL of the created pull request
        """
        try:
            gh = Github(token)
            
            # Extract owner and repo name from URL
            parts = repo_url.strip('/').split('/')
            owner = parts[-2]
            repo_name = parts[-1]
            
            # Get the repository
            repo = gh.get_repo(f"{owner}/{repo_name}")
            
            # Create the pull request
            pr = repo.create_pull(
                title=title,
                body=body,
                head=branch,
                base='main'  # or use the repository's default branch
            )
            
            return pr.html_url
            
        except Exception as e:
            logger.error(f"Failed to create pull request: {str(e)}")
            raise GitOperationError(f"Failed to create pull request: {str(e)}")

class BitbucketServerProvider(GitProvider):
    def __init__(self):
        self.server_url = os.getenv('BITBUCKET_SERVER_URL').rstrip('/')
        self.access_token = os.getenv('BITBUCKET_ACCESS_TOKEN')
        
        if not self.server_url or not self.access_token:
            raise ValueError("BITBUCKET_SERVER_URL and BITBUCKET_ACCESS_TOKEN must be set in environment variables")

    def get_oauth_session(self) -> OAuth2Session:
        """Not used with token auth, but required by abstract class."""
        return None

    def get_authorize_url(self) -> str:
        """Not used with token auth, but required by abstract class."""
        return ""

    def get_token_url(self) -> str:
        """Not used with token auth, but required by abstract class."""
        return ""

    def fetch_token(self, code: str, callback_url: str) -> Dict:
        """Not used with token auth, but required by abstract class."""
        return {}

    def get_repositories(self, token: str = None) -> List[Dict]:
        headers = {'Authorization': f'Bearer {self.access_token}'}
        repos = []
        start = 0
        limit = 100

        try:
            # First, get all projects
            projects_response = requests.get(
                f"{self.server_url}/rest/api/1.0/projects",
                params={'start': 0, 'limit': 100},
                headers=headers
            )
            projects_response.raise_for_status()
            projects_data = projects_response.json()

            # For each project, get its repositories
            for project in projects_data['values']:
                project_key = project['key']
                
                while True:
                    response = requests.get(
                        f"{self.server_url}/rest/api/1.0/projects/{project_key}/repos",
                        params={'start': start, 'limit': limit},
                        headers=headers
                    )
                    response.raise_for_status()
                    data = response.json()
                    
                    for repo in data['values']:
                        repos.append({
                            'name': repo['name'],
                            'full_name': f"{project_key}/{repo['name']}",
                            'url': f"{self.server_url}/projects/{project_key}/repos/{repo['slug']}/browse",
                            'description': repo.get('description', ''),
                            'private': not repo.get('public', True),
                            'provider': 'bitbucket'
                        })

                    if not data.get('isLastPage', True):
                        start = data['nextPageStart']
                    else:
                        break
                
                # Reset start for next project
                start = 0

            logger.info(f"Found {len(repos)} repositories across all projects")
            return repos

        except Exception as e:
            logger.error(f"Error fetching repositories: {str(e)}")
            raise GitOperationError(f"Failed to fetch repositories: {str(e)}")

    def create_pull_request(self, token: str, repo_url: str, branch: str, title: str, body: str) -> str:
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

        # Parse repository URL to get project and repo slug
        parts = repo_url.strip('/').split('/')
        project_key = parts[-3]
        repo_slug = parts[-1]

        data = {
            'title': title,
            'description': body,
            'fromRef': {
                'id': f'refs/heads/{branch}',
                'repository': {
                    'slug': repo_slug,
                    'project': {'key': project_key}
                }
            },
            'toRef': {
                'id': 'refs/heads/main',  # or use configured default branch
                'repository': {
                    'slug': repo_slug,
                    'project': {'key': project_key}
                }
            }
        }

        response = requests.post(
            f"{self.server_url}/rest/api/1.0/projects/{project_key}/repos/{repo_slug}/pull-requests",
            headers=headers,
            json=data
        )
        response.raise_for_status()
        pr_data = response.json()
        
        return pr_data['links']['self'][0]['href']

    def get_user_info(self, token: str = None) -> Dict:
        headers = {'Authorization': f'Bearer {self.access_token}'}
        response = requests.get(
            f"{self.server_url}/rest/api/latest/users",
            headers=headers
        )
        response.raise_for_status()
        user_data = response.json()
        
        if user_data and 'values' in user_data and user_data['values']:
            user = user_data['values'][0]
            return {
                'login': user['slug'],
                'name': user['displayName'],
                'avatar_url': f"{self.server_url}/users/{user['slug']}/avatar.png"
            }
        else:
            raise ValueError("Could not fetch user information")

def get_provider(provider_name: str) -> GitProvider:
    """Factory method to get the appropriate git provider."""
    providers = {
        'github': GitHubProvider,
        'bitbucket': BitbucketServerProvider,
    }
    provider_class = providers.get(provider_name.lower())
    if not provider_class:
        raise ValueError(f"Unsupported git provider: {provider_name}")
    return provider_class() 