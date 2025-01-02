"""Template system for code generation."""

from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class PromptTemplate:
    """Template for generating prompts with consistent structure."""
    system_message: str
    user_template: str
    
    def format(self, **kwargs) -> Dict[str, Any]:
        """Format the template with the given parameters."""
        return {
            "system": self.system_message,
            "user": self.user_template.format(**kwargs)
        }

# Define common prompt templates
TEMPLATES = {
    "generate_code": PromptTemplate(
        system_message="You are an AI coding assistant. Produce Python code that fulfills the user's requirement.",
        user_template="""
        The user wants the following feature:
        {requirement}

        Write a Python program that fulfills this requirement.
        Use best practices, docstrings, and clear code structure.
        """
    ),
    "update_code": PromptTemplate(
        system_message="You are an AI coding assistant. Modify the given code to fulfill the user story.",
        user_template="""
        Existing code:
        {existing_code}

        The user story is:
        {requirement}

        Please update the existing code to fulfill this requirement, preserving existing functionality.
        Only change what is necessary.
        Return code only.
        """
    )
}
