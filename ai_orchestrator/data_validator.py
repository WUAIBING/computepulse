"""
Data Validator - Implements validation rules and data quality checks.

This module provides validation functionality for GPU prices, token prices,
and grid load data. It integrates with the AI Orchestrator's feedback loop
for continuous learning and improvement.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime

from .models import TaskType, ValidationResult

logger = logging.getLogger(__name__)


class DataValidator:
    """
    Validates data quality for GPU prices, token prices, and grid load.

    Integrates with AI models for intelligent validation and anomaly detection.
    """

    def __init__(self):
        """Initialize the data validator."""
        logger.info("Data Validator initialized")

    def validate_gpu_prices(self, data: List[Dict[str, Any]]) -> ValidationResult:
        """
        Validate GPU price data.

        Checks:
        - Price range validity
        - Required fields
        - Data consistency
        - Market reasonableness

        Args:
            data: List of GPU price records

        Returns:
            ValidationResult with validation details
        """
        logger.info(f"Validating {len(data)} GPU price records")

        errors = []
        warnings = []
        validated_data = []

        # Required fields for GPU data
        required_fields = ['provider', 'gpu', 'price', 'region']

        for i, record in enumerate(data):
            record_errors = []
            record_warnings = []

            # Check required fields
            for field in required_fields:
                if field not in record or record[field] is None:
                    record_errors.append(f"Record {i}: Missing required field '{field}'")

            # Validate price
            if 'price' in record and record['price'] is not None:
                try:
                    price = float(record['price'])
                    if price < 0:
                        record_errors.append(f"Record {i}: Price cannot be negative ({price})")
                    elif price > 1000:  # Unrealistic price threshold
                        record_warnings.append(f"Record {i}: Price seems high (${price}/hour)")
                except (ValueError, TypeError):
                    record_errors.append(f"Record {i}: Invalid price format ({record['price']})")

            # Validate GPU field
            if 'gpu' in record and record['gpu']:
                gpu = str(record['gpu']).lower()
                # Check for obviously invalid GPU names
                if len(gpu) < 3:
                    record_warnings.append(f"Record {i}: GPU name seems too short")

            # Validate provider
            if 'provider' in record and record['provider']:
                provider = str(record['provider']).strip()
                if len(provider) < 2:
                    record_errors.append(f"Record {i}: Provider name too short")

            # Add validated record with metadata
            if not record_errors:
                validated_record = record.copy()
                validated_record['_validated'] = True
                validated_record['_validation_timestamp'] = datetime.now().isoformat()
                validated_data.append(validated_record)
            else:
                # Add record with error flag
                error_record = record.copy()
                error_record['_validation_errors'] = record_errors
                validated_data.append(error_record)

            errors.extend(record_errors)
            warnings.extend(record_warnings)

        # Determine overall validity
        is_valid = len(errors) == 0

        logger.info(
            f"GPU validation complete: valid={is_valid}, "
            f"records={len(data)}, errors={len(errors)}, warnings={len(warnings)}"
        )

        return ValidationResult(
            is_valid=is_valid,
            validated_data=validated_data,
            errors=errors,
            warnings=warnings,
            task_type=TaskType.DATA_VALIDATION
        )

    def validate_token_prices(self, data: List[Dict[str, Any]]) -> ValidationResult:
        """
        Validate token price data.

        Checks:
        - Input/output price ranges
        - Required fields (provider, model, input_price, output_price)
        - Price ratio reasonableness
        - Data consistency

        Args:
            data: List of token price records

        Returns:
            ValidationResult with validation details
        """
        logger.info(f"Validating {len(data)} token price records")

        errors = []
        warnings = []
        validated_data = []

        # Required fields for token data
        required_fields = ['provider', 'model', 'input_price', 'output_price']

        for i, record in enumerate(data):
            record_errors = []
            record_warnings = []

            # Check required fields
            for field in required_fields:
                if field not in record or record[field] is None:
                    record_errors.append(f"Record {i}: Missing required field '{field}'")

            # Validate input price
            if 'input_price' in record and record['input_price'] is not None:
                try:
                    input_price = float(record['input_price'])
                    if input_price < 0:
                        record_errors.append(f"Record {i}: Input price cannot be negative")
                    elif input_price > 100:  # Unlikely token price
                        record_warnings.append(f"Record {i}: Input price seems high")
                except (ValueError, TypeError):
                    record_errors.append(f"Record {i}: Invalid input price format")

            # Validate output price
            if 'output_price' in record and record['output_price'] is not None:
                try:
                    output_price = float(record['output_price'])
                    if output_price < 0:
                        record_errors.append(f"Record {i}: Output price cannot be negative")
                    elif output_price > 200:  # Unlikely token price
                        record_warnings.append(f"Record {i}: Output price seems high")
                except (ValueError, TypeError):
                    record_errors.append(f"Record {i}: Invalid output price format")

            # Check price ratio (output should be 2-4x input typically)
            if ('input_price' in record and 'output_price' in record and
                record['input_price'] is not None and record['output_price'] is not None):
                try:
                    input_price = float(record['input_price'])
                    output_price = float(record['output_price'])

                    if input_price > 0:
                        ratio = output_price / input_price
                        if ratio < 1.5:
                            record_warnings.append(
                                f"Record {i}: Output price is unusually low "
                                f"(ratio: {ratio:.2f}x input)"
                            )
                        elif ratio > 5:
                            record_warnings.append(
                                f"Record {i}: Output price is unusually high "
                                f"(ratio: {ratio:.2f}x input)"
                            )
                except (ValueError, TypeError):
                    pass  # Already caught in individual price validation

            # Validate model name
            if 'model' in record and record['model']:
                model = str(record['model']).strip()
                if len(model) < 3:
                    record_errors.append(f"Record {i}: Model name too short")

            # Validate provider
            if 'provider' in record and record['provider']:
                provider = str(record['provider']).strip()
                if len(provider) < 2:
                    record_errors.append(f"Record {i}: Provider name too short")

            # Add validated record with metadata
            if not record_errors:
                validated_record = record.copy()
                validated_record['_validated'] = True
                validated_record['_validation_timestamp'] = datetime.now().isoformat()
                validated_data.append(validated_record)
            else:
                # Add record with error flag
                error_record = record.copy()
                error_record['_validation_errors'] = record_errors
                validated_data.append(error_record)

            errors.extend(record_errors)
            warnings.extend(record_warnings)

        # Determine overall validity
        is_valid = len(errors) == 0

        logger.info(
            f"Token validation complete: valid={is_valid}, "
            f"records={len(data)}, errors={len(errors)}, warnings={len(warnings)}"
        )

        return ValidationResult(
            is_valid=is_valid,
            validated_data=validated_data,
            errors=errors,
            warnings=warnings,
            task_type=TaskType.DATA_VALIDATION
        )

    def validate_grid_load(self, data: List[Dict[str, Any]]) -> ValidationResult:
        """
        Validate grid load data.

        Checks:
        - Load value ranges (0-100%)
        - Required fields (region, timestamp, load_percentage)
        - Data consistency
        - Timestamp validity

        Args:
            data: List of grid load records

        Returns:
            ValidationResult with validation details
        """
        logger.info(f"Validating {len(data)} grid load records")

        errors = []
        warnings = []
        validated_data = []

        # Required fields for grid load data
        required_fields = ['region', 'timestamp', 'load_percentage']

        for i, record in enumerate(data):
            record_errors = []
            record_warnings = []

            # Check required fields
            for field in required_fields:
                if field not in record or record[field] is None:
                    record_errors.append(f"Record {i}: Missing required field '{field}'")

            # Validate load percentage
            if 'load_percentage' in record and record['load_percentage'] is not None:
                try:
                    load = float(record['load_percentage'])
                    if load < 0:
                        record_errors.append(f"Record {i}: Load percentage cannot be negative")
                    elif load > 100:
                        record_errors.append(f"Record {i}: Load percentage cannot exceed 100%")
                    elif load > 95:
                        record_warnings.append(f"Record {i}: Grid load is critically high ({load}%)")
                    elif load < 5:
                        record_warnings.append(f"Record {i}: Grid load is very low ({load}%)")
                except (ValueError, TypeError):
                    record_errors.append(f"Record {i}: Invalid load percentage format")

            # Validate timestamp
            if 'timestamp' in record and record['timestamp']:
                try:
                    # Try to parse timestamp
                    if isinstance(record['timestamp'], str):
                        datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00'))
                    elif isinstance(record['timestamp'], (int, float)):
                        # Unix timestamp
                        datetime.fromtimestamp(record['timestamp'])
                except (ValueError, TypeError, OSError):
                    record_errors.append(f"Record {i}: Invalid timestamp format")

            # Validate region
            if 'region' in record and record['region']:
                region = str(record['region']).strip()
                if len(region) < 2:
                    record_errors.append(f"Record {i}: Region name too short")

            # Add validated record with metadata
            if not record_errors:
                validated_record = record.copy()
                validated_record['_validated'] = True
                validated_record['_validation_timestamp'] = datetime.now().isoformat()
                validated_data.append(validated_record)
            else:
                # Add record with error flag
                error_record = record.copy()
                error_record['_validation_errors'] = record_errors
                validated_data.append(error_record)

            errors.extend(record_errors)
            warnings.extend(record_warnings)

        # Determine overall validity
        is_valid = len(errors) == 0

        logger.info(
            f"Grid load validation complete: valid={is_valid}, "
            f"records={len(data)}, errors={len(errors)}, warnings={len(warnings)}"
        )

        return ValidationResult(
            is_valid=is_valid,
            validated_data=validated_data,
            errors=errors,
            warnings=warnings,
            task_type=TaskType.DATA_VALIDATION
        )

    def cross_validate_sources(
        self,
        source1_data: List[Dict[str, Any]],
        source2_data: List[Dict[str, Any]],
        source1_name: str,
        source2_name: str,
        data_type: str
    ) -> Dict[str, Any]:
        """
        Cross-validate data from two different sources.

        Args:
            source1_data: First data source
            source2_data: Second data source
            source1_name: Name of first source
            source2_name: Name of second source
            data_type: Type of data ('gpu', 'token', 'grid_load')

        Returns:
            Dictionary with cross-validation results
        """
        logger.info(
            f"Cross-validating {data_type} data from {source1_name} and {source2_name}"
        )

        conflicts = []
        source1_items = {}
        source2_items = {}

        # Build lookup dictionaries based on data type
        if data_type == 'gpu':
            key_field = 'gpu'
            for item in source1_data:
                if key_field in item and 'provider' in item:
                    key = f"{item['provider']}_{item[key_field]}"
                    source1_items[key] = item

            for item in source2_data:
                if key_field in item and 'provider' in item:
                    key = f"{item['provider']}_{item[key_field]}"
                    source2_items[key] = item

        elif data_type == 'token':
            key_field = 'model'
            for item in source1_data:
                if key_field in item and 'provider' in item:
                    key = f"{item['provider']}_{item[key_field]}"
                    source1_items[key] = item

            for item in source2_data:
                if key_field in item and 'provider' in item:
                    key = f"{item['provider']}_{item[key_field]}"
                    source2_items[key] = item

        else:  # grid_load
            key_field = 'region'
            for item in source1_data:
                if key_field in item:
                    key = item[key_field]
                    source1_items[key] = item

            for item in source2_data:
                if key_field in item:
                    key = item[key_field]
                    source2_items[key] = item

        # Find conflicts
        for key in set(source1_items.keys()) & set(source2_items.keys()):
            item1 = source1_items[key]
            item2 = source2_items[key]

            if data_type == 'gpu':
                price1 = item1.get('price')
                price2 = item2.get('price')
                if price1 and price2:
                    try:
                        diff = abs(float(price1) - float(price2))
                        avg = (float(price1) + float(price2)) / 2
                        if avg > 0:
                            diff_percent = (diff / avg) * 100
                            if diff_percent > 20:  # Significant difference
                                conflicts.append({
                                    'item': key,
                                    'source1_price': price1,
                                    'source2_price': price2,
                                    'difference_percent': diff_percent,
                                    'recommendation': self._recommend_source(
                                        item1, item2, source1_name, source2_name
                                    )
                                })
                    except (ValueError, TypeError):
                        pass

            elif data_type == 'token':
                input1 = item1.get('input_price')
                input2 = item2.get('input_price')
                output1 = item1.get('output_price')
                output2 = item2.get('output_price')

                if input1 and input2 and output1 and output2:
                    try:
                        input_diff = abs(float(input1) - float(input2))
                        output_diff = abs(float(output1) - float(output2))
                        avg_input = (float(input1) + float(input2)) / 2
                        avg_output = (float(output1) + float(output2)) / 2

                        if avg_input > 0 and avg_output > 0:
                            input_diff_percent = (input_diff / avg_input) * 100
                            output_diff_percent = (output_diff / avg_output) * 100

                            if input_diff_percent > 20 or output_diff_percent > 20:
                                conflicts.append({
                                    'item': key,
                                    'source1_input': input1,
                                    'source2_input': input2,
                                    'source1_output': output1,
                                    'source2_output': output2,
                                    'input_diff_percent': input_diff_percent,
                                    'output_diff_percent': output_diff_percent,
                                    'recommendation': self._recommend_source(
                                        item1, item2, source1_name, source2_name
                                    )
                                })
                    except (ValueError, TypeError):
                        pass

        # Calculate agreement rate
        common_items = len(set(source1_items.keys()) & set(source2_items.keys()))
        total_items = len(source1_items) + len(source2_items)
        if total_items > 0:
            agreement_rate = (common_items / total_items) * 100
        else:
            agreement_rate = 100.0

        result = {
            'conflicts': conflicts,
            'agreement_rate': agreement_rate,
            'common_items': common_items,
            'source1_items': len(source1_items),
            'source2_items': len(source2_items),
            'data_type': data_type
        }

        logger.info(
            f"Cross-validation complete: agreement={agreement_rate:.1f}%, "
            f"conflicts={len(conflicts)}"
        )

        return result

    def _recommend_source(
        self,
        item1: Dict[str, Any],
        item2: Dict[str, Any],
        source1_name: str,
        source2_name: str
    ) -> str:
        """
        Recommend which data source to trust.

        Args:
            item1: Item from first source
            item2: Item from second source
            source1_name: Name of first source
            source2_name: Name of second source

        Returns:
            Recommendation string
        """
        # Simple heuristic: prefer the source with more recent timestamp
        # or more complete data

        score1 = 0
        score2 = 0

        # Check data completeness
        if item1.get('timestamp'):
            score1 += 1
        if item2.get('timestamp'):
            score2 += 1

        # Check for validation status
        if item1.get('_validated'):
            score1 += 1
        if item2.get('_validated'):
            score2 += 1

        if score1 > score2:
            return source1_name
        elif score2 > score1:
            return source2_name
        else:
            return f"Either {source1_name} or {source2_name}"

    def get_validation_summary(self, result: ValidationResult) -> Dict[str, Any]:
        """
        Get a summary of validation results.

        Args:
            result: ValidationResult object

        Returns:
            Summary dictionary
        """
        total_records = len(result.validated_data)
        error_records = sum(
            1 for record in result.validated_data
            if '_validation_errors' in record
        )
        valid_records = total_records - error_records

        return {
            'task_type': result.task_type.value if result.task_type else None,
            'is_valid': result.is_valid,
            'total_records': total_records,
            'valid_records': valid_records,
            'error_records': error_records,
            'warning_count': len(result.warnings),
            'error_count': len(result.errors),
            'validation_rate': (valid_records / total_records * 100) if total_records > 0 else 0,
            'timestamp': datetime.now().isoformat()
        }
