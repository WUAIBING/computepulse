"""
GLM AI Model Adapter.

This adapter integrates with Zhipu AI's GLM models.
"""

import logging
import time
from datetime import datetime
from typing import Any, Dict, Optional

from .base import AIModelAdapter, AdapterResponse, AdapterError


logger = logging.getLogger(__name__)


class GLMAdapter(AIModelAdapter):
    """Adapter for Zhipu AI GLM models."""
    
    DEFAULT_MODEL = "glm-4-flash"
    DEFAULT_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"
    
    def __init__(
        self,
        api_key: str,
        model_name: str = DEFAULT_MODEL,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
        max_retries: int = 3,
        enable_web_search: bool = True,
        cost_per_1m_tokens: float = 0.0,  # Set actual cost based on Zhipu pricing
    ):
        super().__init__(
            model_name=model_name,
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
        )
        self.enable_web_search = enable_web_search
        self._cost_per_1m_tokens = cost_per_1m_tokens
        self._client = None
    
    def _get_client(self):
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            except ImportError:
                raise AdapterError("openai package is required")
        return self._client
    
    async def call_async(self, prompt: str, **kwargs) -> AdapterResponse:
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self._call_sync(prompt, **kwargs))
    
    def _call_sync(self, prompt: str, **kwargs) -> AdapterResponse:
        start_time = time.time()
        try:
            client = self._get_client()
            system_prompt = kwargs.get("system_prompt", "You are GLM, an AI analyst with web search capabilities.")
            
            request_params = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "temperature": kwargs.get("temperature", 0.7),
            }
            
            if self.enable_web_search:
                request_params["tools"] = [{"type": "web_search", "web_search": {"enable": True}}]
            
            response = client.chat.completions.create(**request_params)
            
            response_time = time.time() - start_time
            content = response.choices[0].message.content if response.choices else ""
            token_count = response.usage.total_tokens if hasattr(response, 'usage') and response.usage else 0
            
            return AdapterResponse(
                content=content,
                model_name=self.model_name,
                response_time=response_time,
                token_count=token_count,
                cost=self.calculate_cost(token_count),
                timestamp=datetime.now(),
                success=True,
            )
        except Exception as e:
            return AdapterResponse(
                content="", model_name=self.model_name, response_time=time.time() - start_time,
                token_count=0, cost=0.0, timestamp=datetime.now(), success=False, error=str(e),
            )
