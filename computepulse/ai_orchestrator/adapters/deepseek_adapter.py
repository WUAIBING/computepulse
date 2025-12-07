"""
DeepSeek AI Model Adapter.

This adapter integrates with DeepSeek models via DashScope's OpenAI-compatible API.
Supports deep thinking mode and web search.
"""

import logging
import time
from datetime import datetime
from typing import Any, Dict, Optional

from .base import AIModelAdapter, AdapterResponse, AdapterError


logger = logging.getLogger(__name__)


class DeepSeekAdapter(AIModelAdapter):
    """Adapter for DeepSeek models via DashScope OpenAI-compatible API."""
    
    DEFAULT_MODEL = "deepseek-v3.2"
    DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    
    def __init__(
        self,
        api_key: str,
        model_name: str = DEFAULT_MODEL,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 60.0,  # DeepSeek thinking can take longer
        max_retries: int = 3,
        enable_thinking: bool = True,
        enable_search: bool = False,
        cost_per_1m_tokens: float = 0.0,
    ):
        """
        Initialize DeepSeek adapter.
        
        Args:
            api_key: DashScope API key
            model_name: Model name (default: deepseek-v3.2)
            base_url: API base URL
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            enable_thinking: Enable deep thinking mode
            enable_search: Enable web search (like Kimi K2)
            cost_per_1m_tokens: Cost per 1M tokens
        """
        super().__init__(
            model_name=model_name,
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
        )
        self.enable_thinking = enable_thinking
        self.enable_search = enable_search
        self._cost_per_1m_tokens = cost_per_1m_tokens
        self._client = None
    
    def _get_client(self):
        """Get or create OpenAI client."""
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
        """Make an async call to DeepSeek model."""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self._call_sync(prompt, **kwargs))
    
    def _call_sync(self, prompt: str, **kwargs) -> AdapterResponse:
        """Synchronous implementation of the API call with thinking support."""
        start_time = time.time()
        
        try:
            client = self._get_client()
            
            system_prompt = kwargs.get("system_prompt",
                "You are DeepSeek, an AI assistant with strong reasoning capabilities. "
                "Analyze problems step by step and provide accurate, well-reasoned responses.")
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            # Build extra_body for special features
            extra_body = {}
            if self.enable_thinking:
                extra_body["enable_thinking"] = True
            if self.enable_search:
                extra_body["enable_search"] = True
            
            # Use streaming to capture thinking process
            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                extra_body=extra_body if extra_body else None,
                stream=True,
            )
            
            # Collect response content
            content = ""
            reasoning_content = ""
            
            for chunk in response:
                delta = chunk.choices[0].delta
                # Capture reasoning/thinking content
                if hasattr(delta, "reasoning_content") and delta.reasoning_content is not None:
                    reasoning_content += delta.reasoning_content
                # Capture final answer content
                if hasattr(delta, "content") and delta.content:
                    content += delta.content
            
            response_time = time.time() - start_time
            
            # Estimate token count (streaming doesn't provide usage)
            token_count = len(prompt.split()) + len(content.split()) + len(reasoning_content.split())
            
            # Include reasoning in metadata
            metadata = {}
            if reasoning_content:
                metadata["reasoning"] = reasoning_content
            
            return AdapterResponse(
                content=content,
                model_name=self.model_name,
                response_time=response_time,
                token_count=token_count,
                cost=self.calculate_cost(token_count),
                timestamp=datetime.now(),
                success=True,
                raw_response=metadata if metadata else None,
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            error_msg = str(e)
            logger.error(f"DeepSeek API error: {error_msg}")
            
            return AdapterResponse(
                content="",
                model_name=self.model_name,
                response_time=response_time,
                token_count=0,
                cost=0.0,
                timestamp=datetime.now(),
                success=False,
                error=error_msg,
            )
    
    def call_sync_non_streaming(self, prompt: str, **kwargs) -> AdapterResponse:
        """Non-streaming call for simpler use cases."""
        start_time = time.time()
        
        try:
            client = self._get_client()
            
            system_prompt = kwargs.get("system_prompt",
                "You are DeepSeek, an AI assistant with strong reasoning capabilities.")
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            extra_body = {}
            if self.enable_search:
                extra_body["enable_search"] = True
            
            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                extra_body=extra_body if extra_body else None,
            )
            
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
                content="",
                model_name=self.model_name,
                response_time=time.time() - start_time,
                token_count=0,
                cost=0.0,
                timestamp=datetime.now(),
                success=False,
                error=str(e),
            )
