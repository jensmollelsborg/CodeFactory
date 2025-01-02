"""Input validation utilities."""

import re
from typing import Tuple
from ..core.exceptions import ValidationError

def validate_user_story_input(data: dict) -> Tuple[bool, str]:
    """
    Validates the user story submission data.
    
    Args:
        data: Dictionary containing user story data
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not data.get('userStory'):
        return False, "User story is required"
    
    if len(data['userStory']) > 1000:
        return False, "User story is too long (max 1000 characters)"
    
    if not data.get('priority'):
        return False, "Priority is required"
        
    if data['priority'] not in ['low', 'medium', 'high']:
        return False, "Priority must be one of: low, medium, high"
    
    if len(data.get('notes', '')) > 2000:
        return False, "Notes are too long (max 2000 characters)"
        
    return True, None

def validate_github_url(url: str) -> bool:
    """
    Validates if the given URL is a valid GitHub repository URL.
    
    Args:
        url: The URL to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not url:
        return False
        
    # HTTPS format: https://github.com/owner/repo[.git]
    https_pattern = r'^https?://github\.com/[\w.-]+/[\w.-]+(?:\.git)?$'
    
    # SSH format: git@github.com:owner/repo[.git]
    ssh_pattern = r'^git@github\.com:[\w.-]+/[\w.-]+(?:\.git)?$'
    
    return bool(re.match(https_pattern, url) or re.match(ssh_pattern, url))
