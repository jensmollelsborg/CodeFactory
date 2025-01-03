"""Code generation service using OpenAI."""

import os
import json
from datetime import datetime
from typing import Optional, Dict, Union
from dotenv import load_dotenv
from openai import OpenAI

from ..core.exceptions import CodeGenerationError
from ..core.templates import TEMPLATES
from ..utils.logging import get_logger

# Setup logging
logger = get_logger(__name__)

# Initialize OpenAI client lazily
_client = None
_model = None

# Debug flag - can be enabled via environment variable
DEBUG_PROMPTS = os.getenv("DEBUG_PROMPTS", "").lower() == "true"

def _export_messages_for_debug(messages: list, template_name: str) -> None:
    """
    Export messages to a debug file for inspection.
    Only exports if DEBUG_PROMPTS is True.
    
    Args:
        messages: List of message dictionaries
        template_name: Name of the template used
    """
    if not DEBUG_PROMPTS:
        return
        
    debug_dir = os.path.join(os.getenv("REPO_DIR", "repos"), "debug")
    os.makedirs(debug_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    debug_file = os.path.join(debug_dir, f"openai_messages_{template_name}_{timestamp}.txt")
    
    with open(debug_file, "w", encoding="utf-8") as f:
        f.write(f"Template: {template_name}\n")
        f.write(f"Timestamp: {timestamp}\n")
        f.write("-" * 80 + "\n\n")
        
        for msg in messages:
            f.write(f"Role: {msg['role']}\n")
            f.write("-" * 40 + "\n")
            f.write(msg['content'])
            f.write("\n" + "=" * 80 + "\n\n")

def get_openai_client():
    """Get or create OpenAI client with current environment settings."""
    global _client, _model
    if _client is None:
        # Load environment variables
        load_dotenv()
        _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        _model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    return _client, _model

def _make_openai_request(messages: list, max_tokens: int = 1000) -> str:
    """
    Makes an OpenAI API request.
    
    Args:
        messages: List of message dictionaries for the chat completion
        max_tokens: Maximum tokens for the response
        
    Returns:
        Generated text
        
    Raises:
        CodeGenerationError: If the API request fails
    """
    try:
        client, model = get_openai_client()
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"OpenAI API request failed: {str(e)}")
        raise CodeGenerationError(f"Failed to generate code: {str(e)}")

def _generate_code_with_template(
    template_name: str,
    requirement: str,
    existing_code: Optional[Union[str, Dict[str, str]]] = None,
    max_tokens: int = 1000
) -> Dict[str, str]:
    """
    Generic function to generate code using a template.
    
    Args:
        template_name: Name of the template to use
        requirement: The user story or requirement
        existing_code: Optional existing code for updates
        max_tokens: Maximum tokens for the response
        
    Returns:
        Dictionary mapping file paths to generated code
        
    Raises:
        CodeGenerationError: If code generation fails
    """
    template = TEMPLATES[template_name]
    format_args = {"requirement": requirement}
    
    # Handle existing code format
    if existing_code is not None:
        if isinstance(existing_code, str):
            existing_code = {"main.py": existing_code}
        format_args["existing_code"] = json.dumps(existing_code, indent=2)
    
    formatted = template.format(**format_args)
    messages = [
        {"role": "system", "content": formatted["system"]},
        {"role": "user", "content": formatted["user"]}
    ]
    
    # Export messages for debugging
    _export_messages_for_debug(messages, template_name)
    
    result = _make_openai_request(messages, max_tokens)
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse generated code: {result[:100]}...")
        raise CodeGenerationError("Generated code is not valid JSON")

def generate_code_for_user_story(user_story: str) -> Dict[str, str]:
    """
    Generate code for a user story.
    
    Returns:
        Dictionary mapping file paths to generated code
    """
    return _generate_code_with_template("generate_code", user_story)

def generate_updated_code(user_story: str, existing_code: Dict[str, str]) -> Dict[str, str]:
    """
    Generate updated code based on existing code and user story.
    
    Args:
        user_story: The user story to implement
        existing_code: Dictionary mapping file paths to their current contents
        
    Returns:
        Dictionary mapping file paths to updated code
    """
    return _generate_code_with_template("update_code", user_story, existing_code)

def clean_code_block(generated_code: str) -> str:
    """
    Clean generated code by removing markdown formatting.
    
    Args:
        generated_code: Raw generated code that might contain markdown
        
    Returns:
        Cleaned code without markdown formatting
    """
    # Remove markdown code block markers if present
    code = generated_code.strip()
    if code.startswith("```") and code.endswith("```"):
        # Remove first line (```python or similar)
        first_newline = code.find('\n')
        if first_newline != -1:
            code = code[first_newline + 1:]
        # Remove last line (```)
        code = code[:-3].strip()
    return code
