# CodeFactory 🏭

CodeFactory is an AI-powered code generation service that can create new code or adapt existing codebases based on user stories. It leverages OpenAI's GPT models to understand requirements and generate appropriate code solutions.

## Features

- 🤖 AI-powered code generation using OpenAI GPT models
- 🔄 Adapt existing GitHub repositories based on new requirements
- 🌟 Create new codebases from scratch
- 🔀 Automatic PR creation with generated changes
- 📝 User story management and tracking
- 🎯 Priority-based development
- 🔍 Debug mode for inspecting AI prompts

## Prerequisites

- Python 3.8+
- GitHub account and personal access token
- OpenAI API key

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/codefactory.git
cd codefactory
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy the example environment file and fill in your values:
```bash
cp .env.example .env
```

## Configuration

Edit `.env` with your settings:

```env
OPENAI_API_KEY=<your-openai-api-key>
GITHUB_TOKEN=<your-github-token>
REPO_DIR="<your-repo-dir>"
BASE_BRANCH="main"
OPENAI_MODEL="gpt-4"
DEBUG_PROMPTS=false
```

- `OPENAI_API_KEY`: Your OpenAI API key
- `GITHUB_TOKEN`: GitHub personal access token with repo permissions
- `REPO_DIR`: Directory where repositories will be cloned
- `BASE_BRANCH`: Default branch for repositories (usually "main" or "master")
- `OPENAI_MODEL`: OpenAI model to use (e.g., "gpt-4" or "gpt-3.5-turbo")
- `DEBUG_PROMPTS`: Set to "true" to export AI prompts for debugging

## Usage

1. Start the server:
```bash
python app.py
```

2. Open your browser to `http://localhost:5000`

3. Submit a user story with:
   - Description of the feature/change
   - Priority level
   - Additional notes
   - GitHub repository URL (if adapting existing code)

4. The system will:
   - Generate or update code based on your requirements
   - Create a new branch
   - Commit the changes
   - Create a pull request
   - Save the user story for tracking

## Project Structure

```
codefactory/
├── core/
│   ├── exceptions.py    # Custom exceptions
│   └── templates.py     # AI prompt templates
├── services/
│   ├── code_generation.py  # OpenAI integration
│   ├── git_operations.py   # Git/GitHub operations
│   └── database.py         # Story storage
├── utils/
│   ├── logging.py      # Logging configuration
│   └── validation.py   # Input validation
└── templates/          # HTML templates
```

## Debugging

Enable prompt debugging by setting `DEBUG_PROMPTS=true` in your `.env` file. Debug files will be created in `{REPO_DIR}/debug/` with the following format:
```
openai_messages_{template_name}_{timestamp}.txt
```

These files contain:
- Template name
- Timestamp
- System message
- User message

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Acknowledgments

- OpenAI for their powerful GPT models
- GitHub for repository hosting and API
- Flask framework for web services
