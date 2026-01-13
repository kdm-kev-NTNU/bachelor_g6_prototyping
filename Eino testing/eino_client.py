"""
Eino platform client for LLM API calls.

Eino is a Golang-based AI application development framework by CloudWeGo/ByteDance.
This client provides Python integration for Eino platform.

Can also use OpenAI directly if EINO_API_KEY is set to OpenAI key and EINO_BASE_URL is not set.

Documentation: https://www.cloudwego.io/docs/eino/
"""

import os
import json
from typing import List, Dict, Any, Optional
import requests
from dotenv import load_dotenv

load_dotenv()

# Try importing OpenAI for fallback
try:
    from openai import OpenAI as OpenAIClient
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class EinoClient:
    """
    Client for Eino platform LLM API.
    
    Eino supports multiple ChatModel providers (OpenAI, Claude, Gemini, etc.)
    through a unified interface. This client connects to an Eino server instance.
    """
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize Eino client.
        
        Args:
            api_key: Eino/OpenAI API key (from EINO_API_KEY env var if not provided)
            base_url: Eino API base URL (from EINO_BASE_URL env var if not provided)
                     If not set, will use OpenAI directly
        """
        self.api_key = api_key or os.getenv("EINO_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("EINO_BASE_URL") or os.getenv("EINO_SERVER_URL")
        
        # If no base_url is set, assume we're using OpenAI directly
        self.use_openai_directly = not self.base_url
        
        if not self.api_key:
            raise ValueError("EINO_API_KEY eller OPENAI_API_KEY må være satt")
        
        if self.use_openai_directly:
            if not OPENAI_AVAILABLE:
                raise ImportError("OpenAI ikke installert. Installer med: pip install openai")
            self.openai_client = OpenAIClient(api_key=self.api_key)
            print("[INFO] Bruker OpenAI direkte (ingen Eino server konfigurert)")
        else:
            # Use Eino server
            self.base_url = self.base_url.rstrip('/')
            if not self.base_url.endswith('/v1'):
                self.base_url = f"{self.base_url}/v1"
            print(f"[INFO] Bruker Eino server: {self.base_url}")
    
    def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make chat completion request to Eino platform or OpenAI.
        
        Args:
            model: Model name to use
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            response_format: Optional response format (e.g., {"type": "json_object"})
        
        Returns:
            Response dictionary with 'choices' containing message content
        """
        # Use OpenAI directly if no Eino server configured
        if self.use_openai_directly:
            kwargs = {
                "model": model,
                "messages": messages,
                "temperature": temperature
            }
            if max_tokens:
                kwargs["max_tokens"] = max_tokens
            if response_format:
                kwargs["response_format"] = response_format
            
            response = self.openai_client.chat.completions.create(**kwargs)
            
            # Convert to dict format
            return {
                "choices": [{
                    "message": {
                        "content": response.choices[0].message.content
                    }
                }],
                "usage": {
                    "total_tokens": response.usage.total_tokens if response.usage else None
                }
            }
        
        # Use Eino server
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # Add authorization if API key is provided
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        if response_format:
            payload["response_format"] = response_format
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            
            # Normalize response format to match OpenAI format
            if "choices" in result and len(result["choices"]) > 0:
                if "message" not in result["choices"][0]:
                    # If Eino uses different format, adapt it
                    if "content" in result["choices"][0]:
                        result["choices"][0]["message"] = {
                            "content": result["choices"][0]["content"]
                        }
            
            return result
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Eino API feil: {str(e)}")
    
    def embeddings(
        self,
        model: str,
        input_text: str
    ) -> List[float]:
        """
        Get embeddings from Eino platform or OpenAI.
        
        Args:
            model: Embedding model name
            input_text: Text to embed
        
        Returns:
            List of embedding values
        """
        # Use OpenAI directly if no Eino server configured
        if self.use_openai_directly:
            response = self.openai_client.embeddings.create(
                model=model,
                input=input_text
            )
            return response.data[0].embedding
        
        # Use Eino server
        url = f"{self.base_url}/embeddings"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # Add authorization if API key is provided
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        payload = {
            "model": model,
            "input": input_text
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            
            # Normalize response format
            if "data" in result and len(result["data"]) > 0:
                return result["data"][0].get("embedding", [])
            elif "embedding" in result:
                return result["embedding"]
            else:
                raise Exception("Uventet responsformat fra Eino embeddings API")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Eino embeddings API feil: {str(e)}")


# Compatibility wrapper to match OpenAI interface
class EinoOpenAICompat:
    """OpenAI-compatible wrapper for Eino client."""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """Initialize with Eino client."""
        self._client = EinoClient(api_key, base_url)
    
    @property
    def chat(self):
        """Chat completions interface."""
        return self
    
    @property
    def completions(self):
        """Completions interface."""
        return self
    
    def create(self, **kwargs):
        """Create chat completion (OpenAI-compatible)."""
        return self._client.chat_completion(**kwargs)
    
    @property
    def embeddings(self):
        """Embeddings interface."""
        return EmbeddingsWrapper(self._client)


class EmbeddingsWrapper:
    """Wrapper for embeddings interface."""
    
    def __init__(self, client: EinoClient):
        self._client = client
    
    def create(self, **kwargs):
        """Create embeddings (OpenAI-compatible)."""
        model = kwargs.get("model")
        input_text = kwargs.get("input")
        if isinstance(input_text, list):
            input_text = input_text[0]  # Take first if list
        
        embedding = self._client.embeddings(model, input_text)
        
        # Return OpenAI-compatible format
        return type('obj', (object,), {
            'data': [type('obj', (object,), {'embedding': embedding})()]
        })()


def create_eino_client(api_key: Optional[str] = None, base_url: Optional[str] = None):
    """Factory function to create Eino client."""
    return EinoOpenAICompat(api_key, base_url)


if __name__ == "__main__":
    # Test Eino client
    try:
        client = create_eino_client()
        print("[OK] Eino client opprettet")
        
        # Test chat completion
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Du er en hjelpsom assistent."},
                {"role": "user", "content": "Hei, kan du hjelpe meg?"}
            ],
            temperature=0.7,
            max_tokens=100
        )
        
        print(f"Svar: {response['choices'][0]['message']['content']}")
        
    except Exception as e:
        print(f"[ERROR] {e}")
