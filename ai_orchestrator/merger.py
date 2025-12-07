"""
Confidence Weighted Merger - Merges AI model results using confidence-based weighting.
"""

import logging
from typing import Any, Dict, List, Optional, Union

from .models import MergedResult, Response, TaskType

logger = logging.getLogger(__name__)


class ConfidenceWeightedMerger:
    """
    Merges results from multiple AI models using confidence-based weighting.

    Features:
    - Weighted voting for list data
    - Weighted average for scalar data
    - Metadata preservation
    - Low confidence flagging
    """

    def __init__(self):
        """Initialize the merger."""
        logger.info("Confidence Weighted Merger initialized")

    def merge(
        self,
        responses: Dict[str, Response],
        confidence_scores: Dict[str, float],
        task_type: Optional[TaskType] = None
    ) -> MergedResult:
        """
        Merge multiple model responses using confidence-based weighting.

        Args:
            responses: Dictionary mapping model names to responses
            confidence_scores: Dictionary mapping model names to confidence scores
            task_type: The task type (for task-specific merging logic)

        Returns:
            MergedResult with merged data

        Raises:
            ValueError: If no responses provided or merging fails
        """
        if not responses:
            raise ValueError("No responses provided for merging")

        logger.info(f"Merging {len(responses)} responses")

        try:
            # Filter out failed responses
            successful_responses = {
                name: resp for name, resp in responses.items()
                if resp.success and resp.content
            }

            if not successful_responses:
                logger.warning("No successful responses to merge")
                return MergedResult(
                    data=None,
                    contributing_models=list(responses.keys()),
                    confidence_scores=confidence_scores,
                    metadata={"error": "No successful responses"},
                    flagged_for_review=True
                )

            # Check if all responses agree
            all_content = [resp.content for resp in successful_responses.values()]
            if self._all_agree(all_content):
                logger.info("All models agree, using first response")
                merged_data = successful_responses[list(successful_responses.keys())[0]].content
            else:
                # Merge using task-specific logic
                merged_data = self._merge_content(
                    successful_responses,
                    confidence_scores,
                    task_type
                )

            # Calculate average confidence
            avg_confidence = sum(
                confidence_scores.get(name, 0.0)
                for name in successful_responses.keys()
            ) / len(successful_responses)

            # Flag for review if low confidence
            flagged = avg_confidence < 0.6 or len(successful_responses) < 2

            # Prepare metadata
            metadata = self._prepare_metadata(
                responses,
                successful_responses,
                avg_confidence,
                task_type
            )

            logger.info(f"Merged result confidence: {avg_confidence:.3f}, flagged: {flagged}")

            return MergedResult(
                data=merged_data,
                contributing_models=list(successful_responses.keys()),
                confidence_scores={
                    name: confidence_scores.get(name, 0.0)
                    for name in successful_responses.keys()
                },
                metadata=metadata,
                flagged_for_review=flagged
            )

        except Exception as e:
            logger.error(f"Error merging results: {e}")
            # Return best effort result
            best_response = max(
                responses.values(),
                key=lambda r: confidence_scores.get(r.model_name, 0.0) if r.success else 0.0
            )

            return MergedResult(
                data=best_response.content,
                contributing_models=[best_response.model_name],
                confidence_scores={
                    best_response.model_name: confidence_scores.get(best_response.model_name, 0.0)
                },
                metadata={"error": str(e), "fallback": True},
                flagged_for_review=True
            )

    def _all_agree(self, contents: List[str]) -> bool:
        """
        Check if all contents are identical.

        Args:
            contents: List of content strings

        Returns:
            True if all contents are the same
        """
        if not contents:
            return True

        first = contents[0]
        return all(content == first for content in contents[1:])

    def _merge_content(
        self,
        responses: Dict[str, Response],
        confidence_scores: Dict[str, float],
        task_type: Optional[TaskType] = None
    ) -> Any:
        """
        Merge content using confidence-based weighting.

        Args:
            responses: Successful responses
            confidence_scores: Confidence scores
            task_type: Task type for specialized merging

        Returns:
            Merged content
        """
        # Try to parse as structured data first
        parsed_contents = []
        for name, response in responses.items():
            try:
                parsed = self._parse_content(response.content)
                if parsed is not None:
                    parsed_contents.append((name, parsed, confidence_scores.get(name, 0.0)))
            except Exception as e:
                logger.debug(f"Could not parse content from {name}: {e}")

        # If we have structured data, use weighted merging
        if parsed_contents:
            if self._is_list_data(parsed_contents):
                return self._merge_list_data(parsed_contents)
            elif self._is_scalar_data(parsed_contents):
                return self._merge_scalar_data(parsed_contents)

        # Default: use weighted text merging
        return self._merge_text_responses(responses, confidence_scores)

    def _parse_content(self, content: str) -> Optional[Union[Dict, List, float, int]]:
        """
        Try to parse content as JSON.

        Args:
            content: Content string to parse

        Returns:
            Parsed content or None if parsing fails
        """
        import json

        try:
            # Try to parse as JSON
            return json.loads(content)
        except (json.JSONDecodeError, TypeError):
            # Try to parse as number
            try:
                if '.' in content:
                    return float(content.strip())
                else:
                    return int(content.strip())
            except (ValueError, TypeError):
                return None

    def _is_list_data(self, parsed_contents: List) -> bool:
        """
        Check if parsed content is list data.

        Args:
            parsed_contents: List of (name, parsed, confidence) tuples

        Returns:
            True if content appears to be list data
        """
        if not parsed_contents:
            return False

        # Check if all items are lists
        return all(
            isinstance(parsed, list)
            for _, parsed, _ in parsed_contents
        )

    def _is_scalar_data(self, parsed_contents: List) -> bool:
        """
        Check if parsed content is scalar data.

        Args:
            parsed_contents: List of (name, parsed, confidence) tuples

        Returns:
            True if content appears to be scalar data
        """
        if not parsed_contents:
            return False

        # Check if all items are numbers
        return all(
            isinstance(parsed, (int, float))
            for _, parsed, _ in parsed_contents
        )

    def _merge_list_data(self, parsed_contents: List) -> List[Dict]:
        """
        Merge list data using weighted voting.

        Args:
            parsed_contents: List of (name, parsed, confidence) tuples

        Returns:
            Merged list
        """
        # Group items by a key (e.g., provider, model, etc.)
        grouped = {}

        for name, items, confidence in parsed_contents:
            if not isinstance(items, list):
                continue

            for item in items:
                if isinstance(item, dict):
                    # Use first non-None value as key
                    key = None
                    for k in ['provider', 'model', 'id', 'name']:
                        if k in item and item[k] is not None:
                            key = item[k]
                            break

                    if key:
                        if key not in grouped:
                            grouped[key] = {'items': [], 'total_confidence': 0}

                        grouped[key]['items'].append(item)
                        grouped[key]['total_confidence'] += confidence
                else:
                    # Simple list item
                    key = str(item)
                    if key not in grouped:
                        grouped[key] = {'items': [], 'total_confidence': 0}

                    grouped[key]['items'].append(item)
                    grouped[key]['total_confidence'] += confidence

        # Select best items based on confidence
        sorted_items = sorted(
            grouped.items(),
            key=lambda x: x[1]['total_confidence'],
            reverse=True
        )

        # Merge items from top groups
        merged_items = []
        seen = set()

        for key, data in sorted_items:
            for item in data['items']:
                item_key = str(item)
                if item_key not in seen:
                    merged_items.append(item)
                    seen.add(item_key)

        return merged_items

    def _merge_scalar_data(self, parsed_contents: List) -> float:
        """
        Merge scalar data using weighted average.

        Args:
            parsed_contents: List of (name, parsed, confidence) tuples

        Returns:
            Weighted average
        """
        total_weighted = 0.0
        total_weight = 0.0

        for _, value, confidence in parsed_contents:
            try:
                numeric_value = float(value)
                total_weighted += numeric_value * confidence
                total_weight += confidence
            except (ValueError, TypeError):
                continue

        if total_weight == 0:
            return 0.0

        return total_weighted / total_weight

    def _merge_text_responses(
        self,
        responses: Dict[str, Response],
        confidence_scores: Dict[str, float]
    ) -> str:
        """
        Merge text responses using confidence-based selection.

        Args:
            responses: Response dictionary
            confidence_scores: Confidence scores

        Returns:
            Merged text
        """
        # Score each response by length and confidence
        scored_responses = []

        for name, response in responses.items():
            if not response.success or not response.content:
                continue

            confidence = confidence_scores.get(name, 0.0)
            length_score = min(len(response.content), 1000) / 1000.0  # Normalize length

            # Combined score: prioritize confidence, then length
            score = confidence * 0.8 + length_score * 0.2
            scored_responses.append((score, response.content))

        if not scored_responses:
            return ""

        # Sort by score and select best
        scored_responses.sort(reverse=True)
        return scored_responses[0][1]

    def _prepare_metadata(
        self,
        all_responses: Dict[str, Response],
        successful_responses: Dict[str, Response],
        avg_confidence: float,
        task_type: Optional[TaskType]
    ) -> Dict[str, Any]:
        """
        Prepare metadata for the merged result.

        Args:
            all_responses: All responses
            successful_responses: Successful responses
            avg_confidence: Average confidence score
            task_type: Task type

        Returns:
            Metadata dictionary
        """
        metadata = {
            "total_models": len(all_responses),
            "successful_models": len(successful_responses),
            "avg_confidence": avg_confidence,
            "agreement_score": self._calculate_agreement(all_responses)
        }

        if task_type:
            metadata["task_type"] = task_type.value

        # Add performance stats
        if successful_responses:
            response_times = [r.response_time for r in successful_responses.values()]
            costs = [r.cost for r in successful_responses.values()]

            metadata["avg_response_time"] = sum(response_times) / len(response_times)
            metadata["total_cost"] = sum(costs)

        # Add model details
        metadata["model_details"] = []
        for name, response in successful_responses.items():
            metadata["model_details"].append({
                "name": name,
                "response_time": response.response_time,
                "cost": response.cost,
                "success": response.success
            })

        return metadata

    def _calculate_agreement(self, responses: Dict[str, Response]) -> float:
        """
        Calculate agreement score between responses.

        Args:
            responses: Response dictionary

        Returns:
            Agreement score between 0 and 1
        """
        if not responses:
            return 0.0

        contents = [r.content for r in responses.values() if r.success and r.content]
        if len(contents) < 2:
            return 1.0

        # Simple agreement: proportion of content that matches
        agreements = 0
        total_pairs = 0

        for i in range(len(contents)):
            for j in range(i + 1, len(contents)):
                total_pairs += 1
                if self._similar(contents[i], contents[j]):
                    agreements += 1

        return agreements / total_pairs if total_pairs > 0 else 0.0

    def _similar(self, text1: str, text2: str) -> bool:
        """
        Simple similarity check between two texts.

        Args:
            text1: First text
            text2: Second text

        Returns:
            True if texts are similar
        """
        # Simple check: remove whitespace and compare
        t1 = ' '.join(text1.split())
        t2 = ' '.join(text2.split())

        if t1 == t2:
            return True

        # Check if one is a subset of the other
        if len(t1) > len(t2):
            t1, t2 = t2, t1

        return t2.startswith(t1) or t1 in t2
