"""
Base AI Model Adapter interface.

This module defines the abstract base class for all AI model adapters,
providing a common interface for unified access to different AI providers.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional
from datetime import datetime


logger = logging.getLogger(__name__)


class AdapterError(Exception):
    """Base exception for adapter errors."""
    pass


class AdapterTimeoutError(AdapterError):
    """Raised when an adapter call times out."""
    pass


class AdapterAPIError(AdapterError):
    """Raised when an API call fails."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


@dataclass
class AdapterResponse:
    """Response from an AI model adapter."""
    content: str
    model_name: str
    response_time: float
    token_count: int
    cost: float
    timestamp: datetime
    success: bool = True
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "content": self.content,
            "model_name": self.model_name,
            "response_time": self.response_time,
            "token_count": self.token_count,
            "cost": self.cost,
            "timestamp": self.timestamp.isoformat(),
            "success": self.success,
            "error": self.error,
        }


class AIModelAdapter(ABC):
    """
    Abstract base class for AI model adapters.
    
    All AI model adapters must implement this interface to be used
    with the AI Orchestrator system.
    """
    
    def __init__(
        self,
        model_name: str,
        api_key: str,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """
        Initialize the adapter.
        
        Args:
            model_name: Name of the AI model
            api_key: API key for authentication
            base_url: Base URL for the API (optional)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Initial delay between retries (exponential backoff)
        """
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._cost_per_1m_tokens = 0.0
    
    @property
    def cost_per_1m_tokens(self) -> float:
        """Get cost per 1M tokens."""
        return self._cost_per_1m_tokens
    
    @cost_per_1m_tokens.setter
    def cost_per_1m_tokens(self, value: float):
        """Set cost per 1M tokens."""
        self._cost_per_1m_tokens = value
    
    @abstractmethod
    async def call_async(self, prompt: str, **kwargs) -> AdapterResponse:
        """
        Make an async call to the AI model.
        
        Args:
            prompt: The prompt to send to the model
            **kwargs: Additional arguments for the API call
            
        Returns:
            AdapterResponse with the model's response
        """
        pass
    
    def call_sync(self, prompt: str, **kwargs) -> AdapterResponse:
        """
        Make a synchronous call to the AI model.
        
        Args:
            prompt: The prompt to send to the model
            **kwargs: Additional arguments for the API call
            
        Returns:
            AdapterResponse with the model's response
        """
        return asyncio.run(self.call_async(prompt, **kwargs))
    
    async def call_with_retry(self, prompt: str, **kwargs) -> AdapterResponse:
        """
        Make an async call with retry logic and exponential backoff.
        
        Args:
            prompt: The prompt to send to the model
            **kwargs: Additional arguments for the API call
            
        Returns:
            AdapterResponse with the model's response
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                return await self.call_async(prompt, **kwargs)
            except AdapterTimeoutError:
                # Don't retry on timeout
                raise
            except AdapterError as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(
                        f"{self.model_name} attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"{self.model_name} failed after {self.max_retries} attempts: {e}"
                    )
        
        # Return error response if all retries failed
        return AdapterResponse(
            content="",
            model_name=self.model_name,
            response_time=0.0,
            token_count=0,
            cost=0.0,
            timestamp=datetime.now(),
            success=False,
            error=str(last_error) if last_error else "Unknown error",
        )
    
    async def call_with_timeout(self, prompt: str, timeout: Optional[float] = None, **kwargs) -> AdapterResponse:
        """
        Make an async call with timeout handling.
        
        Args:
            prompt: The prompt to send to the model
            timeout: Custom timeout (uses default if not specified)
            **kwargs: Additional arguments for the API call
            
        Returns:
            AdapterResponse with the model's response
        """
        effective_timeout = timeout or self.timeout
        
        try:
            return await asyncio.wait_for(
                self.call_with_retry(prompt, **kwargs),
                timeout=effective_timeout
            )
        except asyncio.TimeoutError:
            logger.warning(f"{self.model_name} timed out after {effective_timeout}s")
            return AdapterResponse(
                content="",
                model_name=self.model_name,
                response_time=effective_timeout,
                token_count=0,
                cost=0.0,
                timestamp=datetime.now(),
                success=False,
                error=f"Timeout after {effective_timeout}s",
            )
    
    def calculate_cost(self, token_count: int) -> float:
        """
        Calculate the cost for a given number of tokens.
        
        Args:
            token_count: Number of tokens used
            
        Returns:
            Cost in dollars
        """
        return (token_count / 1_000_000) * self._cost_per_1m_tokens
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model_name={self.model_name!r})"
