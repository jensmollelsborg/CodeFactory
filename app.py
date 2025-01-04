"""Main application entry point."""

import os
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern

from codefactory.core.exceptions import CodeGenerationError, GitOperationError, DatabaseError
from codefactory.services.code_generation import (
    generate_code_for_user_story,
    generate_updated_code,
    clean_code_block
)
from codefactory.services.git_operations import (
    parse_github_url,
    clone_or_open_repo,
    create_unique_branch_and_push,
    create_pull_request,
    get_user_repositories
)
from codefactory.services.database import init_db, save_to_db, fetch_all_stories, fetch_story_by_id
from codefactory.utils.validation import validate_user_story_input
from codefactory.utils.logging import setup_logging, get_logger

# Load environment variables
load_dotenv()

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Initialize Flask app
app = Flask(__name__)

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit_user_story():
    """
    Handle user story submission.
    
    1. Receives a user story (plus priority, notes, repository info).
    2. If 'repository' is recognized as a GitHub URL, it adapts an existing codebase.
       Otherwise, generate code from scratch.
    3. Saves code to the database and, if needed, commits changes.
    """
    try:
        # Validate input
        is_valid, error_message = validate_user_story_input(request.form)
        if not is_valid:
            return jsonify({"error": error_message}), 400
            
        user_story = request.form['userStory']
        priority = request.form['priority']
        notes = request.form.get('notes', '')
        repository_input = request.form.get('repository', '').strip()

        # Create a human-readable prompt
        full_prompt = f"User Story: {user_story}\nPriority: {priority}\nNotes: {notes}"

        if repository_input:
            try:
                # Process existing repository
                return process_existing_repo(
                    repository_input,
                    user_story,
                    priority,
                    notes,
                    full_prompt
                )
            except (GitOperationError, CodeGenerationError) as e:
                return jsonify({"error": str(e)}), 500
            except Exception as e:
                logger.error(f"Repository operation failed: {str(e)}")
                return jsonify({"error": "Repository operation failed"}), 500
        else:
            try:
                # Generate new code
                return generate_new_code(
                    user_story,
                    priority,
                    notes,
                    full_prompt
                )
            except CodeGenerationError as e:
                return jsonify({"error": str(e)}), 500
            except Exception as e:
                logger.error(f"Code generation failed: {str(e)}")
                return jsonify({"error": "Code generation failed"}), 500

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500

def process_existing_repo(
    repository_input: str,
    user_story: str,
    priority: str,
    notes: str,
    full_prompt: str
) -> str:
    """Process an existing repository for code updates."""
    # Extract repository information
    owner, remote_repo_name = parse_github_url(repository_input)
    repo_name_local = remote_repo_name

    # Setup commit and PR information
    commit_message = "Adapt existing code for new user story"
    pr_title = f"User Story Update: {user_story[:30]}..."
    pr_body = f"Implements changes to fulfill user story:\n\n{user_story}\n\nPriority: {priority}\nNotes: {notes}"

    # Clone/Open the repository
    repo, repo_path = clone_or_open_repo(repository_input, repo_name_local)

    # Load .gitignore patterns if present
    gitignore_path = os.path.join(repo_path, '.gitignore')
    ignore_spec = None
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r') as f:
            ignore_patterns = f.read().splitlines()
        ignore_spec = PathSpec.from_lines(GitWildMatchPattern, ignore_patterns)

    # Read the existing codebase
    codebase = {}
    for root, _, files in os.walk(repo_path):
        for file in files:
            if not file.endswith('.py'):  # Only process Python files for now
                continue
                
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, repo_path)
            
            # Skip if file matches gitignore patterns
            if ignore_spec and ignore_spec.match_file(rel_path):
                logger.debug(f"Skipping ignored file: {rel_path}")
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    codebase[rel_path] = f.read()
            except Exception as e:
                logger.warning(f"Failed to read file {rel_path}: {str(e)}")
                continue

    # Generate and clean the updated code
    updated_codebase = generate_updated_code(full_prompt, codebase)
    
    # Apply updates to files
    for rel_path, updated_code in updated_codebase.items():
        file_path = os.path.join(repo_path, rel_path)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(clean_code_block(updated_code))

        # Create branch and push each file
        branch_name = create_unique_branch_and_push(
            repo=repo,
            base_branch=os.getenv("BASE_BRANCH", "main"),
            file_path=file_path,
            updated_code=clean_code_block(updated_code),
            commit_message=commit_message
        )

    # Create pull request
    pr_url = create_pull_request(
        repo_url=repository_input,
        branch_name=branch_name,
        pr_title=pr_title,
        pr_body=pr_body
    )

    # Save to database
    try:
        save_to_db(user_story, priority, notes, str(updated_codebase))
    except DatabaseError as e:
        logger.error(f"Database save failed: {str(e)}")
        # Continue even if database save fails

    return render_template(
        "confirmation.html",
        pr_url=pr_url,
        user_story=user_story,
        priority=priority,
        notes=notes
    )

def generate_new_code(
    user_story: str,
    priority: str,
    notes: str,
    full_prompt: str
) -> str:
    """Generate new code from scratch with proper project structure."""
    # Generate the code with multiple files
    generated_codebase = generate_code_for_user_story(full_prompt)
    
    # Create output directory
    output_dir = os.path.join(os.getenv("REPO_DIR", "repos"), "generated")
    os.makedirs(output_dir, exist_ok=True)

    # Save the generated code files
    for rel_path, code in generated_codebase.items():
        file_path = os.path.join(output_dir, rel_path)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(clean_code_block(code))

    # Save to database
    try:
        save_to_db(user_story, priority, notes, str(generated_codebase))
    except DatabaseError as e:
        logger.error(f"Database save failed: {str(e)}")
        # Continue even if database save fails

    return render_template(
        "confirmation.html",
        pr_url=None,
        user_story=user_story,
        priority=priority,
        notes=notes,
        repository_folder="generated"
    )

@app.route('/api/repositories')
def get_repositories():
    """Get list of GitHub repositories accessible to the user."""
    try:
        repositories = get_user_repositories()
        return jsonify({"repositories": repositories})
    except GitOperationError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Unexpected error fetching repositories: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/stories', methods=['GET'])
def view_stories():
    """Return all user stories."""
    try:
        records = fetch_all_stories()
        return jsonify(records)
    except DatabaseError as e:
        return jsonify({"error": str(e)}), 500

@app.route('/stories/<int:story_id>', methods=['GET'])
def view_story(story_id):
    """Return a specific story by ID."""
    try:
        record = fetch_story_by_id(story_id)
        if record:
            return jsonify(record)
        return jsonify({"error": "Story not found"}), 404
    except DatabaseError as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
