"""Server configuration."""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Server settings
HOST = os.getenv('SERVER_HOST', '0.0.0.0')  # Listen on all interfaces
PORT = int(os.getenv('SERVER_PORT', '5000'))
PUBLIC_URL = os.getenv('PUBLIC_URL', f'http://{HOST}:{PORT}')

# GitHub OAuth settings
GITHUB_CLIENT_ID = os.getenv('GITHUB_CLIENT_ID')
GITHUB_CLIENT_SECRET = os.getenv('GITHUB_CLIENT_SECRET')
GITHUB_CALLBACK_URL = os.getenv('GITHUB_CALLBACK_URL', f'{PUBLIC_URL}/auth/github/callback')
