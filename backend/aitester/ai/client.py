"""
AI Client implementations for test generation and failure analysis.
Supports Google Gemini and local Ollama, selected dynamically via config.
"""

import json
import logging
import os
from abc import ABC, abstractmethod
from typing import Any

import httpx

from aitester.core.config import settings
from aitester.core.exceptions import AIEngineError, AIRateLimitError

logger = logging.getLogger("aitester.ai")


class BaseAIClient(ABC):
    """Abstract base class for AI model interactions."""

    @abstractmethod
    async def generate_test_payload(self, prompt: str) -> dict[str, Any]:
        """Sends a prompt asking for a JSON array of test case payloads."""
        pass

    @abstractmethod
    async def generate_with_retry(self, prompt: str, validator: Any, max_retries: int = 3) -> Any:
        """Sends a prompt, validates the output, and retries on failure."""
        pass


class GeminiClient(BaseAIClient):
    """Client for interacting with Google's Gemini API via the google-genai SDK."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        if not self.api_key:
            logger.warning("GEMINI_API_KEY is not set. Gemini operations will fail.")
            self.client = None
        else:
            from google import genai
            self.client = genai.Client(api_key=self.api_key)

        self.model_id = settings.GEMINI_MODEL

    async def generate_test_payload(self, prompt: str) -> dict[str, Any]:
        if not self.client:
            raise AIEngineError("GEMINI_API_KEY is missing. Cannot call AI model.")

        from google.genai import types as genai_types

        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )
            content = response.text
            if not content:
                raise AIEngineError("AI returned an empty response.")

            result: dict[str, Any] = json.loads(content)
            return result

        except AIEngineError:
            raise
        except Exception as e:
            if "ResourceExhausted" in type(e).__name__ or "429" in str(e):
                raise AIRateLimitError("Gemini API rate limit exceeded.") from e
            logger.error(f"Unexpected AI error: {e}")
            raise AIEngineError(f"Unexpected AI engine error: {e}") from e

    async def generate_with_retry(self, prompt: str, validator: Any, max_retries: int = 3) -> Any:
        from aitester.core.exceptions import AIOutputValidationError
        from google.genai import types as genai_types

        if not self.client:
            raise AIEngineError("GEMINI_API_KEY is missing. Cannot call AI model.")

        last_error: Exception | None = None
        for attempt in range(max_retries):
            try:
                response = await self.client.aio.models.generate_content(
                    model=self.model_id,
                    contents=prompt,
                    config=genai_types.GenerateContentConfig(
                        response_mime_type="application/json",
                    ),
                )
                content = response.text
                if not content:
                    raise AIOutputValidationError("AI returned an empty response.")

                validated: Any = validator(content)
                return validated

            except AIOutputValidationError as e:
                last_error = e
                logger.warning(f"AI output validation failed on attempt {attempt + 1}: {e}")
            except (AIEngineError, AIRateLimitError):
                raise
            except Exception as e:
                if "ResourceExhausted" in type(e).__name__ or "429" in str(e):
                    raise AIRateLimitError("Gemini API rate limit exceeded.") from e
                last_error = e
                logger.warning(f"Unexpected AI error on attempt {attempt + 1}: {e}")

        raise last_error or AIEngineError("Failed to generate valid AI output after max retries.")


class OllamaClient(BaseAIClient):
    """Client for interacting with a local Ollama instance."""

    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.model_id = settings.OLLAMA_MODEL

    async def _post_generate(self, prompt: str) -> str:
        """Helper to POST to Ollama API"""
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model_id,
            "prompt": prompt,
            "format": "json",
            "stream": False,
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                return data.get("response", "")
        except httpx.RequestError as e:
            raise AIEngineError(f"Failed to connect to Ollama at {self.base_url}: {e}") from e
        except httpx.HTTPStatusError as e:
            raise AIEngineError(f"Ollama returned an error status: {e.response.status_code}") from e
        except Exception as e:
            raise AIEngineError(f"Unexpected Ollama error: {e}") from e

    async def generate_test_payload(self, prompt: str) -> dict[str, Any]:
        content = await self._post_generate(prompt)
        if not content:
            raise AIEngineError("Ollama returned an empty response.")

        try:
            result: dict[str, Any] = json.loads(content)
            return result
        except json.JSONDecodeError as e:
            raise AIEngineError("Ollama response was not valid JSON.") from e

    async def generate_with_retry(self, prompt: str, validator: Any, max_retries: int = 3) -> Any:
        from aitester.core.exceptions import AIOutputValidationError

        last_error: Exception | None = None
        for attempt in range(max_retries):
            try:
                content = await self._post_generate(prompt)
                if not content:
                    raise AIOutputValidationError("Ollama returned an empty response.")

                validated: Any = validator(content)
                return validated

            except AIOutputValidationError as e:
                last_error = e
                logger.warning(f"Ollama output validation failed on attempt {attempt + 1}: {e}")
            except AIEngineError:
                raise
            except Exception as e:
                last_error = e
                logger.warning(f"Unexpected Ollama error on attempt {attempt + 1}: {e}")

        raise last_error or AIEngineError("Failed to generate valid Ollama output after max retries.")


def get_ai_client() -> BaseAIClient:
    """
    Factory function to return the correct AI client based on configuration.
    """
    provider = settings.effective_ai_provider
    if provider == "gemini":
        return GeminiClient()
    elif provider == "ollama":
        return OllamaClient()
    else:
        # Fallback to Ollama for local dev if unknown
        logger.warning(f"Unknown AI provider '{provider}', falling back to Ollama.")
        return OllamaClient()
