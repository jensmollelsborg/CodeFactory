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
        5. Add appropriate logging
        6. Organize code into appropriate files and modules
        7. Return a JSON object mapping file paths to code content
        8. Use descriptive file names that reflect their purpose""",
        user_template="""
        The user wants the following feature:
        {requirement}

        Write a Python program that fulfills this requirement.
        Use best practices, docstrings, and clear code structure.
        Organize the code into appropriate files and modules.
        Return a JSON object where keys are file paths and values are the file contents.
        Example format:
        {
            "main.py": "content of main.py",
            "utils/helpers.py": "content of helpers.py",
            "models/user.py": "content of user.py"
        }
        """
    ),
    "update_code": PromptTemplate(
        system_message="""You are an AI coding assistant. Modify the given code to fulfill the user story.
        Follow these guidelines:
        1. Preserve existing functionality
        2. Maintain code style consistency
        3. Add appropriate error handling
        4. Update docstrings and comments
        5. Only change what is necessary
        6. Return a JSON object mapping file paths to updated code content
        7. Create new files if needed for better code organization
        8. IMPORTANT: Your response must be a valid JSON object with string keys and values
        9. Do not include markdown code blocks or any other formatting
        10. The response should be in this exact format:
            {
                "file/path/one.py": "content of file one",
                "file/path/two.py": "content of file two"
            }""",
        user_template="""
        Existing codebase (JSON object mapping file paths to code):
        {existing_code}

        The user story is:
        {requirement}

        Please update the existing codebase to fulfill this requirement, preserving existing functionality.
        Only change what is necessary.
        Return a JSON object where keys are file paths and values are the updated file contents.
        You may create new files if needed for better code organization.
        Remember: Your response must be a valid JSON object without any markdown formatting.
        """
    )
}
