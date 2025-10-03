# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This repository contains a Weather Simulator AR app built with Unity/C#, but the current working directory focuses on an Intelligent Code Review Assistant system. The `app/` directory contains a CI-only automated code review tool that runs entirely in GitHub Actions using:

- **Static Analysis**: Semgrep (multi-language) and Bandit (Python security)
- **AI Review**: Local Ollama LLM (qwen2.5-coder:7b-instruct) via LangChain
- **GitHub Integration**: Posts automated reviews on Pull Requests

## Architecture

The code review system follows a modular architecture:

```
app/
├── scripts/ci_review.py     # Main orchestration script
├── services/
│   ├── analyzers.py         # Static analysis runners (Semgrep, Bandit)
│   ├── diff_utils.py        # Diff processing utilities
│   └── llm.py              # LLM integration wrapper
├── prompts/reviewer_prompt.txt  # System prompt for code review
└── .github/workflows/review.yml # CI workflow definition
```

### Key Components

- **Main Script** (`ci_review.py`): Orchestrates the entire review process by fetching PR info, running static analysis, collecting diffs, and coordinating with the LLM
- **Static Analyzers** (`analyzers.py`): Wraps Semgrep and Bandit tools, handling their output formats and error states
- **LLM Service** (`llm.py`): Simple wrapper around Ollama for local AI inference
- **Diff Utils** (`diff_utils.py`): Handles diff truncation to fit within LLM context limits

### Key Constraints

- **Diff Budget**: Maximum 7000 characters total, 2000 per file
- **Static Analysis**: Limited to 25 findings per tool to prevent prompt overflow
- **Model Configuration**: Configurable via `LLM_MODEL` environment variable

## Development Commands

### Setup and Installation
```bash
# Install Python dependencies
pip install -r app/requirements.txt

# Install Ollama (if testing locally)
curl -fsSL https://ollama.com/install.sh | sh
ollama serve
ollama pull qwen2.5-coder:7b-instruct
```

### Running Static Analysis
```bash
# Run Semgrep analysis
semgrep --config auto --json --error .

# Run Bandit security analysis  
bandit -r . -f json -q
```

### Testing Components
```bash
# Test the main review script (requires GitHub environment variables)
python app/scripts/ci_review.py

# Test individual analyzers
python -c "from app.services.analyzers import run_semgrep; print(run_semgrep('.'))"
python -c "from app.services.analyzers import run_bandit; print(run_bandit('.'))"
```

### Workflow Testing
The GitHub workflow runs automatically on PR events. To test manually:
```bash
# Set required environment variables
export GITHUB_EVENT_PATH=/path/to/event.json
export GITHUB_TOKEN=your_token
export LLM_MODEL=qwen2.5-coder:7b-instruct

# Run the CI script
python app/scripts/ci_review.py
```

## Configuration

### Model Selection
Change the LLM model by setting the `LLM_MODEL` environment variable:
- `qwen2.5-coder:7b-instruct` (default)
- `codellama:7b-instruct`
- `starcoder2:7b`

### Extending Analysis
To add more linters:
1. Add dependencies to `requirements.txt`
2. Implement runner functions in `analyzers.py`
3. Update the summarization logic in `ci_review.py`
4. Modify the workflow in `.github/workflows/review.yml`

### Prompt Customization
Edit `app/prompts/reviewer_prompt.txt` to adjust review criteria and output format.

## Project Context

The main repository appears to be for a Weather Simulator AR app built with Unity and C#, but the active development is focused on the Python-based code review assistant in the `app/` directory. This creates an interesting hybrid structure where the repository serves dual purposes.