import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_code_for_user_story(user_story: str) -> str:
    """
    Generate Python code that fulfills the given user story or requirement.
    Uses OpenAI ChatCompletion (GPT-3.5 or GPT-4).
    :param user_story: The prompt describing the user's requirement.
    :return: A string containing the generated code.
    """
    system_message = (
        "You are an AI coding assistant. Produce Python code that fulfills the user's requirement."
    )

    user_message = f"""
    The user wants the following feature:
    {user_story}

    Write a Python program that fulfills this requirement.
    Use best practices, docstrings, and clear code structure.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # or "gpt-4" if you have access
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            max_tokens=400,
            temperature=0,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating code: {e}")
        return ""

def generate_code_for_actionable_items(actionable_items: str) -> str:
    """
    Generate code fulfilling the given actionable items using OpenAI's ChatCompletion endpoint.
    :param actionable_items: A string describing the tasks or requirements.
    :return: Generated Python code as a string.
    """

    system_message = (
        "You are an AI coding assistant. "
        "Please produce Python code that fulfills a set of actionable items."
    )
    user_message = f"""
    The following actionable items need to be implemented:
    {actionable_items}

    Write a Python program that fulfills these requirements.
    Use best practices, docstrings, and clear code structure.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # or "gpt-4"
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            max_tokens=300,
            temperature=0,
        )

        generated_code = response.choices[0].message.content.strip()
        return generated_code

    except Exception as e:
        print(f"Error generating code for actionable items: {e}")
        return ""

if __name__ == "__main__":
    # Example usage

    # Test with a user story
    user_story_example = (
        "As a user, I want to reset my password so that I can regain access to my account."
    )
    code_for_story = generate_code_for_user_story(user_story_example)
    print("Generated Code for User Story:\n", code_for_story, "\n")

    # Test with actionable items
    actionable_items_example = (
        "1. Add a Forgot Password link.\n"
        "2. Send a reset link to the user's email.\n"
        "3. Validate the token and allow the user to set a new password."
    )
    code_for_items = generate_code_for_actionable_items(actionable_items_example)
    print("Generated Code for Actionable Items:\n", code_for_items)
