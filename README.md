# RITUAL

**4-Tier MCP Memory Portal** — A clean, minimal interface for managing LLM context and memory systems.

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/fastapi-0.104-green.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT">
</p>

## Overview

RITUAL is a local web portal for managing a 4-tier MCP (Model Context Protocol) memory system. It provides:

- **Dashboard** — Overview of memory stats across all tiers
- **Memory Management** — Create, edit, delete memory entries
- **API Key Storage** — Secure encrypted storage for provider keys
- **Model Discovery** — Browse and manage available models

### Architecture

```
┌─────────────────────────────────────────────┐
│              RITUAL Portal                   │
├──────────┬──────────┬──────────┬────────────┤
│ Tier 0   │ Tier 1   │ Tier 2   │ Tier 3     │
│Personality│ Context │ Frequent │ Archive    │
└──────────┴──────────┴──────────┴────────────┘
                    │
              MCP Server ← LLM Applications
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python src/backend/main.py

# Open browser
# http://localhost:8765
```

### Docker

```bash
docker-compose up -d
```

### Windows Executable

```bash
python build_exe.py
# Run: dist/RITUAL.exe
# Or: run_ritual.bat
```

## Configuration

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `PORT` | Server port | `8765` |
| `GITHUB_CLIENT_ID` | GitHub OAuth client ID | — |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth secret | — |
| `ENCRYPTION_KEY` | 32-byte key for API key encryption | auto-generated |
| `DATA_DIR` | Storage directory | `./data` |

## Project Structure

```
ritual/
├── src/
│   ├── backend/
│   │   ├── main.py          # Entry point
│   │   └── app/
│   │       ├── mcp.py       # MCP server
│   │       ├── mcp_routes.py # API endpoints
│   │       ├── key_manager.py # Key encryption
│   │       └── model_discovery.py
│   └── frontend/
│       ├── index.html
│       ├── style.css
│       └── app.js
├── docs/                    # Documentation
├── build_exe.py            # Windows build script
└── docker-compose.yml
```

## Credits

**Software Company:** Black Tiger Computing

**Development Team:**
- **Lead Developer:** sonamcgoo
- **Lead Designer:** OpenHands Agent
- **Contributors:** OpenHands Agents (infrastructure, testing, documentation)

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.10+, FastAPI, Uvicorn |
| Frontend | HTML5, CSS3, Vanilla JS |
| Storage | JSON files |
| Security | cryptography (Fernet) |

## License

MIT License — see [LICENSE](LICENSE)

---

*Copyright (c) 2024 Black Tiger Computing*
