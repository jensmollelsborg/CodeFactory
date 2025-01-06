"""Main application entry point."""

import os
from flask import (
    Flask, 
    render_template, 
    request, 
    jsonify, 
    redirect, 
    url_for,
    session
)
from flask_session import Session
from werkzeug.exceptions import HTTPException
from dotenv import load_dotenv
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern
from datetime import timedelta

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
from codefactory.services.auth import (
    get_github_oauth,
    login_required,
    get_github_token,
    is_authenticated,
    clear_auth,
    GITHUB_AUTHORIZE_URL,
    GITHUB_TOKEN_URL,
    GITHUB_CLIENT_SECRET
)
from codefactory.utils.validation import validate_user_story_input
from codefactory.utils.logging import setup_logging, get_logger

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Server configuration
HOST = os.getenv('SERVER_HOST', '0.0.0.0')
PORT = int(os.getenv('SERVER_PORT', '5000'))
PUBLIC_URL = os.getenv('PUBLIC_URL', f'http://{HOST}:{PORT}')

# Configure server-side session
app.config['SECRET_KEY'] = os.getenv('SESSION_SECRET', 'dev-secret-key')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = os.path.join(os.path.dirname(__file__), 'flask_session')
app.config['SESSION_PERMANENT'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

# Ensure session directory exists
os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)

# Initialize session
Session(app)

# Setup logging
setup_logging()
logger = get_logger(__name__)

@app.route('/')
def index():
    """Render the main page."""
    authenticated = is_authenticated()
    user = session.get('github_user', {}) if authenticated else None
    return render_template('index.html', 
                         authenticated=authenticated,
                         user=user)

@app.route('/auth/github')
def github_login():
    """Initiate GitHub OAuth login."""
    try:
        github = get_github_oauth()
        authorization_url, state = github.authorization_url(GITHUB_AUTHORIZE_URL)
        session['oauth_state'] = state
        return redirect(authorization_url)
    except Exception as e:
        logger.error(f"Failed to initiate GitHub login: {str(e)}")
        return render_template('index.html', 
                             error="Failed to initiate GitHub login. Please check your configuration.",
                             authenticated=False)

@app.route('/auth/github/callback')
def github_callback():
    """Handle GitHub OAuth callback."""
    logger.info("Received GitHub callback")
    logger.debug(f"Callback args: {request.args}")

    if 'error' in request.args:
        error_msg = request.args.get('error_description', request.args['error'])
        logger.error(f"GitHub OAuth error: {error_msg}")
        return render_template('index.html', 
                             error=f"GitHub authentication failed: {error_msg}",
                             authenticated=False)

    try:
        if 'code' not in request.args:
            logger.error("No code in callback")
            return render_template('index.html',
                                error="No authentication code received",
                                authenticated=False)

        github = get_github_oauth()
        
        # Get the full callback URL
        callback_url = request.url
        if request.url.startswith('http://') and 'https://' in os.getenv('GITHUB_CALLBACK_URL', ''):
            callback_url = request.url.replace('http://', 'https://', 1)
        
        logger.info("Fetching GitHub token")
        token = github.fetch_token(
            GITHUB_TOKEN_URL,
            client_secret=GITHUB_CLIENT_SECRET,
            authorization_response=callback_url,
            verify=False  # For local development only
        )
        
        logger.info("Token received, setting session")
        session['github_token'] = token
        
        # Get user info
        logger.info("Fetching user info")
        user_response = github.get('https://api.github.com/user')
        if user_response.ok:
            user_data = user_response.json()
            session['github_user'] = user_data
            logger.info(f"Successfully authenticated user: {user_data.get('login')}")
        else:
            logger.warning(f"Failed to fetch user data: {user_response.status_code} - {user_response.text}")
        
        return redirect(url_for('index'))
        
    except Exception as e:
        logger.exception("Failed to complete GitHub authentication")
        return render_template('index.html', 
                             error=f"Authentication error: {str(e)}",
                             authenticated=False)

@app.route('/auth/logout')
def logout():
    """Log out user."""
    clear_auth()
    return redirect(url_for('index'))

@app.route('/submit', methods=['POST'])
@login_required
def submit():
    """Handle user story submission."""
    try:
        user_story = request.form.get('userStory')
        priority = request.form.get('priority')
        notes = request.form.get('notes', '')
        repository = request.form.get('repository')
        change_type = request.form.get('changeType')

        if not all([user_story, priority, repository, change_type]):
            return render_template('index.html', 
                                error="All fields are required",
                                authenticated=True,
                                user=session.get('github_user'))

        # Get the GitHub token from session
        github_token = session.get('github_token', {}).get('access_token')
        if not github_token:
            return render_template('index.html',
                                error="GitHub authentication required",
                                authenticated=False)

        # Initialize the code generator with the GitHub token
        code_generator = CodeGenerator(
            github_token=github_token,
            repo_name=repository,
            base_branch=os.getenv('BASE_BRANCH', 'main')
        )

        # Generate code changes
        changes = code_generator.generate_changes(
            user_story=user_story,
            priority=priority,
            additional_notes=notes,
            change_type=change_type
        )

        return jsonify({"message": "Changes generated successfully", "changes": changes})

    except Exception as e:
        logger.exception("Failed to process user story")
        return render_template('index.html',
                             error=f"Failed to process request: {str(e)}",
                             authenticated=True,
                             user=session.get('github_user'))

@app.route('/api/repositories')
@login_required
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
    # Create SSL context for HTTPS
    ssl_context = ('cert.pem', 'key.pem')
    app.run(host=HOST, port=PORT, debug=True, ssl_context=ssl_context)
