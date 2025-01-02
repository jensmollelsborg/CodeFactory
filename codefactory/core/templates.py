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
        system_message="""You are an AI coding assistant. Produce Python code that fulfills the user's requirement.
        Follow these guidelines:
        1. Use type hints and docstrings
        2. Follow PEP 8 style guidelines
        3. Include error handling
        4. Write modular, reusable code
        5. Add appropriate logging""",
        user_template="""
        The user wants the following feature:
        {requirement}

        Write a Python program that fulfills this requirement.
        Use best practices, docstrings, and clear code structure.
        """
    ),
    "update_code": PromptTemplate(
        system_message="""You are an AI coding assistant. Modify the given code to fulfill the user story.
        Follow these guidelines:
        1. Preserve existing functionality
        2. Maintain code style consistency
        3. Add appropriate error handling
        4. Update docstrings and comments
        5. Only change what is necessary""",
        user_template="""
        Existing code:
        {existing_code}

        The user story is:
        {requirement}

        Please update the existing code to fulfill this requirement, preserving existing functionality.
        Only change what is necessary.
        Return code only.
        """
    ),
    "refactor_code": PromptTemplate(
        system_message="""You are an AI coding assistant. Refactor the given code to improve its quality.
        Follow these guidelines:
        1. Improve code organization
        2. Remove code duplication
        3. Enhance readability
        4. Add type hints and docstrings
        5. Follow SOLID principles""",
        user_template="""
        Code to refactor:
        {existing_code}

        Refactoring goals:
        {requirement}

        Please refactor the code to meet these goals while maintaining functionality.
        Return code only.
        """
    ),
    "fix_bug": PromptTemplate(
        system_message="""You are an AI coding assistant. Fix bugs in the given code.
        Follow these guidelines:
        1. Identify the root cause
        2. Add appropriate error handling
        3. Add validation where needed
        4. Add logging for debugging
        5. Add comments explaining the fix""",
        user_template="""
        Buggy code:
        {existing_code}

        Bug description:
        {requirement}

        Please fix the bug while maintaining existing functionality.
        Return code only.
        """
    )
}
