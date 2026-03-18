# ⊙ Troubleshooting

Solutions to common issues with RITUAL.

## Common Issues

### Server Won't Start

**Problem:** `python -m src.backend.main` fails

**Solutions:**

1. **Port in use:**
   ```bash
   # Find what's using port 8000
   netstat -ano | findstr :8000
   # Kill the process or use different port
   python -m src.backend.main --port 8080
   ```

2. **Missing dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Python version too old:**
   ```bash
   python --version  # Should be 3.10+
   ```

---

### Can't Connect to LM Studio

**Problem:** LM Studio not connecting

**Solutions:**

1. **Check LM Studio is running**
2. **Verify API server is enabled in LM Studio:**
   - Open LM Studio
   - Go to Settings > Developer
   - Enable "Local Server"
3. **Check port matches config** (default: 1234)

---

### API Key Not Working

**Problem:** "Invalid API Key" error

**Solutions:**

1. **Re-enter the key:**
   - Go to Sigils panel
   - Delete the old key
   - Add a new key

2. **Check provider settings:**
   - Verify you're using the correct provider
   - Some keys are provider-specific

---

### Slow Performance

**Problem:** UI is laggy or slow

**Solutions:**

1. **Reduce MCM file sizes** (keep under 100KB)
2. **Close unused browser tabs**
3. **Clear browser cache**
4. **Disable browser extensions**

---

### Data Not Saving

**Problem:** Changes disappear after restart

**Solutions:**

1. **Check file permissions**
2. **Verify data directory exists:**
   ```bash
   ls -la ~/.ritual/
   ```
3. **Check for errors in console**

---

## Debug Mode

Enable debug mode for detailed logging:

```bash
python -m src.backend.main --debug
```

This will show:
- Request/response logs
- Detailed error messages
- Stack traces

## Getting Help

If you're still stuck:

1. Check GitHub Issues
2. Search Discussions
3. Create a new Issue with:
   - Your OS and Python version
   - Steps to reproduce
   - Error messages
   - Screenshots if relevant

---

## Known Limitations

- Currently requires local LLM tools (LM Studio, MSTY)
- No cloud sync (by design - privacy first)
- Single-user only
