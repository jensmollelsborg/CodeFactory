"""Authentication service for GitHub OAuth."""

import os
from functools import wraps
from flask import session, redirect, url_for, request
from requests_oauthlib import OAuth2Session

# GitHub OAuth settings
GITHUB_CLIENT_ID = os.getenv('GITHUB_CLIENT_ID')
GITHUB_CLIENT_SECRET = os.getenv('GITHUB_CLIENT_SECRET')
GITHUB_AUTHORIZE_URL = 'https://github.com/login/oauth/authorize'
GITHUB_TOKEN_URL = 'https://github.com/login/oauth/access_token'
GITHUB_API_BASE_URL = 'https://api.github.com/'
GITHUB_CALLBACK_URL = os.getenv('GITHUB_CALLBACK_URL')

def get_github_oauth():
    """Create GitHub OAuth session."""
    if not GITHUB_CLIENT_ID or not GITHUB_CALLBACK_URL:
        raise ValueError("GitHub OAuth configuration is incomplete. Check GITHUB_CLIENT_ID and GITHUB_CALLBACK_URL in .env")
        
    return OAuth2Session(
        GITHUB_CLIENT_ID,
        redirect_uri=GITHUB_CALLBACK_URL,
        scope=['repo,user']
    )

def login_required(f):
    """Decorator to require GitHub authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'github_token' not in session:
            # Store the requested URL for redirect after auth
            session['next_url'] = request.url
            return redirect(url_for('github_login'))
        return f(*args, **kwargs)
    return decorated_function

def get_github_token():
    """Get GitHub token from session."""
    return session.get('github_token')

def is_authenticated():
    """Check if user is authenticated."""
    return 'github_token' in session

def clear_auth():
    """Clear authentication session."""
    session.pop('github_token', None)
    session.pop('github_user', None)
    session.pop('next_url', None)
