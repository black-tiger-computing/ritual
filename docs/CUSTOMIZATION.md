# ⊙ Customization Guide

Customize RITUAL to match your preferences.

## Themes

### Default Hermetic Theme

RITUAL comes with a beautiful hermetic/mystical theme by default.

### Dark Mode

The interface automatically supports system dark mode preferences.

### Custom CSS

Add custom styles by editing `src/frontend/style.css`:

```css
/* Custom accent color */
:root {
  --accent-color: #9b59b6;
}

/* Custom background */
body {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
}
```

## Configuration

### Server Configuration

Edit `config/default-config.json`:

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8000,
    "debug": false
  },
  "llm_providers": {
    "lm_studio": {
      "url": "http://localhost:1234",
      "enabled": true
    },
    "msty": {
      "url": "http://localhost:9729",
      "enabled": true
    }
  },
  "security": {
    "encrypt_keys": true
  }
}
```

### Environment Variables

You can also use environment variables:

```bash
# .env file
RITUAL_PORT=8000
RITUAL_HOST=0.0.0.0
RITUAL_DEBUG=true
```

## Adding Custom LLM Providers

1. Create a new provider class in `src/backend/app/llm_discovery.py`:

```python
class CustomProvider:
    def __init__(self, url: str, name: str):
        self.url = url
        self.name = name

    def check_connection(self) -> bool:
        # Implement connection check
        pass

    def get_models(self) -> list:
        # Return available models
        pass
```

2. Register the provider in config

## Custom Animations

Add custom CSS animations:

```css
@keyframes mystical-glow {
  0% { box-shadow: 0 0 5px #9b59b6; }
  50% { box-shadow: 0 0 20px #9b59b6; }
  100% { box-shadow: 0 0 5px #9b59b6; }
}

.ritual-element {
  animation: mystical-glow 2s ease-in-out infinite;
}
```

## Plugins (Future)

Coming soon: Plugin system for extending RITUAL functionality.
