import os
from dotenv import load_dotenv
from openai import OpenAI
from flask import Flask, request, jsonify, render_template
from db import init_db, save_to_db, fetch_all_stories, fetch_story_by_id, update_story, delete_story

# Load environment variables from .env
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Get the OpenAI API key

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')  # Render the HTML form

@app.route('/submit', methods=['POST'])
def submit_user_story():
    user_story = request.form['userStory']
    priority = request.form['priority']
    notes = request.form.get('notes', '')

    # Process user story with OpenAI API
    response = client.chat.completions.create(model="gpt-4",
    messages=[
        {"role": "system", "content": "You are an assistant that processes user stories into actionable items."},
        {"role": "user", "content": f"User Story: {user_story}\nPriority: {priority}\nNotes: {notes}"}
    ])

    actionable_items = response.choices[0].message.content

    # Save data to the database
    save_to_db(user_story, priority, notes, actionable_items)

    return jsonify({
        "user_story": user_story,
        "priority": priority,
        "notes": notes,
        "actionable_items": actionable_items
    })

@app.route('/stories', methods=['GET'])
def view_stories():
    records = fetch_all_stories()
    return jsonify(records)  # Return all stories as JSON

@app.route('/stories/<int:story_id>', methods=['GET'])
def view_story(story_id):
    record = fetch_story_by_id(story_id)
    if record:
        return jsonify(record)
    return jsonify({"error": "Story not found"}), 404

if __name__ == '__main__':
    init_db()
    app.run(debug=True)

