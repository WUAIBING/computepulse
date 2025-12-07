"""
Storage Manager for persisting learning data and performance history.

This module handles all persistence operations for the AI Orchestrator,
including confidence scores (JSON) and performance history (JSONL).
"""

import json
import os
import shutil
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import logging
import threading

from .models import AIModel, TaskType, PerformanceRecord, ConfidenceScore
from .config import OrchestratorConfig


logger = logging.getLogger(__name__)


class StorageError(Exception):
    """Raised when a storage operation fails."""
    pass


class StorageManager:
    """Manages persistence of confidence scores and performance history."""
    
    def __init__(self, config: OrchestratorConfig):
        self.config = config
        self.confidence_scores_path = config.confidence_scores_path
        self.performance_history_path = config.performance_history_path
        
        # Thread lock for concurrent access
        self._lock = threading.Lock()
        
        # In-memory fallback when storage fails
        self._use_memory_fallback = False
        self._memory_scores: Dict[Tuple[str, TaskType], float] = {}
        self._memory_records: List[PerformanceRecord] = []
        
        # Ensure storage directory exists
        os.makedirs(config.storage_dir, exist_ok=True)
        
        # Initialize files if they don't exist
        self._initialize_storage_files()
    
    def _initialize_storage_files(self) -> None:
        """Initialize storage files if they don't exist."""
        # Initialize confidence scores file
        if not os.path.exists(self.confidence_scores_path):
            try:
                self._write_json_atomic(self.confidence_scores_path, {
                    "version": "1.0",
                    "last_updated": datetime.now().isoformat(),
                    "scores": {}
                })
                logger.info(f"Initialized confidence scores file: {self.confidence_scores_path}")
            except Exception as e:
                logger.warning(f"Could not initialize confidence scores file: {e}")
        
        # Initialize performance history file
        if not os.path.exists(self.performance_history_path):
            try:
                with open(self.performance_history_path, 'w', encoding='utf-8') as f:
                    pass  # Create empty file
                logger.info(f"Initialized performance history file: {self.performance_history_path}")
            except Exception as e:
                logger.warning(f"Could not initialize performance history file: {e}")
    
    def _write_json_atomic(self, path: str, data: Any) -> None:
        """Write JSON data atomically using a temporary file."""
        temp_path = f"{path}.tmp"
        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            # Atomic rename
            shutil.move(temp_path, path)
        except Exception as e:
            # Clean up temp file if it exists
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
            raise e
    
    def save_confidence_scores(
        self, 
        scores: List[ConfidenceScore]
    ) -> bool:
        """
        Persist confidence scores to storage.
        
        Args:
            scores: List of ConfidenceScore objects
            
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            try:
                # Update in-memory cache (convert to dict format)
                self._memory_scores = {
                    (s.model_name, s.task_type): s.score for s in scores
                }
                
                if self._use_memory_fallback:
                    logger.warning("Using memory fallback, scores not persisted to disk")
                    return True
                
                # Convert to serializable format with full metadata
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
                
                self._write_json_atomic(self.confidence_scores_path, data)
                
                logger.info(f"Saved {len(scores)} confidence scores to {self.confidence_scores_path}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to save confidence scores: {e}")
                self._use_memory_fallback = True
                return False
    
    def load_confidence_scores(self) -> List[ConfidenceScore]:
        """
        Load confidence scores from storage.
        
        Returns:
            List of ConfidenceScore objects
        """
        with self._lock:
            # Return memory cache if using fallback
            if self._use_memory_fallback and self._memory_scores:
                logger.info("Returning confidence scores from memory fallback")
                return [
                    ConfidenceScore(model_name=k[0], task_type=k[1], score=v)
                    for k, v in self._memory_scores.items()
                ]
            
            if not os.path.exists(self.confidence_scores_path):
                logger.info("No existing confidence scores found, starting fresh")
                return []
            
            try:
                with open(self.confidence_scores_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                scores = []
                version = data.get("version", "1.0")
                
                for key, value in data.get("scores", {}).items():
                    # Try to find a valid TaskType suffix
                    parsed = False
                    for task_type in TaskType:
                        suffix = f"_{task_type.value}"
                        if key.endswith(suffix):
                            model_name = key[:-len(suffix)]
                            
                            # Handle both old (float) and new (dict) formats
                            if isinstance(value, dict):
                                score = ConfidenceScore(
                                    model_name=model_name,
                                    task_type=task_type,
                                    score=value["score"],
                                    sample_count=value.get("sample_count", 0),
                                    last_updated=datetime.fromisoformat(value["last_updated"]) if "last_updated" in value else datetime.now(),
                                )
                            else:
                                # Old format: just a float
                                score = ConfidenceScore(
                                    model_name=model_name,
                                    task_type=task_type,
                                    score=float(value),
                                )
                            
                            scores.append(score)
                            parsed = True
                            break
                    
                    if not parsed:
                        logger.warning(f"Could not parse key in stored scores: {key}")
                
                # Update memory cache
                self._memory_scores = {
                    (s.model_name, s.task_type): s.score for s in scores
                }
                
                logger.info(f"Loaded {len(scores)} confidence scores from {self.confidence_scores_path}")
                return scores
                
            except json.JSONDecodeError as e:
                logger.error(f"Corrupted confidence scores file: {e}")
                # Try to recover from backup
                return self._recover_confidence_scores()
            except Exception as e:
                logger.error(f"Failed to load confidence scores: {e}")
                self._use_memory_fallback = True
                return [
                    ConfidenceScore(model_name=k[0], task_type=k[1], score=v)
                    for k, v in self._memory_scores.items()
                ]
    
    def _recover_confidence_scores(self) -> List[ConfidenceScore]:
        """Attempt to recover confidence scores from backup or return defaults."""
        backup_path = f"{self.confidence_scores_path}.bak"
        if os.path.exists(backup_path):
            try:
                with open(backup_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.info("Recovered confidence scores from backup")
                # Restore from backup
                shutil.copy(backup_path, self.confidence_scores_path)
                return self.load_confidence_scores()
            except Exception as e:
                logger.error(f"Failed to recover from backup: {e}")
        
        logger.warning("No backup available, returning empty scores")
        return []
    
    def append_performance_record(self, record: PerformanceRecord) -> bool:
        """
        Append a performance record to the history log (JSONL format).
        
        Args:
            record: Performance record to append
            
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            try:
                # Always add to memory cache
                self._memory_records.append(record)
                
                if self._use_memory_fallback:
                    logger.warning("Using memory fallback, record not persisted to disk")
                    return True
                
                with open(self.performance_history_path, 'a', encoding='utf-8') as f:
                    json.dump(record.to_dict(), f, ensure_ascii=False)
                    f.write('\n')
                
                return True
                
            except Exception as e:
                logger.error(f"Failed to append performance record: {e}")
                self._use_memory_fallback = True
                return False
    
    def append_performance_records_batch(self, records: List[PerformanceRecord]) -> bool:
        """
        Append multiple performance records in a single operation.
        
        Args:
            records: List of performance records to append
            
        Returns:
            True if successful, False otherwise
        """
        if not records:
            return True
        
        with self._lock:
            try:
                # Add to memory cache
                self._memory_records.extend(records)
                
                if self._use_memory_fallback:
                    logger.warning("Using memory fallback, records not persisted to disk")
                    return True
                
                with open(self.performance_history_path, 'a', encoding='utf-8') as f:
                    for record in records:
                        json.dump(record.to_dict(), f, ensure_ascii=False)
                        f.write('\n')
                
                logger.info(f"Appended {len(records)} performance records")
                return True
                
            except Exception as e:
                logger.error(f"Failed to append performance records batch: {e}")
                self._use_memory_fallback = True
                return False
    
    def query_performance_history(
        self,
        model_name: Optional[str] = None,
        task_type: Optional[TaskType] = None,
        limit: int = 1000,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[PerformanceRecord]:
        """
        Query performance history with optional filters.
        
        Args:
            model_name: Filter by model name (optional)
            task_type: Filter by task type (optional)
            limit: Maximum number of records to return
            start_time: Filter records after this time (optional)
            end_time: Filter records before this time (optional)
            
        Returns:
            List of performance records matching the filters
        """
        def matches_filters(record: PerformanceRecord) -> bool:
            """Check if a record matches all filters."""
            if model_name and record.model_name != model_name:
                return False
            if task_type and record.task_type != task_type:
                return False
            if start_time and record.timestamp < start_time:
                return False
            if end_time and record.timestamp > end_time:
                return False
            return True
        
        with self._lock:
            # If using memory fallback, query from memory
            if self._use_memory_fallback or not os.path.exists(self.performance_history_path):
                records = [r for r in self._memory_records if matches_filters(r)]
                return records[:limit]
            
            try:
                records = []
                with open(self.performance_history_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if not line.strip():
                            continue
                        
                        try:
                            data = json.loads(line)
                            record = PerformanceRecord.from_dict(data)
                            
                            if matches_filters(record):
                                records.append(record)
                            
                            if len(records) >= limit:
                                break
                                
                        except Exception as e:
                            logger.warning(f"Failed to parse performance record: {e}")
                            continue
                
                logger.debug(f"Queried {len(records)} performance records")
                return records
                
            except Exception as e:
                logger.error(f"Failed to query performance history: {e}")
                self._use_memory_fallback = True
                return [r for r in self._memory_records if matches_filters(r)][:limit]
    
    def get_performance_summary(
        self,
        model_name: Optional[str] = None,
        task_type: Optional[TaskType] = None
    ) -> Dict:
        """
        Get aggregated performance summary.
        
        Args:
            model_name: Filter by model name (optional)
            task_type: Filter by task type (optional)
            
        Returns:
            Dictionary with aggregated metrics
        """
        records = self.query_performance_history(
            model_name=model_name,
            task_type=task_type,
            limit=10000
        )
        
        if not records:
            return {
                "total_records": 0,
                "accuracy": 0.0,
                "avg_response_time": 0.0,
                "total_cost": 0.0
            }
        
        correct_count = sum(1 for r in records if r.was_correct)
        total_response_time = sum(r.response_time for r in records)
        total_cost = sum(r.cost for r in records)
        
        return {
            "total_records": len(records),
            "accuracy": correct_count / len(records) if records else 0.0,
            "avg_response_time": total_response_time / len(records) if records else 0.0,
            "total_cost": total_cost,
            "avg_cost": total_cost / len(records) if records else 0.0
        }
    
    def cleanup_old_records(self, days_to_keep: int = 90) -> int:
        """
        Remove performance records older than specified days.
        
        Args:
            days_to_keep: Number of days of history to retain
            
        Returns:
            Number of records removed
        """
        with self._lock:
            if not os.path.exists(self.performance_history_path):
                return 0
            
            try:
                cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 3600)
                kept_records = []
                removed_count = 0
                
                with open(self.performance_history_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if not line.strip():
                            continue
                        
                        try:
                            data = json.loads(line)
                            record_time = datetime.fromisoformat(data["timestamp"]).timestamp()
                            
                            if record_time >= cutoff_date:
                                kept_records.append(line)
                            else:
                                removed_count += 1
                                
                        except Exception as e:
                            logger.warning(f"Failed to parse record during cleanup: {e}")
                            # Keep the record if we can't parse it
                            kept_records.append(line)
                
                # Write back only kept records atomically
                temp_path = f"{self.performance_history_path}.tmp"
                with open(temp_path, 'w', encoding='utf-8') as f:
                    f.writelines(kept_records)
                shutil.move(temp_path, self.performance_history_path)
                
                # Also clean up memory cache
                cutoff_datetime = datetime.fromtimestamp(cutoff_date)
                self._memory_records = [r for r in self._memory_records if r.timestamp >= cutoff_datetime]
                
                logger.info(f"Cleaned up {removed_count} old performance records")
                return removed_count
                
            except Exception as e:
                logger.error(f"Failed to cleanup old records: {e}")
                return 0
    
    def create_backup(self) -> bool:
        """
        Create a backup of all storage files.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Backup confidence scores
            if os.path.exists(self.confidence_scores_path):
                shutil.copy(self.confidence_scores_path, f"{self.confidence_scores_path}.bak")
            
            # Backup performance history
            if os.path.exists(self.performance_history_path):
                shutil.copy(self.performance_history_path, f"{self.performance_history_path}.bak")
            
            logger.info("Created storage backups")
            return True
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return False
    
    def reset_memory_fallback(self) -> bool:
        """
        Attempt to reset memory fallback mode and sync to disk.
        
        Returns:
            True if successfully reset, False otherwise
        """
        if not self._use_memory_fallback:
            return True
        
        try:
            # Try to save memory data to disk
            if self._memory_scores:
                self._use_memory_fallback = False
                if not self.save_confidence_scores(self._memory_scores):
                    self._use_memory_fallback = True
                    return False
            
            if self._memory_records:
                self._use_memory_fallback = False
                if not self.append_performance_records_batch(self._memory_records):
                    self._use_memory_fallback = True
                    return False
            
            self._use_memory_fallback = False
            logger.info("Successfully reset memory fallback mode")
            return True
        except Exception as e:
            logger.error(f"Failed to reset memory fallback: {e}")
            return False
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get statistics about storage usage.
        
        Returns:
            Dictionary with storage statistics
        """
        stats = {
            "using_memory_fallback": self._use_memory_fallback,
            "memory_scores_count": len(self._memory_scores),
            "memory_records_count": len(self._memory_records),
            "confidence_scores_file_exists": os.path.exists(self.confidence_scores_path),
            "performance_history_file_exists": os.path.exists(self.performance_history_path),
        }
        
        try:
            if os.path.exists(self.confidence_scores_path):
                stats["confidence_scores_file_size"] = os.path.getsize(self.confidence_scores_path)
            if os.path.exists(self.performance_history_path):
                stats["performance_history_file_size"] = os.path.getsize(self.performance_history_path)
        except Exception as e:
            logger.warning(f"Failed to get file sizes: {e}")
        
        return stats
