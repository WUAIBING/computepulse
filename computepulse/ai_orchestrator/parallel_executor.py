"""
Parallel Execution Layer for the AI Orchestrator system.

This module implements concurrent execution of multiple AI model calls
to minimize latency and maximize throughput.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from .adapters.base import AIModelAdapter, AdapterResponse


logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of parallel execution."""
    responses: Dict[str, AdapterResponse]
    total_time: float
    successful_models: List[str]
    failed_models: List[str]
    first_response_time: Optional[float] = None
    
    def to_dict(self) -> dict:
        return {
            "responses": {k: v.to_dict() for k, v in self.responses.items()},
            "total_time": self.total_time,
            "successful_models": self.successful_models,
            "failed_models": self.failed_models,
            "first_response_time": self.first_response_time,
        }


class ParallelExecutor:
    """
    Executes multiple AI model calls concurrently.
    
    Features:
    - Async parallel execution
    - Per-model timeout handling
    - Early result processing
    - Exception handling and logging
    """
    
    def __init__(
        self,
        adapters: Dict[str, AIModelAdapter],
        default_timeout: float = 60.0,
    ):
        """
        Initialize the parallel executor.
        
        Args:
            adapters: Dictionary mapping model names to adapters
            default_timeout: Default timeout per model in seconds
        """
        self.adapters = adapters
        self.default_timeout = default_timeout
    
    async def execute_parallel(
        self,
        model_names: List[str],
        prompt: str,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> ExecutionResult:
        """
        Execute AI model calls in parallel.
        
        Args:
            model_names: List of model names to call
            prompt: The prompt to send to each model
            timeout: Maximum wait time per model
            **kwargs: Additional arguments for the API calls
            
        Returns:
            ExecutionResult with responses from all models
        """
        effective_timeout = timeout or self.default_timeout
        start_time = time.time()
        first_response_time = None
        
        # Filter to available adapters
        available = [name for name in model_names if name in self.adapters]
        
        if not available:
            logger.warning(f"No adapters available for models: {model_names}")
            return ExecutionResult(
                responses={},
                total_time=0.0,
                successful_models=[],
                failed_models=model_names,
            )
        
        # Create tasks for all models
        tasks = []
        for name in available:
            task = self._call_model_with_timeout(
                name, prompt, effective_timeout, **kwargs
            )
            tasks.append((name, task))
        
        # Execute all tasks concurrently
        responses: Dict[str, AdapterResponse] = {}
        successful = []
        failed = []
        
        # Use asyncio.as_completed for early result processing
        task_map = {asyncio.create_task(task): name for name, task in tasks}
        
        for completed_task in asyncio.as_completed(task_map.keys()):
            try:
                result = await completed_task
                name = task_map[completed_task]
                responses[name] = result
                
                if result.success:
                    successful.append(name)
                    # Record first successful response time
                    if first_response_time is None:
                        first_response_time = time.time() - start_time
                else:
                    failed.append(name)
                    
            except Exception as e:
                # Find which model this was
                name = task_map.get(completed_task, "unknown")
                logger.error(f"Task for {name} raised exception: {e}")
                failed.append(name)
        
        # Add models that weren't in available adapters to failed
        for name in model_names:
            if name not in available:
                failed.append(name)
        
        total_time = time.time() - start_time
        
        logger.info(
            f"Parallel execution completed: {len(successful)} successful, "
            f"{len(failed)} failed, total time: {total_time:.2f}s"
        )
        
        return ExecutionResult(
            responses=responses,
            total_time=total_time,
            successful_models=successful,
            failed_models=failed,
            first_response_time=first_response_time,
        )
    
    async def _call_model_with_timeout(
        self,
        model_name: str,
        prompt: str,
        timeout: float,
        **kwargs,
    ) -> AdapterResponse:
        """
        Call a single model with timeout handling.
        
        Args:
            model_name: Name of the model to call
            prompt: The prompt to send
            timeout: Maximum wait time
            **kwargs: Additional arguments
            
        Returns:
            AdapterResponse from the model
        """
        adapter = self.adapters.get(model_name)
        if not adapter:
            return AdapterResponse(
                content="",
                model_name=model_name,
                response_time=0.0,
                token_count=0,
                cost=0.0,
                timestamp=datetime.now(),
                success=False,
                error=f"No adapter found for model: {model_name}",
            )
        
        try:
            return await asyncio.wait_for(
                adapter.call_async(prompt, **kwargs),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.warning(f"{model_name} timed out after {timeout}s")
            return AdapterResponse(
                content="",
                model_name=model_name,
                response_time=timeout,
                token_count=0,
                cost=0.0,
                timestamp=datetime.now(),
                success=False,
                error=f"Timeout after {timeout}s",
            )
        except Exception as e:
            logger.error(f"{model_name} failed with error: {e}")
            return AdapterResponse(
                content="",
                model_name=model_name,
                response_time=0.0,
                token_count=0,
                cost=0.0,
                timestamp=datetime.now(),
                success=False,
                error=str(e),
            )
    
    async def execute_with_early_return(
        self,
        model_names: List[str],
        prompt: str,
        min_responses: int = 1,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> ExecutionResult:
        """
        Execute models and return as soon as minimum responses are received.
        
        Args:
            model_names: List of model names to call
            prompt: The prompt to send
            min_responses: Minimum number of successful responses needed
            timeout: Maximum wait time per model
            **kwargs: Additional arguments
            
        Returns:
            ExecutionResult with available responses
        """
        effective_timeout = timeout or self.default_timeout
        start_time = time.time()
        first_response_time = None
        
        available = [name for name in model_names if name in self.adapters]
        
        if not available:
            return ExecutionResult(
                responses={},
                total_time=0.0,
                successful_models=[],
                failed_models=model_names,
            )
        
        responses: Dict[str, AdapterResponse] = {}
        successful = []
        failed = []
        
        # Create tasks
        tasks = {
            asyncio.create_task(
                self._call_model_with_timeout(name, prompt, effective_timeout, **kwargs)
            ): name
            for name in available
        }
        
        pending = set(tasks.keys())
        
        while pending and len(successful) < min_responses:
            done, pending = await asyncio.wait(
                pending,
                return_when=asyncio.FIRST_COMPLETED
            )
            
            for task in done:
                name = tasks[task]
                try:
                    result = task.result()
                    responses[name] = result
                    
                    if result.success:
                        successful.append(name)
                        if first_response_time is None:
                            first_response_time = time.time() - start_time
                    else:
                        failed.append(name)
                except Exception as e:
                    logger.error(f"Task for {name} raised exception: {e}")
                    failed.append(name)
        
        # Cancel remaining tasks if we have enough responses
        for task in pending:
            task.cancel()
            name = tasks[task]
            # Don't add to failed - they were cancelled, not failed
        
        total_time = time.time() - start_time
        
        return ExecutionResult(
            responses=responses,
            total_time=total_time,
            successful_models=successful,
            failed_models=failed,
            first_response_time=first_response_time,
        )
    
    def add_adapter(self, name: str, adapter: AIModelAdapter) -> None:
        """Add an adapter to the executor."""
        self.adapters[name] = adapter
        logger.info(f"Added adapter for {name}")
    
    def remove_adapter(self, name: str) -> None:
        """Remove an adapter from the executor."""
        if name in self.adapters:
            del self.adapters[name]
            logger.info(f"Removed adapter for {name}")
    
    def get_available_models(self) -> List[str]:
        """Get list of available model names."""
        return list(self.adapters.keys())
