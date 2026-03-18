# ⊙ Contributing to RITUAL

Thank you for your interest in contributing to RITUAL! This guide will help you get started.

## Code of Conduct

Please be respectful and considerate of others. We follow the [Contributor Covenant](https://www.contributor-covenant.org/).

## How Can I Contribute?

### Reporting Bugs

1. Check if the bug has already been reported
2. Create a new issue with the `bug` label
3. Include detailed steps to reproduce
4. Add your system information

### Suggesting Features

1. Check existing issues and discussions
2. Create a new issue with the `enhancement` label
3. Describe the feature in detail
4. Explain why this would be useful

### Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Add tests if applicable
5. Ensure code passes linting
6. Commit with clear messages: `git commit -m 'Add amazing feature'`
7. Push to your fork: `git push origin feature/amazing-feature`
8. Open a Pull Request

## Development Setup

### Prerequisites

- Python 3.10+
- Git

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/ritual-lang/ritual.git
cd ritual

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements.txt[dev]

# Run tests
pytest

# Run in development mode
python -m src.backend.main
```

## Code Standards

### Python Style

We follow PEP 8 with some modifications:

- Line length: 100 characters max
- Use Black for formatting
- Use isort for import sorting
- Use flake8 for linting

### Commit Messages

Use clear, descriptive commit messages:

```
type(scope): description

[optional body]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Example:
```
feat(sigils): add API key encryption

Add Fernet encryption for storing API keys securely.
```

## Testing Requirements

- All new code must have tests
- Run tests before submitting: `pytest`
- Maintain code coverage above 80%

## Review Process

1. All submissions require review
2. Address feedback promptly
3. Keep changes focused and small

## Recognition

Contributors will be recognized in the README and on our website.

---

Thank you for contributing to RITUAL! 🔮
