# ⊙ API Reference

This document provides a complete reference for the RITUAL REST API.

## Base URL

```
http://localhost:8000/api
```

## Endpoints

### Health Check

Check if the API is running.

```
GET /health
```

**Response:**
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

---

### List LLM Providers

Get all available LLM providers.

```
GET /providers
```

**Response:**
```json
{
  "providers": [
    {
      "id": "lm-studio",
      "name": "LM Studio",
      "url": "http://localhost:1234",
      "status": "connected"
    },
    {
      "id": "msty",
      "name": "MSTY",
      "url": "http://localhost:9729",
      "status": "disconnected"
    }
  ]
}
```

---

### List MCM Files

Get all MCM files.

```
GET /mcm-files
```

**Response:**
```json
{
  "files": [
    {
      "id": "abc123",
      "name": "My Context",
      "content": "...",
      "created_at": "2026-01-01T00:00:00Z",
      "updated_at": "2026-01-01T00:00:00Z"
    }
  ]
}
```

---

### Create MCM File

Create a new MCM file.

```
POST /mcm-files
```

**Request Body:**
```json
{
  "name": "New Context",
  "content": "Context content here..."
}
```

**Response:**
```json
{
  "id": "xyz789",
  "name": "New Context",
  "content": "Context content here...",
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-01T00:00:00Z"
}
```

---

### Delete MCM File

Delete an MCM file.

```
DELETE /mcm-files/{id}
```

**Response:**
```json
{
  "success": true
}
```

---

### List Sigils (API Keys)

Get all stored API keys (encrypted).

```
GET /sigils
```

**Response:**
```json
{
  "sigils": [
    {
      "id": "key123",
      "name": "My OpenAI Key",
      "provider": "openai",
      "created_at": "2026-01-01T00:00:00Z"
    }
  ]
}
```

---

### Add Sigil

Add a new API key.

```
POST /sigils
```

**Request Body:**
```json
{
  "name": "My LM Studio Key",
  "provider": "lm-studio",
  "api_key": "sk-..."
}
```

**Response:**
```json
{
  "id": "key456",
  "name": "My LM Studio Key",
  "provider": "lm-studio",
  "created_at": "2026-01-01T00:00:00Z"
}
```

---

### Delete Sigil

Delete an API key.

```
DELETE /sigils/{id}
```

**Response:**
```json
{
  "success": true
}
```

---

## Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Invalid API key |
| 404 | Not Found - Resource doesn't exist |
| 500 | Internal Server Error |

## Rate Limiting

Currently no rate limiting is enforced for local usage.
