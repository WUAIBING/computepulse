"""
MiniMax AI Model Adapter.

This adapter integrates with MiniMax AI models.
"""

import logging
import time
import requests
from datetime import datetime
from typing import Any, Dict, Optional

from .base import AIModelAdapter, AdapterResponse, AdapterError


logger = logging.getLogger(__name__)


class MiniMaxAdapter(AIModelAdapter):
    """Adapter for MiniMax AI models."""
    
    DEFAULT_MODEL = "abab6.5s-chat"
    DEFAULT_BASE_URL = "https://api.minimax.chat/v1/text/chatcompletion_v2"
    
    def __init__(
        self,
        api_key: str,
        model_name: str = DEFAULT_MODEL,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
        max_retries: int = 3,
        cost_per_1m_tokens: float = 0.0,  # Set actual cost based on MiniMax pricing
    ):
        super().__init__(
            model_name=model_name,
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
        )
        self._cost_per_1m_tokens = cost_per_1m_tokens
    
    async def call_async(self, prompt: str, **kwargs) -> AdapterResponse:
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self._call_sync(prompt, **kwargs))
    
    def _call_sync(self, prompt: str, **kwargs) -> AdapterResponse:
        start_time = time.time()
        try:
            system_prompt = kwargs.get("system_prompt", "You are MiniMax, a strategic AI assistant.")
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "temperature": kwargs.get("temperature", 0.7),
            }
            
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            response_time = time.time() - start_time
            content = ""
            if "choices" in data and data["choices"]:
                content = data["choices"][0].get("message", {}).get("content", "")
            
            token_count = data.get("usage", {}).get("total_tokens", 0)
            
            return AdapterResponse(
                content=content,
                model_name=self.model_name,
                response_time=response_time,
                token_count=token_count,
                cost=self.calculate_cost(token_count),
                timestamp=datetime.now(),
                success=True,
                raw_response=data,
            )
        except Exception as e:
            return AdapterResponse(
                content="", model_name=self.model_name, response_time=time.time() - start_time,
                token_count=0, cost=0.0, timestamp=datetime.now(), success=False, error=str(e),
            )
