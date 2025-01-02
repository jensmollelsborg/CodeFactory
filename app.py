import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template

from db import init_db, save_to_db, fetch_all_stories, fetch_story_by_id, update_story, delete_story
from module2 import generate_code_for_user_story  # <--- Import your function

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

    # Combine user input into a prompt or direct string
    # (module2.generate_code_for_user_story can handle just the story, or the full details)
    prompt = f"User Story: {user_story}\nPriority: {priority}\nNotes: {notes}"

    # 1. Generate code using Module 2
    generated_code = generate_code_for_user_story(prompt)

    # 2. Save data to the database
    #    Here we store the 'generated_code' in place of the "actionable_items" column
    save_to_db(user_story, priority, notes, generated_code)

    # 3. Return JSON response
    return jsonify({
        "user_story": user_story,
        "priority": priority,
        "notes": notes,
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
