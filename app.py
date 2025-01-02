import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template

from db import init_db, save_to_db, fetch_all_stories, fetch_story_by_id, update_story, delete_story
from code_gen_lib import generate_code_for_user_story, clean_code_block  # <--- Import your function

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')  # Render the HTML form

@app.route('/submit', methods=['POST'])
def submit_user_story():
    """
    Receives a user story (with priority and notes),
    generates code using module2.generate_code_for_user_story,
    saves it to the database, and returns the generated code.
    """
    user_story = request.form['userStory']
    priority = request.form['priority']
    notes = request.form.get('notes', '')
    repository_name = request.form['repository']  # New field

    # Combine user input into a prompt or direct string
    # (module2.generate_code_for_user_story can handle just the story, or the full details)
    prompt = f"User Story: {user_story}\nPriority: {priority}\nNotes: {notes}"

    # 1. Generate code using Module 2
    generated_code = generate_code_for_user_story(prompt)
    cleaned_code = clean_code_block(generated_code)

    # Step 2: Save the code in the specified repository directory
    repo_dir = os.path.join("repos", repository_name)
    os.makedirs(repo_dir, exist_ok=True)  # Create directory if not exists
    file_path = os.path.join(repo_dir, "generated_code.py")

    with open(file_path, "w", encoding="utf-8") as file:
        file.write(cleaned_code)

    # Step 3: Save data to the database (storing the generated code or path)
    # In this example, we store 'generated_code' in place of "actionable_items" column
    save_to_db(user_story, priority, notes, generated_code)

    return jsonify({
        "user_story": user_story,
        "priority": priority,
        "notes": notes,
        "repository": repository_name,
        "stored_file": file_path,
        "generated_code": generated_code
    })

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
