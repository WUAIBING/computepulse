"""
Parallel Executor - Executes AI model calls concurrently with asyncio.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
import uuid

from .config import OrchestratorConfig
from .models import AIModel, Request, Response

logger = logging.getLogger(__name__)


class ParallelExecutor:
    """
    Executes multiple AI model calls in parallel using asyncio.

    Features:
    - Async/await support for concurrent execution
    - Per-model timeout handling
    - Early result processing (process results as they arrive)
    - Exception handling and logging
    - Performance tracking
    """

    def __init__(self, config: OrchestratorConfig):
        """
        Initialize the parallel executor.

        Args:
            config: Orchestrator configuration
        """
        self.config = config
        logger.info("Parallel Executor initialized")

    async def execute(
        self,
        request: Request,
        models: List[AIModel],
        model_call_func: Callable[[AIModel, Request], Response]
    ) -> Dict[str, Response]:
        """
        Execute AI model calls in parallel.

        Args:
            request: The request to process
            models: List of AI models to call
            model_call_func: Function to call for each model (model, request) -> Response

        Returns:
            Dictionary mapping model names to responses

        Raises:
            RuntimeError: If no models provided or all calls fail
        """
        if not models:
            raise ValueError("No models provided for execution")

        logger.info(f"Executing {len(models)} model calls in parallel")

        try:
            # Create tasks for all model calls
            tasks = {}
            for model in models:
                task_id = str(uuid.uuid4())
                task = asyncio.create_task(
                    self._execute_single_model(model, request, model_call_func)
                )
                tasks[task_id] = (model.name, task)

            # Wait for all tasks with timeout
            responses = {}
            completed = set()
            timeout_occurred = False

            while tasks and not timeout_occurred:
                # Wait for at least one task to complete
                done, pending = await asyncio.wait(
                    [task for _, task in tasks.values()],
                    return_when=asyncio.FIRST_COMPLETED,
                    timeout=self.config.model_timeout_seconds
                )

                # Process completed tasks
                for task in done:
                    try:
                        result = await task
                        if result:
                            responses[result.model_name] = result
                            completed.add(task)

                        # Remove from pending tasks
                        for task_id, (model_name, task) in list(tasks.items()):
                            if task == task:
                                del tasks[task_id]
                                break

                    except asyncio.TimeoutError:
                        logger.warning(f"Task timed out")
                        completed.add(task)
                        timeout_occurred = True

                    except Exception as e:
                        logger.error(f"Task failed with error: {e}")
                        completed.add(task)

                # Check if we've received enough results
                if self.config.enable_early_result_processing and len(responses) >= 2:
                    logger.info("Received enough results, cancelling remaining tasks")
                    for task in pending:
                        task.cancel()
                    break

                # Update remaining tasks
                remaining_tasks = {
                    task_id: (model_name, task)
                    for task_id, (model_name, task) in tasks.items()
                    if task not in completed
                }
                tasks = remaining_tasks

            # Cancel any remaining tasks
            for task_id, (model_name, task) in tasks.items():
                logger.debug(f"Cancelling task for {model_name}")
                task.cancel()

            # Check if we have any responses
            if not responses:
                raise RuntimeError("All model calls failed or timed out")

            logger.info(f"Received {len(responses)} successful responses")
            return responses

        except Exception as e:
            logger.error(f"Error in parallel execution: {e}")
            raise

    async def _execute_single_model(
        self,
        model: AIModel,
        request: Request,
        model_call_func: Callable[[AIModel, Request], Response]
    ) -> Optional[Response]:
        """
        Execute a single model call with error handling.

        Args:
            model: The AI model to call
            request: The request to process
            model_call_func: Function to call for the model

        Returns:
            Response object or None if failed
        """
        start_time = datetime.now()

        try:
            logger.debug(f"Calling model: {model.name}")

            # Call the model (may be sync or async)
            if asyncio.iscoroutinefunction(model_call_func):
                result = await model_call_func(model, request)
            else:
                result = await asyncio.to_thread(model_call_func, model, request)

            # Ensure we have a valid response
            if not result:
                logger.warning(f"Model {model.name} returned empty result")
                return Response(
                    model_name=model.name,
                    content="",
                    response_time=0.0,
                    token_count=0,
                    cost=0.0,
                    success=False,
                    error="Empty response"
                )

            return result

        except asyncio.TimeoutError:
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.warning(f"Model {model.name} timed out after {elapsed:.2f}s")
            return Response(
                model_name=model.name,
                content="",
                response_time=elapsed,
                token_count=0,
                cost=0.0,
                success=False,
                error="Timeout"
            )

        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.error(f"Model {model.name} failed: {e}")
            return Response(
                model_name=model.name,
                content="",
                response_time=elapsed,
                token_count=0,
                cost=0.0,
                success=False,
                error=str(e)
            )

    async def execute_with_fallback(
        self,
        request: Request,
        primary_models: List[AIModel],
        fallback_models: List[AIModel],
        model_call_func: Callable[[AIModel, Request], Response]
    ) -> Dict[str, Response]:
        """
        Execute with fallback: try primary models first, then fallback if needed.

        Args:
            request: The request to process
            primary_models: Primary models to try first
            fallback_models: Fallback models if primary fails
            model_call_func: Function to call for each model

        Returns:
            Dictionary mapping model names to responses
        """
        logger.info(f"Trying {len(primary_models)} primary models")

        try:
            # Try primary models
            responses = await self.execute(request, primary_models, model_call_func)

            # If we got enough responses, return them
            if len(responses) >= 2:
                return responses

            # Otherwise, add fallback models
            logger.info("Primary models insufficient, adding fallback models")
            fallback_responses = await self.execute(request, fallback_models, model_call_func)
            responses.update(fallback_responses)

            return responses

        except Exception as e:
            logger.error(f"Primary models failed: {e}")

            # If primary completely failed, try all fallback models
            logger.info("Falling back to fallback models")
            return await self.execute(request, fallback_models, model_call_func)
