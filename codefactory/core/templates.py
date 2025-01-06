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
        7. Create new files if needed for better code organization""",
        user_template="""
        Existing codebase (JSON object mapping file paths to code):
        {existing_code}

        The user story is:
        {requirement}

        Please update the existing codebase to fulfill this requirement, preserving existing functionality.
        Only change what is necessary.
        Return a JSON object where keys are file paths and values are the updated file contents.
        You may create new files if needed for better code organization.
        """
    )
}

"""Templates for code generation prompts."""

# Base template for all code changes
BASE_TEMPLATE = """
You are tasked with implementing code changes based on the following request:

{user_story}

Context:
- Repository: {repo_name}
- Base Branch: {base_branch}
- Priority: {priority}
- Type: {change_type}
{additional_notes}

Please follow these guidelines:
1. Write clean, maintainable code
2. Follow the project's coding style
3. Include appropriate error handling
4. Add necessary tests
5. Update documentation as needed

Current codebase context:
{codebase_context}
"""

# Template for feature requests
FEATURE_REQUEST_TEMPLATE = """
{base_template}

Feature Implementation Guidelines:
1. Design the feature to be modular and extensible
2. Consider future maintenance and scalability
3. Add appropriate validation and error handling
4. Include user feedback mechanisms where appropriate
5. Document the new functionality
6. Add unit tests for the new feature
7. Consider performance implications

Expected Deliverables:
1. Implementation of the requested feature
2. Unit tests covering the new functionality
3. Documentation updates
4. API documentation if applicable
5. Migration scripts if needed
"""

# Template for refactoring requests
REFACTORING_TEMPLATE = """
{base_template}

Refactoring Guidelines:
1. Maintain existing functionality
2. Improve code readability and maintainability
3. Remove code duplication
4. Apply SOLID principles
5. Optimize performance where possible
6. Ensure all tests pass after changes
7. Document architectural decisions

Expected Deliverables:
1. Refactored code implementation
2. Updated or new unit tests
3. Performance benchmarks (before/after)
4. Documentation of architectural changes
5. Migration guide if needed
"""

# Template for bug fixes
BUGFIX_TEMPLATE = """
{base_template}

Bug Fix Guidelines:
1. Identify root cause of the issue
2. Add regression tests to prevent recurrence
3. Consider edge cases
4. Document the fix and its implications
5. Update error messages if applicable
6. Add logging for better debugging
7. Consider adding monitoring/alerts

Expected Deliverables:
1. Fixed implementation
2. Regression tests
3. Root cause analysis
4. Documentation updates
5. Monitoring improvements if needed
"""

def get_template(change_type: str, **kwargs) -> str:
    """Get the appropriate template based on the change type.
    
    Args:
        change_type: Type of change (feature, refactor, bugfix)
        **kwargs: Additional template parameters
    
    Returns:
        Formatted template string
    """
    # Format base template first
    base = BASE_TEMPLATE.format(
        change_type=change_type,
        **kwargs
    )
    
    # Select specific template based on change type
    template_map = {
        'feature': FEATURE_REQUEST_TEMPLATE,
        'refactor': REFACTORING_TEMPLATE,
        'bugfix': BUGFIX_TEMPLATE
    }
    
    template = template_map.get(change_type.lower(), FEATURE_REQUEST_TEMPLATE)
    
    # Format the full template
    return template.format(base_template=base)
