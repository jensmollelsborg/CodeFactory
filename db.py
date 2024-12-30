import sqlite3

def init_db():
    """Initialize the database and create the user_stories table."""
    conn = sqlite3.connect('user_stories.db')  # Connect to the database file
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_stories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_story TEXT,
            priority TEXT,
            notes TEXT,
            actionable_items TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_to_db(user_story, priority, notes, actionable_items):
    """Save a user story and its details to the database."""
    conn = sqlite3.connect('user_stories.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO user_stories (user_story, priority, notes, actionable_items)
        VALUES (?, ?, ?, ?)
    ''', (user_story, priority, notes, actionable_items))
    conn.commit()
    conn.close()

def fetch_all_stories():
    """Fetch all user stories from the database."""
    conn = sqlite3.connect('user_stories.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM user_stories')
    records = cursor.fetchall()
    conn.close()
    return records

def fetch_story_by_id(story_id):
    """Fetch a specific user story by its ID."""
    conn = sqlite3.connect('user_stories.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM user_stories WHERE id = ?', (story_id,))
    record = cursor.fetchone()
    conn.close()
    return record

def update_story(story_id, user_story, priority, notes, actionable_items):
    """Update a user story's details."""
    conn = sqlite3.connect('user_stories.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE user_stories
        SET user_story = ?, priority = ?, notes = ?, actionable_items = ?
        WHERE id = ?
    ''', (user_story, priority, notes, actionable_items, story_id))
    conn.commit()
    conn.close()

def delete_story(story_id):
    """Delete a user story by its ID."""
    conn = sqlite3.connect('user_stories.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM user_stories WHERE id = ?', (story_id,))
    conn.commit()
    conn.close()

# Example usage (comment out or remove in production)
if __name__ == "__main__":
    # Initialize the database
    init_db()

    # Example operations
    save_to_db("As a user, I want to reset my password.", "High", "Ensure security measures.", "1. Add forgot password feature. 2. Send reset email.")
    print("All Stories:", fetch_all_stories())
    print("Story by ID:", fetch_story_by_id(1))

    update_story(1, "As a user, I want to change my password.", "Medium", "Ensure ease of use.", "1. Add password change feature.")
    print("Updated Story:", fetch_story_by_id(1))

    delete_story(1)
    print("All Stories After Deletion:", fetch_all_stories())
