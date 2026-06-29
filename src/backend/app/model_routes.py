"""
RITUAL Model Discovery Routes
HuggingFace, CivitAI, and local model browsing
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel

from app.model_discovery import ModelDiscoveryService, DiscoveredModel

logger = logging.getLogger(__name__)

# Router
models_router = APIRouter()


class ModelSearchRequest(BaseModel):
    query: str = ""
    sources: List[str] = ["huggingface", "civitai", "local"]
    model_type: Optional[str] = None
    limit: int = 20


class ModelDownloadRequest(BaseModel):
    model_id: str
    destination: str
    source: str = "huggingface"


@models_router.get("")
async def search_models(
    request: Request,
    query: Optional[str] = None,
    sources: Optional[str] = None,  # Comma-separated
    model_type: Optional[str] = None,
    limit: int = 20
):
    """
    Search for models across all sources.
    
    Args:
        query: Search query
        sources: Comma-separated list of sources (huggingface, civitai, local)
        model_type: Filter by model type
        limit: Number of results per source
    """
    discovery = request.app.state.discovery_service
    
    source_list = sources.split(",") if sources else ["huggingface", "civitai", "local"]
    
    results = discovery.search_all(
        query=query or "",
        sources=source_list,
        model_type=model_type,
        limit=limit
    )
    
    # Flatten and format results
    all_models = []
    for source, models in results.items():
        for model in models:
            model_dict = model.to_dict()
            model_dict["source"] = source
            all_models.append(model_dict)
    
    return {
        "results": all_models,
        "count": len(all_models),
        "query": query,
        "sources": source_list
    }


@models_router.post("/search")
async def search_models_post(data: ModelSearchRequest, request: Request):
    """Search models (POST version)."""
    discovery = request.app.state.discovery_service
    
    results = discovery.search_all(
        query=data.query,
        sources=data.sources,
        model_type=data.model_type,
        limit=data.limit
    )
    
    all_models = []
    for source, models in results.items():
        for model in models:
            model_dict = model.to_dict()
            model_dict["source"] = source
            all_models.append(model_dict)
    
    return {
        "results": all_models,
        "count": len(all_models)
    }


@models_router.get("/huggingface")
async def search_huggingface(
    request: Request,
    query: Optional[str] = None,
    filter_: Optional[str] = None,
    sort: str = "downloads",
    limit: int = 20
):
    """Search HuggingFace specifically."""
    discovery = request.app.state.discovery_service
    client = discovery.get_hf_client()
    
    models = client.search_models(
        query=query,
        filter_=filter_,
        sort=sort,
        limit=limit
    )
    
    return {
        "models": [m.to_dict() for m in models],
        "count": len(models),
        "source": "huggingface"
    }


@models_router.get("/huggingface/{model_id}")
async def get_huggingface_model(model_id: str, request: Request):
    """Get detailed info about a HuggingFace model."""
    discovery = request.app.state.discovery_service
    client = discovery.get_hf_client()
    
    model = client.get_model_info(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    return model.to_dict()


@models_router.get("/huggingface/{model_id}/files")
async def get_huggingface_files(model_id: str, request: Request):
    """Get file list for a HuggingFace model."""
    discovery = request.app.state.discovery_service
    client = discovery.get_hf_client()
    
    files = client.get_model_files(model_id)
    return {"model_id": model_id, "files": files}


@models_router.post("/huggingface/{model_id}/download")
async def download_huggingface_model(
    model_id: str,
    destination: str,
    request: Request,
    background_tasks: BackgroundTasks
):
    """Download a HuggingFace model."""
    discovery = request.app.state.discovery_service
    client = discovery.get_hf_client()
    
    # Run download in background
    def do_download():
        client.download_model(model_id, destination)
    
    background_tasks.add_task(do_download)
    
    return {
        "status": "downloading",
        "model_id": model_id,
        "destination": destination
    }


@models_router.get("/civitai")
async def search_civitai(
    request: Request,
    query: Optional[str] = None,
    model_type: Optional[str] = None,
    sort: str = "Downloads",
    limit: int = 20
):
    """Search CivitAI specifically."""
    discovery = request.app.state.discovery_service
    client = discovery.get_civitai_client()
    
    models = client.search_models(
        query=query,
        model_type=model_type,
        sort=sort,
        limit=limit
    )
    
    return {
        "models": [m.to_dict() for m in models],
        "count": len(models),
        "source": "civitai"
    }


@models_router.get("/civitai/{model_id}")
async def get_civitai_model(model_id: int, request: Request):
    """Get detailed info about a CivitAI model."""
    discovery = request.app.state.discovery_service
    client = discovery.get_civitai_client()
    
    model = client.get_model_info(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    return model.to_dict()


@models_router.get("/local")
async def list_local_models(
    request: Request,
    recursive: bool = True,
    models_dir: Optional[str] = None
):
    """List locally available models."""
    discovery = request.app.state.discovery_service
    scanner = discovery.get_local_scanner()
    
    if models_dir:
        scanner.set_models_dir(models_dir)
    
    models = scanner.scan(recursive=recursive)
    
    return {
        "models": [m.to_dict() for m in models],
        "count": len(models),
        "source": "local",
        "directory": scanner.models_dir
    }


@models_router.post("/local/scan")
async def scan_local_models(
    models_dir: str,
    request: Request,
    recursive: bool = True
):
    """Scan a specific directory for models."""
    discovery = request.app.state.discovery_service
    scanner = discovery.get_local_scanner()
    scanner.set_models_dir(models_dir)
    
    models = scanner.scan(recursive=recursive)
    
    return {
        "models": [m.to_dict() for m in models],
        "count": len(models),
        "directory": models_dir
    }


@models_router.get("/sources")
async def get_model_sources():
    """Get information about available model sources."""
    return {
        "sources": [
            {
                "id": "huggingface",
                "name": "HuggingFace Hub",
                "url": "https://huggingface.co/models",
                "types": ["text-generation", "embedding", "vision", "image"],
                "requires_auth": False,
                "supports_download": True
            },
            {
                "id": "civitai",
                "name": "CivitAI",
                "url": "https://civitai.com",
                "types": ["lora", "checkpoint", "embedding", "controlnet"],
                "requires_auth": False,
                "supports_download": True
            },
            {
                "id": "local",
                "name": "Local Models",
                "url": None,
                "types": ["all"],
                "requires_auth": False,
                "supports_download": False
            }
        ]
    }


# Recommended small quantized models for prompt engineer
@models_router.get("/recommended")
async def get_recommended_models():
    """Get recommended small quantized models for local inference."""
    return {
        "recommended": [
            {
                "name": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
                "size": "~1GB",
                "quantization": "Q4_K_M",
                "context_length": 2048,
                "use_case": "Fast local inference, good for simple tasks",
                "source": "huggingface"
            },
            {
                "name": "TheBloke/Mistral-7B-Instruct-v0.2-GGUF",
                "size": "~4GB",
                "quantization": "Q4_K_M",
                "context_length": 32768,
                "use_case": "Good balance of quality and size",
                "source": "huggingface"
            },
            {
                "name": "TheBloke/Llama-2-7B-Chat-GGUF",
                "size": "~3.8GB",
                "quantization": "Q4_K_M",
                "context_length": 4096,
                "use_case": "Well-optimized Llama 2 7B",
                "source": "huggingface"
            },
            {
                "name": "TheBloke/zephyr-7B-beta-GGUF",
                "size": "~4GB",
                "quantization": "Q4_K_M",
                "context_length": 4096,
                "use_case": "Great instruction following",
                "source": "huggingface"
            },
            {
                "name": "QuantFactory/MetaLlama-3.1-8B-Instruct-GGUF",
                "size": "~4.7GB",
                "quantization": "Q4_K_M",
                "context_length": 8192,
                "use_case": "Latest Llama 3.1, excellent quality",
                "source": "huggingface"
            },
            {
                "name": "TheBloke/Phi-3-mini-4k-instruct-GGUF",
                "size": "~2.5GB",
                "quantization": "Q4_K_M",
                "context_length": 4096,
                "use_case": "Microsoft's efficient small model",
                "source": "huggingface"
            }
        ],
        "note": "These models work well with llama.cpp for local inference"
    }


@models_router.get("/ollama/status")
async def ollama_status():
    """Check if Ollama is running and get available models."""
    import requests
    
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=3)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return {
                "running": True,
                "models": [m["name"] for m in models],
                "count": len(models)
            }
    except:
        pass
    
    return {
        "running": False,
        "models": [],
        "count": 0,
        "hint": "Install Ollama and run 'ollama serve' to enable local inference"
    }
