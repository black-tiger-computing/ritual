#!/usr/bin/env python3
"""Setup MCM Portal project structure and copy files from HaleHound"""
import shutil
import json
from pathlib import Path

# Define paths
ritual_dir = Path(__file__).parent
mcm_portal_dir = ritual_dir / "mcm-portal"
app_dir = mcm_portal_dir / "app"
static_dir = app_dir / "static"

# Create directories
print("Creating directories...")
mcm_portal_dir.mkdir(exist_ok=True)
app_dir.mkdir(exist_ok=True)
static_dir.mkdir(exist_ok=True)
print("✓ Directories created")

# Define file contents
files_to_create = {
    mcm_portal_dir / "main.py": '''"""MCM AI Portal - Main Entry Point"""
import os, sys, json, webbrowser
from pathlib import Path
import uvicorn
sys.path.insert(0, str(Path(__file__).parent))
from app.server import create_app
from app.config import AppConfig
from app.storage import StorageManager

def setup_app_directory():
    app_dir = Path.home() / ".mcm-ai-portal"
    app_dir.mkdir(exist_ok=True)
    (app_dir / "mcm_files").mkdir(exist_ok=True)
    (app_dir / "configs").mkdir(exist_ok=True)
    return app_dir

def main(host="127.0.0.1", port=8000, open_browser=True):
    print("""
╔════════════════════════════════════════╗
║           ⊙ RITUAL ⊙                  ║
║    Hermetic LLM Context Portal         ║
╚════════════════════════════════════════╝
""")
    app_dir = setup_app_directory()
    config = AppConfig(app_dir=app_dir)
    storage = StorageManager(app_dir=app_dir)
    app = create_app(config, storage)
    
    if open_browser:
        import threading, time
        threading.Thread(target=lambda: (time.sleep(2), webbrowser.open(f"http://{host}:{port}")), daemon=True).start()
    
    try:
        uvicorn.run(app, host=host, port=port, log_level="info")
    except KeyboardInterrupt:
        print("\\n👋 Circle dispersed. Ritual concluded.")
        sys.exit(0)

if __name__ == "__main__":
    main()
''',
    
    app_dir / "__init__.py": '"""MCM AI Portal Application Package"""',
    
    app_dir / "config.py": '''"""Configuration Management"""
import json
from pathlib import Path
from typing import Dict, Any, Optional

class AppConfig:
    def __init__(self, app_dir: Path):
        self.app_dir = app_dir
        self.config_file = app_dir / "configs" / "config.json"
        self.data = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        if self.config_file.exists():
            with open(self.config_file) as f:
                return json.load(f)
        default = {
            "lm_studio": {"auto_detect": True, "host": "localhost", "port": 1234, "enabled": True},
            "msty": {"auto_detect": True, "host": "localhost", "port": 5001, "enabled": True},
            "api_keys_encrypted": True,
            "web_ui": {"host": "127.0.0.1", "port": 8000}
        }
        self.save(default)
        return default
    
    def save(self, data: Optional[Dict] = None):
        if data:
            self.data = data
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "w") as f:
            json.dump(self.data, f, indent=2)
    
    def get(self, key: str, default=None):
        keys = key.split(".")
        val = self.data
        for k in keys:
            val = val.get(k, {}) if isinstance(val, dict) else default
        return val if val != {} else default
''',
    
    app_dir / "storage.py": '''"""Local Storage Management"""
import json, yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from cryptography.fernet import Fernet
import os

class StorageManager:
    def __init__(self, app_dir: Path):
        self.app_dir = app_dir
        self.mcm_dir = app_dir / "mcm_files"
        self.config_dir = app_dir / "configs"
        self.cipher = self._init_cipher()
        self.mcm_dir.mkdir(exist_ok=True)
        self.config_dir.mkdir(exist_ok=True)
    
    def _init_cipher(self) -> Fernet:
        key_file = self.config_dir / ".cipher_key"
        if key_file.exists():
            with open(key_file, "rb") as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, "wb") as f:
                f.write(key)
            os.chmod(str(key_file), 0o600)
        return Fernet(key)
    
    def list_mcm_files(self) -> List[Dict[str, Any]]:
        files = []
        for ext in ["*.json", "*.yaml", "*.yml"]:
            for file_path in self.mcm_dir.glob(ext):
                files.append({"name": file_path.stem, "format": file_path.suffix.lstrip("."), "path": str(file_path), "size": file_path.stat().st_size})
        return sorted(files, key=lambda x: x["name"])
    
    def load_mcm_file(self, filename: str) -> Dict[str, Any]:
        file_path = self.mcm_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(f"MCM file not found: {filename}")
        with open(file_path, "r") as f:
            return yaml.safe_load(f) if file_path.suffix.lower() in [".yaml", ".yml"] else json.load(f)
    
    def save_mcm_file(self, filename: str, data: Dict[str, Any], format: str = "json"):
        ext = f".{format}" if not filename.endswith(f".{format}") else ""
        file_path = self.mcm_dir / f"{filename}{ext}"
        with open(file_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False) if format in ["yaml", "yml"] else json.dump(data, f, indent=2)
        return str(file_path)
    
    def delete_mcm_file(self, filename: str) -> bool:
        file_path = self.mcm_dir / filename
        if file_path.exists():
            file_path.unlink()
            return True
        return False
    
    def store_api_key(self, service: str, key: str):
        keys_file = self.config_dir / ".api_keys"
        keys = {}
        if keys_file.exists():
            with open(keys_file, "rb") as f:
                keys = json.loads(self.cipher.decrypt(f.read()).decode())
        keys[service] = key
        with open(keys_file, "wb") as f:
            f.write(self.cipher.encrypt(json.dumps(keys).encode()))
        os.chmod(str(keys_file), 0o600)
    
    def get_api_key(self, service: str) -> Optional[str]:
        keys_file = self.config_dir / ".api_keys"
        if not keys_file.exists():
            return None
        with open(keys_file, "rb") as f:
            keys = json.loads(self.cipher.decrypt(f.read()).decode())
        return keys.get(service)
    
    def delete_api_key(self, service: str) -> bool:
        keys_file = self.config_dir / ".api_keys"
        if not keys_file.exists():
            return False
        with open(keys_file, "rb") as f:
            keys = json.loads(self.cipher.decrypt(f.read()).decode())
        if service in keys:
            del keys[service]
            with open(keys_file, "wb") as f:
                f.write(self.cipher.encrypt(json.dumps(keys).encode()))
            return True
        return False
''',
    
    app_dir / "llm_discovery.py": '''"""LLM Auto-Discovery"""
from typing import Dict, Any
from app.config import AppConfig

class LLMDiscovery:
    def __init__(self, config: AppConfig):
        self.config = config
        self.discovered_llms = {}
    
    def check_lm_studio(self) -> Dict[str, Any]:
        host = self.config.get("lm_studio.host", "localhost")
        port = self.config.get("lm_studio.port", 1234)
        try:
            import requests
            resp = requests.get(f"http://{host}:{port}/v1/models", timeout=2)
            if resp.status_code == 200:
                return {"available": True, "host": host, "port": port, "url": f"http://{host}:{port}"}
        except:
            pass
        return {"available": False}
    
    def check_msty(self) -> Dict[str, Any]:
        host = self.config.get("msty.host", "localhost")
        port = self.config.get("msty.port", 5001)
        try:
            import requests
            resp = requests.get(f"http://{host}:{port}/health", timeout=2)
            if resp.status_code == 200:
                return {"available": True, "host": host, "port": port, "url": f"http://{host}:{port}"}
        except:
            pass
        return {"available": False}
    
    def discover_all(self):
        self.discovered_llms = {"lm_studio": self.check_lm_studio(), "msty": self.check_msty()}
        return self.discovered_llms
''',
    
    app_dir / "server.py": '''"""FastAPI Server Setup"""
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
import json
from typing import Dict, Any
from app.config import AppConfig
from app.storage import StorageManager
from app.llm_discovery import LLMDiscovery

class MCMFileCreate(BaseModel):
    filename: str
    format: str
    data: Dict[str, Any]

class APIKeyRequest(BaseModel):
    service: str
    key: str

def create_app(config: AppConfig, storage: StorageManager) -> FastAPI:
    app = FastAPI(title="MCM AI Portal", version="0.1.0")
    llm_discovery = LLMDiscovery(config)
    
    @app.get("/api/mcm/files")
    async def list_mcm_files():
        return {"files": storage.list_mcm_files(), "path": str(storage.mcm_dir)}
    
    @app.post("/api/mcm/files")
    async def create_mcm_file(request: MCMFileCreate):
        try:
            path = storage.save_mcm_file(request.filename, request.data, request.format)
            return {"success": True, "path": path}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.get("/api/portal/status")
    async def portal_status():
        return {
            "app": "MCM AI Portal",
            "version": "0.1.0",
            "data_dir": str(storage.app_dir),
            "mcm_files": len(storage.list_mcm_files()),
            "llms": {"lm_studio": llm_discovery.check_lm_studio(), "msty": llm_discovery.check_msty()}
        }
    
    @app.get("/")
    async def serve_index():
        index_path = Path(__file__).parent.parent / "app" / "static" / "index.html"
        return FileResponse(index_path) if index_path.exists() else HTTPException(status_code=404)
    
    return app
''',
    
    static_dir / "index.html": '''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Ritual - Hermetic Portal</title><link rel="stylesheet" href="/static/style.css"></head>
<body><div class="container"><header class="header"><h1>⊙ RITUAL ⊙</h1><p>Hermetic LLM Context Portal</p></header>
<button class="btn btn-primary" onclick="alert('Portal activated!')">⊕ SUMMON INTERFACE ⊕</button></div>
<script src="/static/app.js"></script></body></html>''',
    
    static_dir / "style.css": '''*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:Georgia,serif;background:linear-gradient(-45deg,#1a0033,#2d0052,#0f1747,#3d1066);color:#e0d5ff;min-height:100vh;}
.container{max-width:1200px;margin:0 auto;padding:20px;}
.header{background:rgba(20,5,50,0.7);padding:40px;border-radius:12px;text-align:center;}
.header h1{font-size:3em;background:linear-gradient(135deg,#6e7eea,#b266ff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.btn{padding:14px 28px;border:none;border-radius:6px;cursor:pointer;text-transform:uppercase;}
.btn-primary{background:linear-gradient(135deg,rgba(102,126,234,0.7),rgba(178,102,255,0.5));color:#fff;}''',
    
    static_dir / "app.js": '''const API_BASE = '/api';
fetch(API_BASE + '/portal/status').then(r => r.json()).then(d => console.log('MCM Portal Ready:', d)).catch(e => console.error('Error:', e));''',
    
    mcm_portal_dir / "requirements.txt": '''fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
pyyaml==6.0.1
cryptography==41.0.7
aiohttp==3.9.1
python-multipart==0.0.6
requests==2.31.0
''',
    
    mcm_portal_dir / "RUN_MCM_PORTAL.bat": '''@echo off
python -m venv venv
call venv\\Scripts\\activate.bat
pip install -r requirements.txt
start http://localhost:8000
python main.py
pause
''',
    
    mcm_portal_dir / "README.md": '''# MCM AI Portal

Web dashboard for managing MCM files, API keys, and LLM connections.

## Quick Start
Double-click `RUN_MCM_PORTAL.bat`

## Features
- MCM file management
- Encrypted API key storage  
- LLM auto-discovery
- Real-time monitoring
'''
}

# Create files
print("Creating files...")
for file_path, content in files_to_create.items():
    file_path.write_text(content)
    print(f"✓ {file_path.name}")

print("\n✨ MCM Portal project structure created successfully!")
print(f"Location: {mcm_portal_dir}")
