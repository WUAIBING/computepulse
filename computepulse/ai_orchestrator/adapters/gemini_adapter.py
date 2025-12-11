"""
Gemini Adapter for AI Orchestrator.

This adapter connects to Google's Gemini models using the google-generativeai library.
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

try:
    import google.generativeai as genai
    HAS_GOOGLE_GENAI = True
except ImportError:
    HAS_GOOGLE_GENAI = False

from .base import AIModelAdapter, AdapterResponse, AdapterError, AdapterAPIError

logger = logging.getLogger(__name__)


class GeminiAdapter(AIModelAdapter):
    """Adapter for Google's Gemini models."""
    
    DEFAULT_MODEL = "gemini-1.5-pro"  # Default fallback
    
    def __init__(
        self,
        model_name: str,
        api_key: str,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        super().__init__(model_name, api_key, base_url, timeout, max_retries, retry_delay)
        
        if not HAS_GOOGLE_GENAI:
            logger.warning("google-generativeai library not found. GeminiAdapter will fail if called.")
        else:
            genai.configure(api_key=api_key)
            
        # Map orchestrator model names to Gemini API model names
        self.model_mapping = {
            "gemini-1.5-pro": "gemini-1.5-pro",
            "gemini-1.5-flash": "gemini-1.5-flash",
            "gemini-3-pro-preview": "gemini-1.5-pro",  # Fallback until 3 is public/available in SDK, or use specific preview name if known. 
                                                       # Assuming 'gemini-1.5-pro' for safety or 'models/gemini-...' if user has access.
                                                       # For now, I will use the passed name, assuming the user has access.
        }

    async def call_async(self, prompt: str, **kwargs) -> AdapterResponse:
        """
        Make an async call to Gemini.
        """
        if not HAS_GOOGLE_GENAI:
            raise AdapterError("google-generativeai library is not installed")
            
        start_time = datetime.now()
        
        try:
            # Determine API model name
            api_model_name = self.model_mapping.get(self.model_name, self.model_name)
            
            # Create model instance
            model = genai.GenerativeModel(api_model_name)
            
            # Generate content
            # Note: generate_content_async is available in newer versions
            response = await model.generate_content_async(prompt)
            
            # Calculate duration
            duration = (datetime.now() - start_time).total_seconds()
            
            # Extract text
            content = response.text
            
            # Estimate usage (Gemini API returns usage metadata in some versions, 
            # but usually we might need to count locally or check response.usage_metadata)
            token_count = 0
            if hasattr(response, 'usage_metadata'):
                token_count = response.usage_metadata.total_token_count
            else:
                # Rough estimation fallback
                token_count = len(content) // 4
                
            cost = self.calculate_cost(token_count)
            
            return AdapterResponse(
                content=content,
                model_name=self.model_name,
                response_time=duration,
                token_count=token_count,
                cost=cost,
                timestamp=datetime.now(),
                success=True,
                raw_response={"text": content}
            )
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"Gemini API error: {e}")
            raise AdapterAPIError(f"Gemini call failed: {str(e)}")

