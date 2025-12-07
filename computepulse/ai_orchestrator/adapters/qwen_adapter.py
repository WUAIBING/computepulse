"""
Qwen AI Model Adapter.

This adapter integrates with Alibaba's DashScope API for Qwen models using native dashscope SDK.
"""

import logging
import time
from datetime import datetime
from typing import Any, Dict, Optional

from .base import AIModelAdapter, AdapterResponse, AdapterError


logger = logging.getLogger(__name__)


class QwenAdapter(AIModelAdapter):
    """Adapter for Alibaba Qwen models via DashScope native API."""
    
    DEFAULT_MODEL = "qwen3-max"
    
    def __init__(
        self,
        api_key: str,
        model_name: str = DEFAULT_MODEL,
        base_url: Optional[str] = None,  # Not used for native dashscope
        timeout: float = 30.0,
        max_retries: int = 3,
        enable_search: bool = True,
        cost_per_1m_tokens: float = 0.0,
    ):
        """
        Initialize Qwen adapter.
        
        Args:
            api_key: DashScope API key
            model_name: Model name (default: qwen3-max)
            base_url: Not used for native dashscope SDK
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            enable_search: Enable web search capability
            cost_per_1m_tokens: Cost per 1M tokens
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
    
    async def call_async(self, prompt: str, **kwargs) -> AdapterResponse:
        """Make an async call to Qwen model."""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self._call_sync(prompt, **kwargs))
    
    def _call_sync(self, prompt: str, **kwargs) -> AdapterResponse:
        """Synchronous implementation using dashscope.Generation.call."""
        start_time = time.time()
        
        try:
            import dashscope
            
            system_prompt = kwargs.get("system_prompt", 
                "You are Qwen, a helpful AI assistant. Provide accurate and detailed responses.")
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            # Call using native dashscope SDK
            response = dashscope.Generation.call(
                api_key=self.api_key,
                model=self.model_name,
                messages=messages,
                enable_search=self.enable_search,
                result_format="message"
            )
            
            response_time = time.time() - start_time
            
            # Extract content from response
            content = ""
            if response.output and response.output.choices:
                content = response.output.choices[0].message.content
            
            # Extract token usage
            token_count = 0
            if response.usage:
                token_count = response.usage.total_tokens
            
            cost = self.calculate_cost(token_count)
            
            return AdapterResponse(
                content=content,
                model_name=self.model_name,
                response_time=response_time,
                token_count=token_count,
                cost=cost,
                timestamp=datetime.now(),
                success=True,
                raw_response=response if hasattr(response, '__dict__') else None,
            )
            
        except ImportError:
            raise AdapterError("dashscope package is required. Install with: pip install dashscope")
        except Exception as e:
            response_time = time.time() - start_time
            error_msg = str(e)
            logger.error(f"Qwen API error: {error_msg}")
            
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
