# ⊙ Architecture

This document describes the technical architecture of RITUAL.

## System Overview

RITUAL is built as a lightweight, local-first web application using Python (FastAPI) for the backend and vanilla HTML/CSS/JS for the frontend.

```
┌─────────────────────────────────────────────────────────┐
│                     RITUAL Portal                        │
├─────────────────────────────────────────────────────────┤
│  Frontend (HTML/CSS/JS)     │  Backend (FastAPI)       │
│  - Dashboard                │  - REST API               │
│  - Grimoire                 │  - LLM Discovery          │
│  - Sigils                   │  - Storage Manager        │
└─────────────────────────────────────────────────────────┘
                                │
                    ┌───────────┴───────────┐
                    │    External Services  │
                    │  - LM Studio          │
                    │  - MSTY               │
                    │  - OpenAI             │
                    └───────────────────────┘
```

## Components

### Backend (src/backend/)

| Module | Description |
|--------|-------------|
| `main.py` | Application entry point |
| `app/server.py` | FastAPI server setup |
| `app/config.py` | Configuration management |
| `app/storage.py` | Data persistence layer |
| `app/llm_discovery.py` | LLM provider discovery |

### Frontend (src/frontend/)

| File | Description |
|------|-------------|
| `index.html` | Main application page |
| `style.css` | Styling with mystical theme |
| `app.js` | Client-side application logic |

## API Endpoints

### Health Check

```
GET /api/health
```

Response:
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

### LLM Providers

```
GET /api/providers
```

Response:
```json
{
  "providers": [
    {"name": "lm-studio", "url": "http://localhost:1234"},
    {"name": "msty", "url": "http://localhost:9729"}
  ]
}
```

### MCM Files

```
GET /api/mcm-files
POST /api/mcm-files
DELETE /api/mcm-files/{id}
```

### API Keys (Sigils)

```
GET /api/sigils
POST /api/sigils
DELETE /api/sigils/{id}
```

## Data Storage

RITUAL uses JSON-based local storage:

- **Configuration:** `config/default-config.json`
- **MCM Files:** Stored in user data directory
- **API Keys:** Encrypted using `cryptography` library

## Security

### API Key Encryption

API keys are encrypted using Fernet (symmetric encryption):

```python
from cryptography.fernet import Fernet

# Generate key
key = Fernet.generate_key()
cipher = Fernet(key)

# Encrypt
encrypted = cipher.encrypt(api_key.encode())

# Decrypt
decrypted = cipher.decrypt(encrypted).decode()
```

## Extension Points

RITUAL can be extended through:

1. **Custom LLM Providers** — Implement the provider interface
2. **Theme Plugins** — Add custom CSS themes
3. **API Hooks** — Add middleware for logging, auth, etc.
