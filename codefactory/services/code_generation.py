"""Code generation service using OpenAI."""

import os
from typing import Optional
from dotenv import load_dotenv
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from ..core.exceptions import CodeGenerationError
from ..core.templates import TEMPLATES
from ..utils.logging import get_logger

# Load environment variables
load_dotenv()

# Setup logging
logger = get_logger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
openai_model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry_error_callback=lambda retry_state: None
)
def _make_openai_request(messages: list, max_tokens: int = 400) -> Optional[str]:
    """
    Makes an OpenAI API request with retry mechanism.
    
    Args:
        messages: List of message dictionaries for the chat completion
        max_tokens: Maximum tokens for the response
        
    Returns:
        Generated text or None if all retries fail
        
    Raises:
        CodeGenerationError: If the API request fails after all retries
    """
    try:
        response = client.chat.completions.create(
            model=openai_model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"OpenAI API request failed: {str(e)}")
        return None

def _generate_code_with_template(
    template_name: str,
    requirement: str,
    existing_code: Optional[str] = None,
    max_tokens: int = 400
) -> str:
    """
    Generic function to generate code using a template.
    
    Args:
        template_name: Name of the template to use
        requirement: The user story or requirement
        existing_code: Optional existing code for updates
        max_tokens: Maximum tokens for the response
        
    Returns:
        Generated code
        
    Raises:
        CodeGenerationError: If code generation fails
    """
    template = TEMPLATES[template_name]
    format_args = {"requirement": requirement}
    if existing_code is not None:
        format_args["existing_code"] = existing_code
    
    formatted = template.format(**format_args)
    
    messages = [
        {"role": "system", "content": formatted["system"]},
        {"role": "user", "content": formatted["user"]}
    ]
    
    try:
        generated_code = _make_openai_request(messages, max_tokens)
        if not generated_code:
            raise CodeGenerationError(f"Failed to generate code using template {template_name}")
        return generated_code
    except Exception as e:
        error_msg = f"Error generating code with template {template_name}: {str(e)}"
        logger.error(error_msg)
        raise CodeGenerationError(error_msg)

def generate_code_for_user_story(user_story: str) -> str:
    """Generate code for a user story."""
    return _generate_code_with_template("generate_code", user_story)

def generate_code_for_actionable_items(actionable_items: str) -> str:
    """Generate code for actionable items."""
    return _generate_code_with_template("generate_code", actionable_items)

def generate_updated_code(user_story: str, existing_code: str) -> str:
    """Generate updated code based on existing code and user story."""
    return _generate_code_with_template(
        "update_code",
        user_story,
        existing_code=existing_code,
        max_tokens=2000
    )

def clean_code_block(generated_code: str) -> str:
    """
    Clean generated code by removing markdown formatting.
    
    Args:
        generated_code: Raw generated code that might contain markdown
        
    Returns:
        Cleaned code without markdown formatting
    """
    if not generated_code:
        return ""
        
    code = generated_code.strip()

    # Remove any leading triple backticks and optional language spec
    if code.startswith("```"):
        lines = code.split("\n")
        lines = lines[1:]  # Drop the first line
        code = "\n".join(lines)

    # Remove any trailing triple backticks
    if code.endswith("```"):
        code = code.rsplit("```", 1)[0].strip()

    return code

def validate_generated_code(code: str) -> bool:
    """
    Validate generated code for basic Python syntax.
    
    Args:
        code: Generated code to validate
        
    Returns:
        True if code is valid Python, False otherwise
    """
    try:
        compile(code, "<string>", "exec")
        return True
    except SyntaxError:
        return False

def refactor_code(code: str, refactoring_goals: str) -> str:
    """
    Refactor existing code based on specified goals.
    
    Args:
        code: Existing code to refactor
        refactoring_goals: Description of refactoring goals
        
    Returns:
        Refactored code
        
    Raises:
        CodeGenerationError: If refactoring fails
    """
    generated = _generate_code_with_template(
        "refactor_code",
        refactoring_goals,
        existing_code=code,
        max_tokens=2000
    )
    
    cleaned = clean_code_block(generated)
    if not validate_generated_code(cleaned):
        raise CodeGenerationError("Generated code contains syntax errors")
    
    return cleaned

def fix_bug(code: str, bug_description: str) -> str:
    """
    Fix bugs in existing code.
    
    Args:
        code: Code containing the bug
        bug_description: Description of the bug to fix
        
    Returns:
        Fixed code
        
    Raises:
        CodeGenerationError: If bug fixing fails
    """
    generated = _generate_code_with_template(
        "fix_bug",
        bug_description,
        existing_code=code,
        max_tokens=2000
    )
    
    cleaned = clean_code_block(generated)
    if not validate_generated_code(cleaned):
        raise CodeGenerationError("Generated code contains syntax errors")
    
    return cleaned
