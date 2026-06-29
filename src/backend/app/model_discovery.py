"""
RITUAL Model Discovery
HuggingFace and CivitAI integration for browsing and downloading models
"""

import logging
import os
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import json

import requests

logger = logging.getLogger(__name__)


class ModelSource(Enum):
    HUGGINGFACE = "huggingface"
    CIVITAI = "civitai"
    LOCAL = "local"


class ModelType(Enum):
    TEXT = "text"
    IMAGE = "image"
    EMBEDDING = "embedding"
    VISION = "vision"
    UNKNOWN = "unknown"


@dataclass
class DiscoveredModel:
    """A discovered model from a registry."""
    id: str
    name: str
    source: str
    model_type: str
    downloads: int = 0
    likes: int = 0
    author: str = ""
    description: str = ""
    tags: List[str] = field(default_factory=list)
    sha: str = ""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    files: List[str] = field(default_factory=list)
    size_bytes: int = 0
    quantization: Optional[str] = None
    context_length: Optional[int] = None
    license: Optional[str] = None
    pipeline_tag: Optional[str] = None
    url: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "source": self.source,
            "model_type": self.model_type,
            "downloads": self.downloads,
            "likes": self.likes,
            "author": self.author,
            "description": self.description[:500] if self.description else "",
            "tags": self.tags[:10],
            "sha": self.sha,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "files": self.files[:5],
            "size_bytes": self.size_bytes,
            "quantization": self.quantization,
            "context_length": self.context_length,
            "license": self.license,
            "pipeline_tag": self.pipeline_tag,
            "url": self.url
        }
    
    @property
    def size_formatted(self) -> str:
        """Get human-readable size."""
        size = self.size_bytes
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"
    
    @property
    def is_quantized(self) -> bool:
        """Check if model appears to be quantized."""
        if self.quantization:
            return True
        q_patterns = ['q4', 'q5', 'q8', 'q16', 'q2_k', 'q3_k', 'q4_k', 'q5_k', 'q6_k', 'q8_k']
        name_lower = self.name.lower()
        return any(p in name_lower for p in q_patterns)


class HuggingFaceClient:
    """Client for HuggingFace Hub API."""
    
    BASE_URL = "https://huggingface.co/api"
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.environ.get("HF_TOKEN")
        self.headers = {}
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"
    
    def search_models(
        self,
        query: Optional[str] = None,
        filter_: Optional[str] = None,
        sort: str = "downloads",
        direction: int = -1,
        limit: int = 20,
        offset: int = 0
    ) -> List[DiscoveredModel]:
        """
        Search for models on HuggingFace.
        
        Args:
            query: Search query
            filter_: Model filter (e.g., "text-generation", "llm")
            sort: Sort field (downloads, likes, created_at)
            direction: 1 for ascending, -1 for descending
            limit: Number of results
            offset: Pagination offset
        """
        params = {
            "sort": sort,
            "direction": direction,
            "limit": limit,
            "offset": offset
        }
        
        if query:
            params["search"] = query
        if filter_:
            params["filter"] = filter_
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/models",
                headers=self.headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            models = []
            for item in data:
                model = self._parse_model(item)
                models.append(model)
            
            return models
        except requests.exceptions.RequestException as e:
            logger.error(f"HF search error: {e}")
            return []
    
    def get_model_info(self, model_id: str) -> Optional[DiscoveredModel]:
        """Get detailed info about a specific model."""
        try:
            # Get model card info
            response = requests.get(
                f"{self.BASE_URL}/models/{model_id}",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            return self._parse_model(data)
        except requests.exceptions.RequestException as e:
            logger.error(f"HF model info error: {e}")
            return None
    
    def get_model_files(self, model_id: str) -> List[Dict[str, Any]]:
        """Get list of files in a model repository."""
        try:
            response = requests.get(
                f"{self.BASE_URL}/models/{model_id}/trees/main",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            files = []
            for item in data:
                if item.get("type") == "file":
                    files.append({
                        "path": item.get("path"),
                        "size": item.get("size"),
                        "type": item.get("type")
                    })
            return files
        except requests.exceptions.RequestException as e:
            logger.error(f"HF files error: {e}")
            return []
    
    def download_model(self, model_id: str, destination: str) -> bool:
        """
        Download a model using huggingface-cli or git.
        Returns True if successful.
        """
        try:
            # Try huggingface-cli first
            cmd = ["huggingface-cli", "download", model_id, "--local-dir", destination]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            if result.returncode == 0:
                logger.info(f"Downloaded {model_id} to {destination}")
                return True
            
            # Fallback to git clone
            logger.info("Falling back to git clone...")
            cmd = ["git", "clone", f"https://huggingface.co/{model_id}", destination]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600
            )
            
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Download error: {e}")
            return False
    
    def _parse_model(self, data: Dict[str, Any]) -> DiscoveredModel:
        """Parse HF API response into DiscoveredModel."""
        # Extract author from model id
        author = data.get("id", "").split("/")[0] if "/" in data.get("id", "") else "unknown"
        
        # Determine model type from pipeline_tag
        pipeline_tag = data.get("pipeline_tag", "")
        model_type = self._infer_model_type(pipeline_tag, data.get("tags", []))
        
        # Try to detect quantization
        model_id = data.get("id", "")
        quantization = self._detect_quantization(model_id)
        
        # Extract context length from config if available
        context_length = None
        config = data.get("config", {})
        if config:
            context_length = config.get("max_position_embeddings") or config.get("n_ctx")
        
        return DiscoveredModel(
            id=data.get("id", ""),
            name=data.get("id", "").split("/")[-1],
            source=ModelSource.HUGGINGFACE.value,
            model_type=model_type,
            downloads=data.get("downloads", 0),
            likes=data.get("likes", 0),
            author=author,
            description=data.get("cardData", {}).get("base_model", ""),
            tags=data.get("tags", [])[:10],
            sha=data.get("sha", ""),
            created_at=data.get("createdAt"),
            updated_at=data.get("lastModified"),
            size_bytes=data.get("siblings", [{}])[0].get("size", 0) if data.get("siblings") else 0,
            quantization=quantization,
            context_length=context_length,
            license=data.get("license"),
            pipeline_tag=pipeline_tag,
            url=f"https://huggingface.co/{data.get('id', '')}"
        )
    
    def _infer_model_type(self, pipeline_tag: str, tags: List[str]) -> str:
        """Infer model type from pipeline tag and tags."""
        tag_lower = (pipeline_tag + " " + " ".join(tags)).lower()
        
        if any(x in tag_lower for x in ["text-generation", "causal-lm", "gpt", "llama", "mistral", "mixtral"]):
            return ModelType.TEXT.value
        elif any(x in tag_lower for x in ["image", "stable-diffusion", "sd", "flux"]):
            return ModelType.IMAGE.value
        elif any(x in tag_lower for x in ["embedding", "sentence", "bert"]):
            return ModelType.EMBEDDING.value
        elif any(x in tag_lower for x in ["vision", "clip", "image-text"]):
            return ModelType.VISION.value
        return ModelType.UNKNOWN.value
    
    def _detect_quantization(self, model_id: str) -> Optional[str]:
        """Detect quantization level from model ID."""
        model_lower = model_id.lower()
        
        if "q2_k" in model_lower:
            return "Q2_K"
        elif "q3_k" in model_lower:
            return "Q3_K"
        elif "q4_k" in model_lower:
            return "Q4_K"
        elif "q5_k" in model_lower:
            return "Q5_K"
        elif "q6_k" in model_lower:
            return "Q6_K"
        elif "q8" in model_lower:
            return "Q8_0"
        elif "f16" in model_lower:
            return "FP16"
        elif "f32" in model_lower:
            return "FP32"
        elif "int8" in model_lower:
            return "INT8"
        elif "int4" in model_lower:
            return "INT4"
        
        return None


class CivitAIClient:
    """Client for CivitAI API."""
    
    BASE_URL = "https://civitai.com/api/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("CIVITAI_API_KEY")
        self.headers = {}
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"
    
    def search_models(
        self,
        query: Optional[str] = None,
        model_type: Optional[str] = None,
        sort: str = "Downloads",
        period: str = "AllTime",
        limit: int = 20,
        offset: int = 0
    ) -> List[DiscoveredModel]:
        """
        Search for models on CivitAI.
        
        Args:
            query: Search query
            model_type: Type filter (e.g., "Lora", "Checkpoint")
            sort: Sort field
            period: Time period
            limit: Number of results
            offset: Pagination offset
        """
        params = {
            "sort": sort,
            "period": period,
            "limit": limit,
            "offset": offset
        }
        
        if query:
            params["query"] = query
        if model_type:
            params["type"] = model_type
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/models",
                headers=self.headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            models = []
            for item in data.get("items", []):
                model = self._parse_model(item)
                models.append(model)
            
            return models
        except requests.exceptions.RequestException as e:
            logger.error(f"CivitAI search error: {e}")
            return []
    
    def get_model_info(self, model_id: int) -> Optional[DiscoveredModel]:
        """Get detailed info about a specific model."""
        try:
            response = requests.get(
                f"{self.BASE_URL}/models/{model_id}",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            return self._parse_model(data)
        except requests.exceptions.RequestException as e:
            logger.error(f"CivitAI model info error: {e}")
            return None
    
    def get_model_versions(self, model_id: int) -> List[Dict[str, Any]]:
        """Get all versions of a model."""
        try:
            response = requests.get(
                f"{self.BASE_URL}/models/{model_id}",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            return data.get("modelVersions", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"CivitAI versions error: {e}")
            return []
    
    def download_model(self, model_version_id: int, destination: str) -> bool:
        """
        Download a model by version ID.
        Returns download URL - actual download should be handled separately.
        """
        try:
            response = requests.get(
                f"{self.BASE_URL}/models/{model_version_id}/download",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            # Return the download URL
            return data.get("downloadUrl")
        except requests.exceptions.RequestException as e:
            logger.error(f"CivitAI download error: {e}")
            return None
    
    def _parse_model(self, data: Dict[str, Any]) -> DiscoveredModel:
        """Parse CivitAI API response into DiscoveredModel."""
        # Get first version info if available
        versions = data.get("modelVersions", [])
        first_version = versions[0] if versions else {}
        
        # Get primary file
        files = first_version.get("files", [])
        primary_file = files[0] if files else {}
        
        # Get tags
        tags = [t.get("name", "") for t in data.get("tags", [])]
        
        return DiscoveredModel(
            id=str(data.get("id", "")),
            name=data.get("name", ""),
            source=ModelSource.CIVITAI.value,
            model_type=data.get("type", "").lower(),
            downloads=data.get("downloadCount", 0),
            likes=data.get("likes", 0),
            author=data.get("creator", {}).get("username", ""),
            description=data.get("description", ""),
            tags=tags[:10],
            created_at=data.get("createdAt"),
            updated_at=data.get("updatedAt"),
            files=[f.get("name", "") for f in files[:5]],
            size_bytes=primary_file.get("sizeKB", 0) * 1024,
            url=f"https://civitai.com/models/{data.get('id', '')}"
        )


class LocalModelScanner:
    """Scan local directories for models."""
    
    SUPPORTED_EXTENSIONS = [
        ".bin",  # GGUF, safetensors
        ".gguf",
        ".safetensors",
        ".pt",
        ".pth",
        ".ckpt",
        ".pt",
        ".onnx",
        ".ggml"
    ]
    
    SUPPORTED_FILENAMES = [
        "config.json",
        "tokenizer.json",
        "tokenizer_config.json",
        "model.safetensors",
        "pytorch_model.bin",
        "model.bin",
        "consolidated.safetensors"
    ]
    
    def __init__(self):
        self.models_dir = self._get_default_models_dir()
    
    def _get_default_models_dir(self) -> str:
        """Get the default local models directory."""
        possible_dirs = [
            os.path.expanduser("~/models"),
            os.path.expanduser("~/.cache/huggingface/hub"),
            os.path.expanduser("~/.ollama/models"),
            os.path.join(os.getcwd(), "models"),
            "./models"
        ]
        
        for d in possible_dirs:
            if os.path.exists(d):
                return d
        
        return possible_dirs[0]  # Return first option even if not exists
    
    def set_models_dir(self, directory: str) -> None:
        """Set the directory to scan for models."""
        self.models_dir = directory
    
    def scan(self, recursive: bool = True) -> List[DiscoveredModel]:
        """Scan for models in the configured directory."""
        if not os.path.exists(self.models_dir):
            logger.warning(f"Models directory does not exist: {self.models_dir}")
            return []
        
        models = []
        scanned_paths = set()
        
        if recursive:
            for root, dirs, files in os.walk(self.models_dir):
                # Skip hidden and cache directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
                
                for file in files:
                    if self._is_model_file(file, root):
                        path = os.path.join(root, file)
                        if path not in scanned_paths:
                            model = self._create_local_model(path, files)
                            if model:
                                models.append(model)
                                scanned_paths.add(path)
        else:
            for file in os.listdir(self.models_dir):
                path = os.path.join(self.models_dir, file)
                if os.path.isdir(path):
                    model = self._scan_model_directory(path)
                    if model:
                        models.append(model)
        
        return models
    
    def _is_model_file(self, filename: str, directory: str) -> bool:
        """Check if a file is likely a model file."""
        ext = os.path.splitext(filename)[1].lower()
        return ext in self.SUPPORTED_EXTENSIONS
    
    def _scan_model_directory(self, path: str) -> Optional[DiscoveredModel]:
        """Scan a directory for a model."""
        if not os.path.isdir(path):
            return None
        
        files = os.listdir(path)
        
        # Check for model indicators
        has_config = any(f in files for f in self.SUPPORTED_FILENAMES)
        
        model_files = [f for f in files if any(f.endswith(ext) for ext in self.SUPPORTED_EXTENSIONS)]
        
        if model_files or has_config:
            primary_file = os.path.join(path, model_files[0]) if model_files else None
            size = os.path.getsize(primary_file) if primary_file and os.path.exists(primary_file) else 0
            
            return DiscoveredModel(
                id=path,
                name=os.path.basename(path),
                source=ModelSource.LOCAL.value,
                model_type=ModelType.UNKNOWN.value,
                size_bytes=size,
                files=files[:10],
                url=path
            )
        
        return None
    
    def _create_local_model(self, path: str, sibling_files: List[str]) -> Optional[DiscoveredModel]:
        """Create a model entry from a file path."""
        directory = os.path.dirname(path)
        filename = os.path.basename(path)
        
        size = os.path.getsize(path)
        
        return DiscoveredModel(
            id=path,
            name=filename,
            source=ModelSource.LOCAL.value,
            model_type=ModelType.UNKNOWN.value,
            size_bytes=size,
            files=[f for f in sibling_files if not f.startswith('.')][:10],
            url=path
        )


class ModelDiscoveryService:
    """
    Unified model discovery service combining HF, CivitAI, and local models.
    """
    
    def __init__(self):
        self.hf_client = HuggingFaceClient()
        self.civitai_client = CivitAIClient()
        self.local_scanner = LocalModelScanner()
    
    def search_all(
        self,
        query: str,
        sources: Optional[List[str]] = None,
        model_type: Optional[str] = None,
        limit: int = 20
    ) -> Dict[str, List[DiscoveredModel]]:
        """
        Search across all configured sources.
        
        Args:
            query: Search query
            sources: List of sources to search (hf, civitai, local)
            model_type: Filter by model type
            limit: Results per source
        
        Returns:
            Dict mapping source names to lists of models
        """
        if sources is None:
            sources = ["huggingface", "civitai", "local"]
        
        results = {}
        
        if "huggingface" in sources:
            results["huggingface"] = self.hf_client.search_models(
                query=query,
                filter_=model_type,
                limit=limit
            )
        
        if "civitai" in sources:
            results["civitai"] = self.civitai_client.search_models(
                query=query,
                model_type=model_type,
                limit=limit
            )
        
        if "local" in sources:
            local_models = self.local_scanner.scan()
            # Filter local models by query
            if query:
                query_lower = query.lower()
                local_models = [
                    m for m in local_models
                    if query_lower in m.name.lower()
                ]
            results["local"] = local_models[:limit]
        
        return results
    
    def get_hf_client(self) -> HuggingFaceClient:
        return self.hf_client
    
    def get_civitai_client(self) -> CivitAIClient:
        return self.civitai_client
    
    def get_local_scanner(self) -> LocalModelScanner:
        return self.local_scanner


# Global discovery service
discovery_service = ModelDiscoveryService()


def get_discovery_service() -> ModelDiscoveryService:
    """Get the global discovery service instance."""
    return discovery_service
