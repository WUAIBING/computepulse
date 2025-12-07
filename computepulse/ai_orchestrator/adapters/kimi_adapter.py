"""
Kimi AI Model Adapter.

This adapter integrates with Kimi models via DashScope OpenAI-compatible API.
"""

import logging
import time
from datetime import datetime
from typing import Any, Dict, Optional

from .base import AIModelAdapter, AdapterResponse, AdapterError


logger = logging.getLogger(__name__)


class KimiAdapter(AIModelAdapter):
    """Adapter for Kimi models via DashScope OpenAI-compatible API."""
    
    DEFAULT_MODEL = "Moonshot-Kimi-K2-Instruct"
    DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    
    def __init__(
        self,
        api_key: str,
        model_name: str = DEFAULT_MODEL,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 60.0,
        max_retries: int = 3,
        enable_search: bool = True,
        cost_per_1m_tokens: float = 0.0,
    ):
        """
        Initialize the Kimi adapter.
        
        Args:
            api_key: DashScope API key
            model_name: Model name (default: Moonshot-Kimi-K2-Instruct)
            base_url: DashScope OpenAI-compatible API URL
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            enable_search: Enable web search capability
            cost_per_1m_tokens: Cost per 1M tokens (configurable)
        """
        super().__init__(
            model_name=model_name,
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
        )
        self.enable_search = enable_search
        self._cost_per_1m_tokens = cost_per_1m_tokens
        self._client = None
    
    def _get_client(self):
        """Get or create OpenAI client for DashScope."""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url,
                )
            except ImportError:
                raise AdapterError("openai package is required. Install with: pip install openai")
        return self._client
    
    async def call_async(self, prompt: str, **kwargs) -> AdapterResponse:
        """Make an async call to Kimi via DashScope."""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self._call_sync(prompt, **kwargs))
    
    def _call_sync(self, prompt: str, **kwargs) -> AdapterResponse:
        """Make a synchronous call to Kimi via DashScope."""
        start_time = time.time()
        
        try:
            client = self._get_client()
            
            system_prompt = kwargs.get(
                "system_prompt", 
                "你是Kimi，一个由Moonshot AI提供的智能助手，擅长研究和分析。"
            )
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            # Build request parameters
            request_params = {
                "model": self.model_name,
                "messages": messages,
                "temperature": kwargs.get("temperature", 0.7),
            }
            
            # Enable web search via extra_body
            if self.enable_search:
                request_params["extra_body"] = {"enable_search": True}
            
            response = client.chat.completions.create(**request_params)
            
            response_time = time.time() - start_time
            
            # Extract content
            content = ""
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content or ""
            
            # Extract token count
            token_count = 0
            if hasattr(response, 'usage') and response.usage:
                token_count = response.usage.total_tokens
            
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
            response_time = time.time() - start_time
            logger.error(f"Kimi API call failed: {e}")
            
            return AdapterResponse(
                content="",
                model_name=self.model_name,
                response_time=response_time,
                token_count=0,
                cost=0.0,
                timestamp=datetime.now(),
                success=False,
                error=str(e),
            )
