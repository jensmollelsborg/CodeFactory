import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template, abort
from db import init_db, save_to_db, fetch_all_stories, fetch_story_by_id
from code_gen_lib import generate_code_for_user_story, clean_code_block, generate_updated_code
from git_lib import clone_or_open_repo, create_unique_branch_and_push, create_pull_request, base_branch, parse_github_url

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)

def validate_user_story_input(data):
    """
    Validates the user story submission data.
    Returns (is_valid, error_message).
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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit_user_story():
    """
    1. Receives a user story (plus priority, notes, repository info).
    2. If 'repository' is recognized as a GitHub URL, it adapts an existing codebase.
       Otherwise, generate code from scratch.
    3. Saves code to the database and, if needed, commits changes.
    """
    # Validate input
    is_valid, error_message = validate_user_story_input(request.form)
    if not is_valid:
        return jsonify({"error": error_message}), 400
        
    user_story = request.form['userStory']
    priority = request.form['priority']
    notes = request.form.get('notes', '')
    repository_input = request.form.get('repository', '').strip()

    # Create a human-readable prompt or user story context
    full_prompt = f"User Story: {user_story}\nPriority: {priority}\nNotes: {notes}"

    # Determine if 'repository_input' is a GitHub URL
    if repository_input:
        try:
            if not (repository_input.startswith("http://") or 
                   repository_input.startswith("https://") or 
                   repository_input.startswith("git@")):
                return jsonify({"error": "Invalid repository URL format"}), 400
        except Exception as e:
            return jsonify({"error": "Invalid repository URL format"}), 400

        # ============== FLOW #1: ADAPT EXISTING REPO + CREATE PR ====================
        commit_message = "Adapt existing code for new user story"
        pr_branch = "feature/user-story-update"
        pr_title = f"User Story Update: {user_story[:30]}..."  # keep it short
        pr_body = f"Implements changes to fulfill user story:\n\n{user_story}\n\nPriority: {priority}\nNotes: {notes}"

        # Extract the remote repo name from the URL
        owner, remote_repo_name = parse_github_url(repository_input)
        
        # Use the parsed repo name for the local directory
        repo_name_local = remote_repo_name

        # 1. Clone/Open the repository (use the remote name)
        #    We’ll store it in repos/existing_repo
        repo, repo_path = clone_or_open_repo(repository_input, repo_name_local)

        # 2. Decide which file(s) to adapt. For example, "main.py"
        main_py_path = os.path.join(repo_path, "main.py")
        if not os.path.exists(main_py_path):
            # If there's no main.py, you might create one or choose a different file
            with open(main_py_path, "w", encoding="utf-8") as f:
                f.write("# main.py created\n")
        
        with open(main_py_path, "r", encoding="utf-8") as f:
            existing_code = f.read()

        # 3. Generate updated code
        updated_code = generate_updated_code(full_prompt, existing_code)
        updated_cleaned_code = clean_code_block(updated_code)

        # 4. Create a unique branch from 'main', commit & push
        branch_name = create_unique_branch_and_push(
            repo=repo,
            base_branch=base_branch,  # default branch
            file_path=main_py_path,
            updated_code=updated_cleaned_code,
            commit_message=commit_message
        )

        # 5. Create a Pull Request from that unique branch
        pr_url = create_pull_request(
            repo_url=repository_input,
            branch_name=branch_name,
            pr_title=pr_title,
            pr_body=pr_body,
            base_branch=base_branch
        )

        # 6. Save to the database (storing the updated code or path)
        save_to_db(user_story, priority, notes, updated_code)

        return render_template("confirmation.html",
                               pr_url=pr_url,
                               user_story=user_story,
                               priority=priority,
                               notes=notes)

    else:
        # -- FLOW #2: Generate code from scratch and store locally in repos/<repository_input> --

        # 1. Generate code
        generated_code = generate_code_for_user_story(full_prompt)
        cleaned_code = clean_code_block(generated_code)

        # 2. Create a local repository folder if not exists
        repo_dir = os.path.join(repo_dir, repository_input)
        os.makedirs(repo_dir, exist_ok=True)

        # 3. Save the code in "generated_code.py"
        file_path = os.path.join(repo_dir, "main.py")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(cleaned_code)

        # Optionally, you could also 'init' a local git repo here if you want
        # e.g., using GitPython: git.Repo.init(repo_dir), then commit_changes

        # 4. Save to the database
        save_to_db(user_story, priority, notes, generated_code)

        return render_template("confirmation.html",
                               pr_url=None,
                               user_story=user_story,
                               priority=priority,
                               notes=notes,
                               repository_folder=repository_input)

@app.route('/stories', methods=['GET'])
def view_stories():
    """
    Returns all user stories from the database in JSON format.
    """
    records = fetch_all_stories()
    return jsonify(records)

@app.route('/stories/<int:story_id>', methods=['GET'])
def view_story(story_id):
    """
    Returns a specific story by ID, or a 404 if it doesn't exist.
    """
    record = fetch_story_by_id(story_id)
    if record:
        return jsonify(record)
    return jsonify({"error": "Story not found"}), 404

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
