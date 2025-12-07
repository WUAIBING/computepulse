"""
Async Storage Manager for non-blocking file I/O operations.

Provides async versions of storage operations for use in async contexts.
Uses aiofiles for non-blocking file operations.
"""

import asyncio
import json
import os
import shutil
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import logging

from .models import TaskType, PerformanceRecord, ConfidenceScore
from .config import OrchestratorConfig


logger = logging.getLogger(__name__)


class AsyncStorageManager:
    """
    Async storage manager for non-blocking persistence operations.

    Uses asyncio and aiofiles for non-blocking file I/O.
    Falls back to thread pool execution when aiofiles is not available.
    """

    def __init__(self, config: OrchestratorConfig):
        self.config = config
        self.confidence_scores_path = config.confidence_scores_path
        self.performance_history_path = config.performance_history_path

        # In-memory cache
        self._memory_scores: Dict[Tuple[str, TaskType], float] = {}
        self._memory_records: List[PerformanceRecord] = []

        # Write buffer for batching
        self._write_buffer: List[PerformanceRecord] = []
        self._buffer_lock = asyncio.Lock()
        self._flush_interval = 5.0  # seconds
        self._max_buffer_size = 100

        # Background flush task
        self._flush_task: Optional[asyncio.Task] = None

        # Check if aiofiles is available
        self._use_aiofiles = False
        try:
            import aiofiles
            self._use_aiofiles = True
        except ImportError:
            logger.warning("aiofiles not installed, using thread pool for async I/O")

    async def initialize(self) -> None:
        """Initialize storage files and start background tasks."""
        os.makedirs(self.config.storage_dir, exist_ok=True)

        # Initialize files
        await self._initialize_storage_files()

        # Start background flush task
        self._flush_task = asyncio.create_task(self._flush_loop())
        logger.info("AsyncStorageManager initialized")

    async def shutdown(self) -> None:
        """Shutdown and flush pending writes."""
        # Stop flush task
        if self._flush_task and not self._flush_task.done():
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass

        # Flush remaining buffer
        await self.flush_buffer()
        logger.info("AsyncStorageManager shutdown complete")

    async def _initialize_storage_files(self) -> None:
        """Initialize storage files if they don't exist."""
        if not os.path.exists(self.confidence_scores_path):
            initial_data = {
                "version": "1.1",
                "last_updated": datetime.now().isoformat(),
                "scores": {}
            }
            await self._write_json(self.confidence_scores_path, initial_data)
            logger.info(f"Initialized confidence scores file: {self.confidence_scores_path}")

        if not os.path.exists(self.performance_history_path):
            await self._write_file(self.performance_history_path, "")
            logger.info(f"Initialized performance history file: {self.performance_history_path}")

    async def _read_file(self, path: str) -> str:
        """Read file contents asynchronously."""
        if self._use_aiofiles:
            import aiofiles
            async with aiofiles.open(path, 'r', encoding='utf-8') as f:
                return await f.read()
        else:
            # Fallback to thread pool
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                lambda: open(path, 'r', encoding='utf-8').read()
            )

    async def _write_file(self, path: str, content: str) -> None:
        """Write file contents asynchronously."""
        if self._use_aiofiles:
            import aiofiles
            async with aiofiles.open(path, 'w', encoding='utf-8') as f:
                await f.write(content)
        else:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: open(path, 'w', encoding='utf-8').write(content)
            )

    async def _append_file(self, path: str, content: str) -> None:
        """Append to file asynchronously."""
        if self._use_aiofiles:
            import aiofiles
            async with aiofiles.open(path, 'a', encoding='utf-8') as f:
                await f.write(content)
        else:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: open(path, 'a', encoding='utf-8').write(content)
            )

    async def _read_json(self, path: str) -> Dict[str, Any]:
        """Read and parse JSON file asynchronously."""
        content = await self._read_file(path)
        return json.loads(content)

    async def _write_json(self, path: str, data: Any) -> None:
        """Write JSON data asynchronously with atomic write."""
        temp_path = f"{path}.tmp"
        content = json.dumps(data, indent=2, ensure_ascii=False)
        await self._write_file(temp_path, content)

        # Atomic rename (sync operation, but very fast)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: shutil.move(temp_path, path))

    async def save_confidence_scores(self, scores: List[ConfidenceScore]) -> bool:
        """
        Save confidence scores asynchronously.

        Args:
            scores: List of ConfidenceScore objects

        Returns:
            True if successful
        """
        try:
            # Update memory cache
            self._memory_scores = {
                (s.model_name, s.task_type): s.score for s in scores
            }

            # Serialize
            serializable_scores = {}
            for score in scores:
                key = f"{score.model_name}_{score.task_type.value}"
                serializable_scores[key] = {
                    "score": score.score,
                    "sample_count": score.sample_count,
                    "last_updated": score.last_updated.isoformat(),
                }

            data = {
                "version": "1.1",
                "last_updated": datetime.now().isoformat(),
                "scores": serializable_scores
            }

            await self._write_json(self.confidence_scores_path, data)
            logger.info(f"Async saved {len(scores)} confidence scores")
            return True

        except Exception as e:
            logger.error(f"Async save confidence scores failed: {e}")
            return False

    async def load_confidence_scores(self) -> List[ConfidenceScore]:
        """
        Load confidence scores asynchronously.

        Returns:
            List of ConfidenceScore objects
        """
        if not os.path.exists(self.confidence_scores_path):
            return []

        try:
            data = await self._read_json(self.confidence_scores_path)
            scores = []

            for key, value in data.get("scores", {}).items():
                for task_type in TaskType:
                    suffix = f"_{task_type.value}"
                    if key.endswith(suffix):
                        model_name = key[:-len(suffix)]

                        if isinstance(value, dict):
                            score = ConfidenceScore(
                                model_name=model_name,
                                task_type=task_type,
                                score=value["score"],
                                sample_count=value.get("sample_count", 0),
                                last_updated=datetime.fromisoformat(value["last_updated"]) if "last_updated" in value else datetime.now(),
                            )
                        else:
                            score = ConfidenceScore(
                                model_name=model_name,
                                task_type=task_type,
                                score=float(value),
                            )
                        scores.append(score)
                        break

            # Update memory cache
            self._memory_scores = {
                (s.model_name, s.task_type): s.score for s in scores
            }

            logger.info(f"Async loaded {len(scores)} confidence scores")
            return scores

        except Exception as e:
            logger.error(f"Async load confidence scores failed: {e}")
            return []

    async def append_performance_record(self, record: PerformanceRecord) -> bool:
        """
        Add a performance record to the write buffer.

        The record will be flushed to disk periodically or when buffer is full.

        Args:
            record: Performance record to append

        Returns:
            True if added to buffer successfully
        """
        async with self._buffer_lock:
            self._write_buffer.append(record)
            self._memory_records.append(record)

            # Flush if buffer is full
            if len(self._write_buffer) >= self._max_buffer_size:
                await self._flush_buffer_internal()

        return True

    async def append_performance_records_batch(self, records: List[PerformanceRecord]) -> bool:
        """
        Add multiple performance records to the buffer.

        Args:
            records: List of performance records

        Returns:
            True if successful
        """
        if not records:
            return True

        async with self._buffer_lock:
            self._write_buffer.extend(records)
            self._memory_records.extend(records)

            # Flush if buffer exceeds threshold
            if len(self._write_buffer) >= self._max_buffer_size:
                await self._flush_buffer_internal()

        return True

    async def flush_buffer(self) -> int:
        """
        Flush all buffered records to disk.

        Returns:
            Number of records flushed
        """
        async with self._buffer_lock:
            return await self._flush_buffer_internal()

    async def _flush_buffer_internal(self) -> int:
        """Internal flush without lock (must be called with lock held)."""
        if not self._write_buffer:
            return 0

        count = len(self._write_buffer)

        try:
            # Build content to append
            lines = []
            for record in self._write_buffer:
                lines.append(json.dumps(record.to_dict(), ensure_ascii=False) + '\n')

            content = ''.join(lines)
            await self._append_file(self.performance_history_path, content)

            logger.debug(f"Flushed {count} records to disk")

        except Exception as e:
            logger.error(f"Failed to flush buffer: {e}")
            # Don't clear buffer on failure, will retry
            return 0

        # Clear buffer on success
        self._write_buffer.clear()
        return count

    async def _flush_loop(self) -> None:
        """Background loop for periodic buffer flushing."""
        while True:
            try:
                await asyncio.sleep(self._flush_interval)
                await self.flush_buffer()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Flush loop error: {e}")

    async def query_performance_history(
        self,
        model_name: Optional[str] = None,
        task_type: Optional[TaskType] = None,
        limit: int = 1000
    ) -> List[PerformanceRecord]:
        """
        Query performance history asynchronously.

        Args:
            model_name: Filter by model name
            task_type: Filter by task type
            limit: Maximum records to return

        Returns:
            List of matching records
        """
        def matches(record: PerformanceRecord) -> bool:
            if model_name and record.model_name != model_name:
                return False
            if task_type and record.task_type != task_type:
                return False
            return True

        if not os.path.exists(self.performance_history_path):
            return [r for r in self._memory_records if matches(r)][:limit]

        try:
            content = await self._read_file(self.performance_history_path)
            records = []

            for line in content.splitlines():
                if not line.strip():
                    continue

                try:
                    data = json.loads(line)
                    record = PerformanceRecord.from_dict(data)
                    if matches(record):
                        records.append(record)
                        if len(records) >= limit:
                            break
                except Exception as e:
                    logger.warning(f"Failed to parse record: {e}")
                    continue

            return records

        except Exception as e:
            logger.error(f"Query failed: {e}")
            return [r for r in self._memory_records if matches(r)][:limit]

    async def get_performance_summary(
        self,
        model_name: Optional[str] = None,
        task_type: Optional[TaskType] = None
    ) -> Dict[str, Any]:
        """
        Get aggregated performance summary asynchronously.

        Args:
            model_name: Filter by model name
            task_type: Filter by task type

        Returns:
            Aggregated metrics dictionary
        """
        records = await self.query_performance_history(
            model_name=model_name,
            task_type=task_type,
            limit=10000
        )

        if not records:
            return {
                "total_records": 0,
                "accuracy": 0.0,
                "avg_response_time": 0.0,
                "total_cost": 0.0,
                "avg_cost": 0.0
            }

        correct = sum(1 for r in records if r.was_correct)
        total_time = sum(r.response_time for r in records)
        total_cost = sum(r.cost for r in records)
        n = len(records)

        return {
            "total_records": n,
            "accuracy": correct / n,
            "avg_response_time": total_time / n,
            "total_cost": total_cost,
            "avg_cost": total_cost / n
        }

    def get_buffer_stats(self) -> Dict[str, Any]:
        """Get buffer statistics."""
        return {
            "buffer_size": len(self._write_buffer),
            "max_buffer_size": self._max_buffer_size,
            "flush_interval": self._flush_interval,
            "memory_records_count": len(self._memory_records),
            "memory_scores_count": len(self._memory_scores)
        }
