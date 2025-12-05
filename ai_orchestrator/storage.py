"""
Storage Manager for persisting learning data and performance history.
"""

import json
import os
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging

from .models import AIModel, TaskType, PerformanceRecord
from .config import OrchestratorConfig


logger = logging.getLogger(__name__)


class StorageManager:
    """Manages persistence of confidence scores and performance history."""
    
    def __init__(self, config: OrchestratorConfig):
        self.config = config
        self.confidence_scores_path = config.confidence_scores_path
        self.performance_history_path = config.performance_history_path
        
        # Ensure storage directory exists
        os.makedirs(config.storage_dir, exist_ok=True)
    
    def save_confidence_scores(
        self, 
        scores: Dict[Tuple[str, TaskType], float]
    ) -> bool:
        """
        Persist confidence scores to storage.
        
        Args:
            scores: Dictionary mapping (model_name, task_type) to confidence score
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert tuple keys to string keys for JSON serialization
            serializable_scores = {
                f"{model_name}_{task_type.value}": score
                for (model_name, task_type), score in scores.items()
            }
            
            data = {
                "version": "1.0",
                "last_updated": datetime.now().isoformat(),
                "scores": serializable_scores
            }
            
            with open(self.confidence_scores_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(scores)} confidence scores to {self.confidence_scores_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save confidence scores: {e}")
            return False
    
    def load_confidence_scores(self) -> Dict[Tuple[str, TaskType], float]:
        """
        Load confidence scores from storage.
        
        Returns:
            Dictionary mapping (model_name, task_type) to confidence score
        """
        if not os.path.exists(self.confidence_scores_path):
            logger.info("No existing confidence scores found, starting fresh")
            return {}
        
        try:
            with open(self.confidence_scores_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert string keys back to tuple keys
            scores = {}
            for key, score in data.get("scores", {}).items():
                parts = key.rsplit('_', 1)
                if len(parts) == 2:
                    model_name, task_type_str = parts
                    try:
                        task_type = TaskType(task_type_str)
                        scores[(model_name, task_type)] = score
                    except ValueError:
                        logger.warning(f"Invalid task type in stored scores: {task_type_str}")
            
            logger.info(f"Loaded {len(scores)} confidence scores from {self.confidence_scores_path}")
            return scores
            
        except Exception as e:
            logger.error(f"Failed to load confidence scores: {e}")
            return {}
    
    def append_performance_record(self, record: PerformanceRecord) -> bool:
        """
        Append a performance record to the history log (JSONL format).
        
        Args:
            record: Performance record to append
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(self.performance_history_path, 'a', encoding='utf-8') as f:
                json.dump(record.to_dict(), f, ensure_ascii=False)
                f.write('\n')
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to append performance record: {e}")
            return False
    
    def query_performance_history(
        self,
        model_name: Optional[str] = None,
        task_type: Optional[TaskType] = None,
        limit: int = 1000
    ) -> List[PerformanceRecord]:
        """
        Query performance history with optional filters.
        
        Args:
            model_name: Filter by model name (optional)
            task_type: Filter by task type (optional)
            limit: Maximum number of records to return
            
        Returns:
            List of performance records matching the filters
        """
        if not os.path.exists(self.performance_history_path):
            return []
        
        try:
            records = []
            with open(self.performance_history_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    try:
                        data = json.loads(line)
                        record = PerformanceRecord.from_dict(data)
                        
                        # Apply filters
                        if model_name and record.model_name != model_name:
                            continue
                        if task_type and record.task_type != task_type:
                            continue
                        
                        records.append(record)
                        
                        if len(records) >= limit:
                            break
                            
                    except Exception as e:
                        logger.warning(f"Failed to parse performance record: {e}")
                        continue
            
            logger.info(f"Queried {len(records)} performance records")
            return records
            
        except Exception as e:
            logger.error(f"Failed to query performance history: {e}")
            return []
    
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
            
            # Write back only kept records
            with open(self.performance_history_path, 'w', encoding='utf-8') as f:
                f.writelines(kept_records)
            
            logger.info(f"Cleaned up {removed_count} old performance records")
            return removed_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old records: {e}")
            return 0
