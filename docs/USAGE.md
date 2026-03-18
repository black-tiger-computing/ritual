# ⊙ User Guide

Welcome to the RITUAL user guide. This document will walk you through using all the features of RITUAL.

## Quick Start

1. Start the server: `python -m src.backend.main`
2. Open browser: `http://localhost:8000`
3. You're ready to go!

## Interface Overview

### Dashboard

The main dashboard provides a quick overview of your LLM connections and MCM files.

**Key Features:**
- Connection status at a glance
- Quick access to recent MCM files
- One-button activation

### Grimoire (MCM Management)

The Grimoire is where you manage your Model Context Management files.

**Operations:**
- Create new MCM files
- Edit existing files
- Delete unused contexts
- Import/Export MCM files

### Sigils (API Key Management)

Sigils allow you to securely store and manage API keys for various LLM providers.

**Supported Providers:**
- LM Studio
- MSTY
- OpenAI
- Anthropic
- And more...

**Managing Sigils:**
1. Click "Add Sigil" in the Sigils panel
2. Enter your API key
3. Select the provider
4. Save securely

## Configuration

### Setting Up LM Studio

1. Open LM Studio
2. Go to Settings > API
3. Note the local server URL (default: `http://localhost:1234`)
4. Add this to RITUAL's configuration

### Setting Up MSTY

1. Open MSTY
2. Navigate to API settings
3. Copy the API endpoint
4. Configure in RITUAL

## Tips & Tricks

### Performance Optimization

- Keep MCM files under 100KB for optimal performance
- Use context consolidation regularly
- Disable unused LLM connections

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+S` | Save current MCM |
| `Ctrl+N` | New MCM file |
| `Ctrl+K` | Open command palette |

## Troubleshooting

### Connection Issues

**Problem:** Cannot connect to LM Studio

**Solution:**
1. Ensure LM Studio is running
2. Check the API server is enabled in LM Studio settings
3. Verify the port number matches your configuration

### API Key Issues

**Problem:** "Invalid API Key" error

**Solution:**
1. Double-check the API key
2. Re-enter the key in Sigils
3. Verify the provider is correct
