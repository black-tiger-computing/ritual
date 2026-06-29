"""
RITUAL Model Runner
Local quantized model inference for the Prompt Engineer assistant
Supports llama.cpp, transformers, and cloud inference backends
"""

import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import json

logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    """Configuration for a model."""
    name: str
    path: str  # Local path or HuggingFace ID
    backend: str  # "llama.cpp", "transformers", "openai", "anthropic", "ollama"
    quantization: Optional[str] = "Q4_K_M"  # For llama.cpp
    context_length: int = 2048
    gpu_layers: int = -1  # -1 = all
    temperature: float = 0.7
    max_tokens: int = 512
    api_base: Optional[str] = None  # For custom API endpoints
    api_key: Optional[str] = None  # For cloud APIs


@dataclass
class ChatMessage:
    """A single chat message."""
    role: str  # "system", "user", "assistant"
    content: str


class BaseModelRunner(ABC):
    """Abstract base class for model runners."""
    
    @abstractmethod
    def generate(self, messages: List[ChatMessage], **kwargs) -> str:
        """Generate a response from messages."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the model is available/loaded."""
        pass
    
    @abstractmethod
    def load(self) -> bool:
        """Load the model."""
        pass


class LlamaCPPRunner(BaseModelRunner):
    """Llama.cpp Python bindings runner."""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self._model = None
        self._context = None
    
    def is_available(self) -> bool:
        try:
            from llama_cpp import Llama
            return True
        except ImportError:
            return False
    
    def load(self) -> bool:
        if self._model is not None:
            return True
        
        try:
            from llama_cpp import Llama
            logger.info(f"Loading llama.cpp model: {self.config.path}")
            
            self._model = Llama(
                model_path=self.config.path,
                n_ctx=self.config.context_length,
                n_gpu_layers=self.config.gpu_layers,
                verbose=False
            )
            logger.info("Model loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False
    
    def generate(self, messages: List[ChatMessage], **kwargs) -> str:
        if not self._model:
            if not self.load():
                return "Error: Model not available"
        
        # Build prompt from messages
        prompt = self._messages_to_prompt(messages)
        
        try:
            output = self._model(
                prompt,
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                temperature=kwargs.get("temperature", self.config.temperature),
                stop=["</s>", "\n\nUser:", "User:"],
                echo=False
            )
            return output["choices"][0]["text"].strip()
        except Exception as e:
            logger.error(f"Generation error: {e}")
            return f"Error: {str(e)}"
    
    def _messages_to_prompt(self, messages: List[ChatMessage]) -> str:
        """Convert messages to a prompt string."""
        parts = []
        for msg in messages:
            if msg.role == "system":
                parts.append(f"System: {msg.content}")
            elif msg.role == "user":
                parts.append(f"User: {msg.content}")
            elif msg.role == "assistant":
                parts.append(f"Assistant: {msg.content}")
        parts.append("Assistant:")
        return "\n\n".join(parts)


class TransformersRunner(BaseModelRunner):
    """HuggingFace Transformers runner."""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self._pipeline = None
    
    def is_available(self) -> bool:
        try:
            import transformers
            return True
        except ImportError:
            return False
    
    def load(self) -> bool:
        if self._pipeline is not None:
            return True
        
        try:
            from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
            import torch
            
            logger.info(f"Loading transformers model: {self.config.path}")
            
            # Try to load with quantization if specified
            if self.config.quantization:
                from transformers import BitsAndBytesConfig
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16
                )
            else:
                quantization_config = None
            
            self._pipeline = pipeline(
                "text-generation",
                model=self.config.path,
                model_kwargs={
                    "quantization_config": quantization_config,
                    "torch_dtype": torch.float16,
                    "device_map": "auto"
                },
                tokenizer=AutoTokenizer.from_pretrained(self.config.path)
            )
            logger.info("Model loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False
    
    def generate(self, messages: List[ChatMessage], **kwargs) -> str:
        if not self._pipeline:
            if not self.load():
                return "Error: Model not available"
        
        prompt = self._messages_to_prompt(messages)
        
        try:
            output = self._pipeline(
                prompt,
                max_new_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                temperature=kwargs.get("temperature", self.config.temperature),
                do_sample=True,
                pad_token_id=self._pipeline.tokenizer.eos_token_id
            )
            return output[0]["generated_text"][len(prompt):].strip()
        except Exception as e:
            logger.error(f"Generation error: {e}")
            return f"Error: {str(e)}"
    
    def _messages_to_prompt(self, messages: List[ChatMessage]) -> str:
        """Convert messages to prompt."""
        parts = []
        for msg in messages:
            if msg.role == "system":
                parts.append(f"System: {msg.content}")
            elif msg.role == "user":
                parts.append(f"User: {msg.content}")
            elif msg.role == "assistant":
                parts.append(f"Assistant: {msg.content}")
        parts.append("Assistant:")
        return "\n\n".join(parts)


class OpenAICompatibleRunner(BaseModelRunner):
    """OpenAI API compatible runner (also works with Ollama, Together AI, etc.)."""
    
    def __init__(self, config: ModelConfig):
        self.config = config
    
    def is_available(self) -> bool:
        return True  # Always available if we have the URL
    
    def load(self) -> bool:
        return True  # No local loading needed
    
    def generate(self, messages: List[ChatMessage], **kwargs) -> str:
        import requests
        
        api_base = self.config.api_base or "https://api.openai.com/v1"
        headers = {
            "Content-Type": "application/json"
        }
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        
        payload = {
            "model": self.config.name,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "temperature": kwargs.get("temperature", self.config.temperature)
        }
        
        try:
            response = requests.post(
                f"{api_base}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except requests.exceptions.ConnectionError:
            return "Error: Cannot connect to API endpoint"
        except requests.exceptions.Timeout:
            return "Error: Request timed out"
        except Exception as e:
            logger.error(f"API error: {e}")
            return f"Error: {str(e)}"


class AnthropicRunner(BaseModelRunner):
    """Anthropic Claude API runner."""
    
    def __init__(self, config: ModelConfig):
        self.config = config
    
    def is_available(self) -> bool:
        return self.config.api_key is not None
    
    def load(self) -> bool:
        return self.is_available()
    
    def generate(self, messages: List[ChatMessage], **kwargs) -> str:
        import requests
        
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.config.api_key,
            "anthropic-version": "2023-06-01"
        }
        
        # Build Claude-format messages
        claude_messages = []
        for msg in messages:
            if msg.role == "system":
                continue  # System prompt goes in separate field
            claude_messages.append({
                "role": "user" if msg.role == "user" else "assistant",
                "content": msg.content
            })
        
        payload = {
            "model": self.config.name,
            "messages": claude_messages,
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "temperature": kwargs.get("temperature", self.config.temperature)
        }
        
        # Add system prompt if present
        for msg in messages:
            if msg.role == "system":
                payload["system"] = msg.content
                break
        
        try:
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            return f"Error: {str(e)}"


class ModelManager:
    """
    Central manager for all model runners.
    Handles model discovery, loading, and routing.
    """
    
    def __init__(self):
        self._runners: Dict[str, BaseModelRunner] = {}
        self._config: Optional[ModelConfig] = None
        self._available_backends = self._detect_backends()
    
    def _detect_backends(self) -> Dict[str, bool]:
        """Detect which backends are available."""
        backends = {
            "llama_cpp": False,
            "transformers": False,
            "openai": True,  # Always available if we have requests
            "anthropic": True  # Always available if we have requests
        }
        
        try:
            import llama_cpp
            backends["llama_cpp"] = True
            logger.info("llama.cpp backend detected")
        except ImportError:
            pass
        
        try:
            import transformers
            backends["transformers"] = True
            logger.info("transformers backend detected")
        except ImportError:
            pass
        
        return backends
    
    def configure(self, config: ModelConfig) -> bool:
        """Configure the model to use."""
        self._config = config
        
        # Create appropriate runner
        if config.backend == "llama.cpp" or config.backend == "llama_cpp":
            if not self._available_backends["llama_cpp"]:
                logger.error("llama.cpp not available")
                return False
            self._runners[config.name] = LlamaCPPRunner(config)
        
        elif config.backend == "transformers":
            if not self._available_backends["transformers"]:
                logger.error("transformers not available")
                return False
            self._runners[config.name] = TransformersRunner(config)
        
        elif config.backend in ["openai", "ollama", "together", "openrouter", "local"]:
            self._runners[config.name] = OpenAICompatibleRunner(config)
        
        elif config.backend == "anthropic":
            self._runners[config.name] = AnthropicRunner(config)
        
        else:
            logger.error(f"Unknown backend: {config.backend}")
            return False
        
        logger.info(f"Configured model: {config.name} with {config.backend}")
        return True
    
    def get_runner(self, name: Optional[str] = None) -> Optional[BaseModelRunner]:
        """Get a runner by name."""
        if name is None:
            name = self._config.name if self._config else None
        
        return self._runners.get(name)
    
    def generate(self, messages: List[ChatMessage], model_name: Optional[str] = None, **kwargs) -> str:
        """Generate a response using the specified or default model."""
        runner = self.get_runner(model_name)
        if not runner:
            return "Error: No model configured"
        
        if not runner.is_available():
            return "Error: Model not available"
        
        return runner.generate(messages, **kwargs)
    
    def get_available_backends(self) -> Dict[str, bool]:
        """Get which backends are available."""
        return self._available_backends.copy()
    
    def get_current_config(self) -> Optional[ModelConfig]:
        """Get current model configuration."""
        return self._config


# Global model manager instance
model_manager = ModelManager()


def configure_model(config: ModelConfig) -> bool:
    """Configure the global model manager."""
    return model_manager.configure(config)


def get_model_manager() -> ModelManager:
    """Get the global model manager."""
    return model_manager
