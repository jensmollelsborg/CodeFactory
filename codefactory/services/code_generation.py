"""Code generation service supporting both OpenAI and Ollama."""

import os
import json
from datetime import datetime
from typing import Optional, Dict, Union
import requests
from abc import ABC, abstractmethod
from dotenv import load_dotenv

from ..core.exceptions import CodeGenerationError
from ..core.templates import TEMPLATES
from ..utils.logging import get_logger

# Setup logging
logger = get_logger(__name__)

# Debug flag - can be enabled via environment variable
DEBUG_PROMPTS = os.getenv("DEBUG_PROMPTS", "").lower() == "true"

class ModelProvider(ABC):
    @abstractmethod
    def generate_completion(self, messages: list) -> str:
        """Generate completion from messages."""
        pass

class OpenAIProvider(ModelProvider):
    def __init__(self):
        from openai import OpenAI
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4")

    def generate_completion(self, messages: list) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.1
            )
            return response.choices[0].message.content
        except Exception as e:
            raise CodeGenerationError(f"OpenAI API error: {str(e)}")

class OllamaProvider(ModelProvider):
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "codellama")

    def generate_completion(self, messages: list) -> str:
        try:
            # Convert chat messages to Ollama format
            prompt = self._convert_messages_to_prompt(messages)
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.1
                }
            )
            response.raise_for_status()
            return response.json()["response"]
        except Exception as e:
            raise CodeGenerationError(f"Ollama API error: {str(e)}")

    def _convert_messages_to_prompt(self, messages: list) -> str:
        """Convert ChatML format messages to a single prompt string."""
        prompt_parts = []
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                prompt_parts.append(f"Instructions: {content}\n")
            elif role == "user":
                prompt_parts.append(f"User: {content}\n")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}\n")
                
        return "\n".join(prompt_parts)

def get_model_provider() -> ModelProvider:
    """Factory function to get the configured model provider."""
    provider = os.getenv("MODEL_PROVIDER", "openai").lower()
    
    if provider == "openai":
        return OpenAIProvider()
    elif provider == "ollama":
        return OllamaProvider()
    else:
        raise ValueError(f"Unsupported model provider: {provider}")

def _export_messages_for_debug(messages: list, template_name: str) -> None:
    """Export messages to a debug file for inspection."""
    if not DEBUG_PROMPTS:
        return
        
    debug_dir = os.path.join(os.getenv("REPO_DIR", "repos"), "debug")
    os.makedirs(debug_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    debug_file = os.path.join(debug_dir, f"model_messages_{template_name}_{timestamp}.txt")
    
    with open(debug_file, "w", encoding="utf-8") as f:
        f.write(f"Template: {template_name}\n")
        f.write(f"Timestamp: {timestamp}\n")
        f.write("-" * 80 + "\n\n")
        
        for msg in messages:
            f.write(f"Role: {msg['role']}\n")
            f.write("-" * 40 + "\n")
            f.write(msg['content'])
            f.write("\n" + "=" * 80 + "\n\n")

def generate_code(template_name: str, **kwargs) -> str:
    """
    Generate code using the specified template and model provider.
    
    Args:
        template_name: Name of the template to use
        **kwargs: Template variables
        
    Returns:
        Generated code or content
        
    Raises:
        CodeGenerationError: If code generation fails
    """
    try:
        template = TEMPLATES.get(template_name)
        if not template:
            raise CodeGenerationError(f"Template not found: {template_name}")
            
        # Prepare messages
        messages = [
            {"role": "system", "content": template.system_message}
        ]
        
        # Add user message with template
        user_message = template.user_template.format(**kwargs)
        messages.append({"role": "user", "content": user_message})
        
        # Export messages for debugging if enabled
        _export_messages_for_debug(messages, template_name)
        
        # Get configured provider and generate completion
        provider = get_model_provider()
        logger.info(f"Using model provider: {provider.__class__.__name__}")
        
        response = provider.generate_completion(messages)
        
        # For code generation templates, try to parse as JSON
        if template_name in ["generate_code", "update_code"]:
            try:
                return json.loads(response)
            except json.JSONDecodeError as e:
                raise CodeGenerationError(f"Failed to parse response as JSON: {str(e)}")
        
        return response
        
    except Exception as e:
        raise CodeGenerationError(f"Code generation failed: {str(e)}")

def generate_code_for_user_story(user_story: str) -> Dict[str, str]:
    """
    Generate code for a user story.
    
    Returns:
        Dictionary mapping file paths to generated code
    """
    return generate_code("generate_code", requirement=user_story)

def generate_updated_code(user_story: str, existing_code: Dict[str, str]) -> Dict[str, str]:
    """
    Generate updated code based on existing code and user story.
    
    Args:
        user_story: The user story to implement
        existing_code: Dictionary mapping file paths to their current contents
        
    Returns:
        Dictionary mapping file paths to updated code
    """
    return generate_code("update_code", requirement=user_story, existing_code=existing_code)

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
