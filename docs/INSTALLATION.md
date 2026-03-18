# ⊙ Installation Guide

This guide will help you install and set up RITUAL on your system.

## Prerequisites

- **Python 3.10 or higher** — Download from [python.org](https://www.python.org)
- **pip** — Comes with Python 3.10+

## Windows Installation

### Option 1: Quick Start

```cmd
# Clone the repository
git clone https://github.com/ritual-lang/ritual.git
cd ritual

# Install dependencies
pip install -r requirements.txt

# Run the server
python -m src.backend.main
```

### Option 2: Using setup.bat

```cmd
# Run the setup script
setup.bat

# Start the server
python -m src.backend.main
```

### Option 3: Using the executable

```cmd
# Run the pre-built executable (if available)
scripts\run.bat
```

## Linux/Mac Installation

```bash
# Clone the repository
git clone https://github.com/ritual-lang/ritual.git
cd ritual

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Mac: source venv/bin/activate
# On Linux: source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python -m src.backend.main
```

## Docker Installation (Optional)

```bash
# Build the Docker image
docker build -t ritual:latest .

# Run the container
docker run -p 8000:8000 ritual:latest
```

## Verification

After installation, verify RITUAL is running:

1. Open your browser to `http://localhost:8000`
2. You should see the RITUAL dashboard
3. Check the API at `http://localhost:8000/api/health`

## Troubleshooting

### Port Already in Use

If port 8000 is already in use, specify a different port:

```bash
python -m src.backend.main --port 8080
```

### Python Not Found

Make sure Python is in your PATH:

```cmd
# Check Python version
python --version

# If not found, add Python to PATH
# Or use full path to python.exe
```

### Module Not Found Errors

Reinstall dependencies:

```bash
pip install --upgrade -r requirements.txt
```

## Next Steps

- Read the [Usage Guide](USAGE.md) to learn how to use RITUAL
- Check [Configuration](CUSTOMIZATION.md) for customization options
