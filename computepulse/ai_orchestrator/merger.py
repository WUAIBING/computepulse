"""
Confidence Weighted Merger for the AI Orchestrator system.

This module implements merging of results from multiple AI models
using confidence-based weighting.
"""

import json
import logging
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .models import MergedResult, TaskType
from .adapters.base import AdapterResponse


logger = logging.getLogger(__name__)


@dataclass
class MergeMetadata:
    """Metadata about the merge operation."""
    total_models: int
    agreeing_models: int
    disagreement_resolved_by: Optional[str] = None
    low_confidence_flag: bool = False
    merge_method: str = "weighted_vote"


class ConfidenceWeightedMerger:
    """
    Merges results from multiple AI models using confidence-based weighting.
    
    Supports different merge strategies for different data types:
    - List data: Weighted voting on disagreements
    - Scalar data: Weighted average
    - Text data: Select highest confidence response
    """
    
    # Threshold below which all models are considered low confidence
    LOW_CONFIDENCE_THRESHOLD = 0.4
    
    def __init__(
        self,
        low_confidence_threshold: float = 0.4,
    ):
        """
        Initialize the merger.
        
        Args:
            low_confidence_threshold: Threshold for flagging low confidence
        """
        self.low_confidence_threshold = low_confidence_threshold
    
    def merge(
        self,
        responses: Dict[str, AdapterResponse],
        confidence_scores: Dict[str, float],
        task_type: TaskType,
    ) -> MergedResult:
        """
        Merge multiple AI responses using confidence weighting.
        
        Args:
            responses: Responses from each AI model
            confidence_scores: Confidence score for each model
            task_type: The task type being processed
            
        Returns:
            MergedResult with merged data and metadata
        """
        # Filter successful responses
        successful = {
            name: resp for name, resp in responses.items()
            if resp.success and resp.content
        }
        
        if not successful:
            return MergedResult(
                data=None,
                contributing_models=[],
                confidence_scores={},
                metadata={"error": "No successful responses to merge"},
                flagged_for_review=True,
            )
        
        # Check for low confidence
        all_low_confidence = all(
            confidence_scores.get(name, 0.5) < self.low_confidence_threshold
            for name in successful
        )
        
        # Try to parse as JSON first
        parsed_responses = self._try_parse_json(successful)
        
        if parsed_responses:
            # Merge structured data
            merged_data, metadata = self._merge_structured_data(
                parsed_responses, confidence_scores
            )
        else:
            # Merge text responses
            merged_data, metadata = self._merge_text_responses(
                successful, confidence_scores
            )
        
        return MergedResult(
            data=merged_data,
            contributing_models=list(successful.keys()),
            confidence_scores={
                name: confidence_scores.get(name, 0.5)
                for name in successful
            },
            metadata={
                "merge_method": metadata.merge_method,
                "agreeing_models": metadata.agreeing_models,
                "total_models": metadata.total_models,
                "task_type": task_type.value,
            },
            flagged_for_review=all_low_confidence or metadata.low_confidence_flag,
        )
    
    def _try_parse_json(
        self,
        responses: Dict[str, AdapterResponse],
    ) -> Optional[Dict[str, Any]]:
        """Try to parse responses as JSON."""
        parsed = {}
        
        for name, resp in responses.items():
            content = resp.content.strip()
            
            # Try to extract JSON from markdown code blocks
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', content)
            if json_match:
                content = json_match.group(1).strip()
            
            try:
                parsed[name] = json.loads(content)
            except json.JSONDecodeError:
                # Try to find JSON array or object in the content
                array_match = re.search(r'\[[\s\S]*\]', content)
                obj_match = re.search(r'\{[\s\S]*\}', content)
                
                if array_match:
                    try:
                        parsed[name] = json.loads(array_match.group())
                    except json.JSONDecodeError:
                        pass
                elif obj_match:
                    try:
                        parsed[name] = json.loads(obj_match.group())
                    except json.JSONDecodeError:
                        pass
        
        # Return parsed if at least half of responses were parsed
        if len(parsed) >= len(responses) / 2:
            return parsed
        return None
    
    def _merge_structured_data(
        self,
        parsed_responses: Dict[str, Any],
        confidence_scores: Dict[str, float],
    ) -> Tuple[Any, MergeMetadata]:
        """Merge structured (JSON) data."""
        # Check if all responses are lists
        all_lists = all(isinstance(v, list) for v in parsed_responses.values())
        
        if all_lists:
            return self._merge_list_data(parsed_responses, confidence_scores)
        
        # Check if all responses are dicts
        all_dicts = all(isinstance(v, dict) for v in parsed_responses.values())
        
        if all_dicts:
            return self._merge_dict_data(parsed_responses, confidence_scores)
        
        # Mixed types - use highest confidence
        return self._select_highest_confidence(parsed_responses, confidence_scores)
    
    def _merge_list_data(
        self,
        parsed_responses: Dict[str, List],
        confidence_scores: Dict[str, float],
    ) -> Tuple[List, MergeMetadata]:
        """Merge list data using weighted voting."""
        # If only one response, return it
        if len(parsed_responses) == 1:
            name = list(parsed_responses.keys())[0]
            return parsed_responses[name], MergeMetadata(
                total_models=1,
                agreeing_models=1,
                merge_method="single_response",
            )
        
        # Group items by a key (try to find common identifier)
        all_items = []
        for name, items in parsed_responses.items():
            confidence = confidence_scores.get(name, 0.5)
            for item in items:
                all_items.append((name, item, confidence))
        
        # If items have identifiable keys, group and vote
        # Otherwise, use union with deduplication
        merged = self._deduplicate_items(all_items, confidence_scores)
        
        agreeing = self._count_agreeing_models(parsed_responses)
        
        return merged, MergeMetadata(
            total_models=len(parsed_responses),
            agreeing_models=agreeing,
            merge_method="list_merge",
        )
    
    def _merge_dict_data(
        self,
        parsed_responses: Dict[str, Dict],
        confidence_scores: Dict[str, float],
    ) -> Tuple[Dict, MergeMetadata]:
        """Merge dictionary data."""
        # Collect all keys
        all_keys = set()
        for data in parsed_responses.values():
            all_keys.update(data.keys())
        
        merged = {}
        
        for key in all_keys:
            values = []
            for name, data in parsed_responses.items():
                if key in data:
                    values.append((name, data[key], confidence_scores.get(name, 0.5)))
            
            if values:
                # Use weighted voting for this key
                merged[key] = self._weighted_vote(values)
        
        agreeing = self._count_agreeing_models(parsed_responses)
        
        return merged, MergeMetadata(
            total_models=len(parsed_responses),
            agreeing_models=agreeing,
            merge_method="dict_merge",
        )
    
    def _merge_text_responses(
        self,
        responses: Dict[str, AdapterResponse],
        confidence_scores: Dict[str, float],
    ) -> Tuple[str, MergeMetadata]:
        """Merge text responses by selecting highest confidence."""
        if not responses:
            return "", MergeMetadata(
                total_models=0,
                agreeing_models=0,
                merge_method="no_responses",
            )
        
        # Select response with highest confidence
        best_name = max(
            responses.keys(),
            key=lambda x: confidence_scores.get(x, 0.5)
        )
        
        return responses[best_name].content, MergeMetadata(
            total_models=len(responses),
            agreeing_models=1,
            merge_method="highest_confidence",
            disagreement_resolved_by=best_name,
        )
    
    def _select_highest_confidence(
        self,
        parsed_responses: Dict[str, Any],
        confidence_scores: Dict[str, float],
    ) -> Tuple[Any, MergeMetadata]:
        """Select the response with highest confidence."""
        best_name = max(
            parsed_responses.keys(),
            key=lambda x: confidence_scores.get(x, 0.5)
        )
        
        return parsed_responses[best_name], MergeMetadata(
            total_models=len(parsed_responses),
            agreeing_models=1,
            merge_method="highest_confidence",
            disagreement_resolved_by=best_name,
        )
    
    def _weighted_vote(
        self,
        candidates: List[Tuple[str, Any, float]],
    ) -> Any:
        """
        Perform weighted voting on candidates.
        
        Args:
            candidates: List of (model_name, value, confidence) tuples
            
        Returns:
            The winning value
        """
        if not candidates:
            return None
        
        if len(candidates) == 1:
            return candidates[0][1]
        
        # Group by value (using string representation for comparison)
        value_groups: Dict[str, List[Tuple[str, Any, float]]] = defaultdict(list)
        
        for name, value, confidence in candidates:
            # Use JSON string for comparison
            try:
                key = json.dumps(value, sort_keys=True)
            except (TypeError, ValueError):
                key = str(value)
            value_groups[key].append((name, value, confidence))
        
        # Calculate weighted score for each value
        scores = {}
        for key, group in value_groups.items():
            scores[key] = sum(conf for _, _, conf in group)
        
        # Return value with highest weighted score
        best_key = max(scores, key=scores.get)
        return value_groups[best_key][0][1]
    
    def _deduplicate_items(
        self,
        all_items: List[Tuple[str, Any, float]],
        confidence_scores: Dict[str, float],
    ) -> List:
        """Deduplicate items from multiple sources."""
        seen = {}
        
        for name, item, confidence in all_items:
            try:
                key = json.dumps(item, sort_keys=True)
            except (TypeError, ValueError):
                key = str(item)
            
            if key not in seen or confidence > seen[key][1]:
                seen[key] = (item, confidence)
        
        return [item for item, _ in seen.values()]
    
    def _count_agreeing_models(
        self,
        parsed_responses: Dict[str, Any],
    ) -> int:
        """Count how many models agree on the same result."""
        if len(parsed_responses) <= 1:
            return len(parsed_responses)
        
        # Compare responses
        values = list(parsed_responses.values())
        first = values[0]
        
        agreeing = 1
        for other in values[1:]:
            try:
                if json.dumps(first, sort_keys=True) == json.dumps(other, sort_keys=True):
                    agreeing += 1
            except (TypeError, ValueError):
                if str(first) == str(other):
                    agreeing += 1
        
        return agreeing
