"""
Migration Adapter - Provides backward compatibility with existing ComputePulse API.

This module allows gradual migration from the old system to the new AI Orchestrator
while maintaining full backward compatibility. Supports feature flags for gradual rollout.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional, Callable

from .config import OrchestratorConfig
from .orchestrator import AIOrchestrator
from .models import AIModel, TaskType

logger = logging.getLogger(__name__)


class MigrationAdapter:
    """
    Adapter for gradual migration from old ComputePulse API to new AI Orchestrator.

    Features:
    - Backward compatibility with existing API
    - Feature flags for gradual migration
    - Seamless fallback to old system if needed
    - Configuration-driven behavior
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the migration adapter.

        Args:
            config_path: Path to configuration file (optional)
        """
        self.config_path = config_path or os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'config.json'
        )

        self.config = self._load_config()
        self.orchestrator = None
        self.use_orchestrator = self.config.get('use_orchestrator', True)

        # Legacy system (will be initialized if needed)
        self.legacy_system = None

        # Feature flags
        self.feature_flags = self.config.get('feature_flags', {})

        logger.info(
            f"Migration Adapter initialized: "
            f"use_orchestrator={self.use_orchestrator}, "
            f"config_path={self.config_path}"
        )

    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file or use defaults.

        Returns:
            Configuration dictionary
        """
        default_config = {
            'use_orchestrator': True,
            'feature_flags': {
                'enable_validation': True,
                'enable_performance_tracking': True,
                'enable_feedback_loop': True,
                'enable_model_selection': True,
                'enable_parallel_execution': True,
                'enable_result_merging': True
            },
            'orchestrator': {
                'default_quality_threshold': 0.8,
                'default_cost_limit': 1.0,
                'model_timeout_seconds': 30.0,
                'simple_query_model_count': 1,
                'complex_reasoning_model_count': 2,
                'validation_model_count': 3
            },
            'models': [
                {
                    'name': 'qwen-max',
                    'provider': 'Alibaba',
                    'cost_per_1m_tokens': 0.4,
                    'avg_response_time': 2.0,
                    'enabled': True
                },
                {
                    'name': 'deepseek-v3',
                    'provider': 'DeepSeek',
                    'cost_per_1m_tokens': 0.15,
                    'avg_response_time': 1.8,
                    'enabled': True
                }
            ],
            'legacy_system': {
                'enabled': False,
                'api_endpoint': 'http://localhost:8000',
                'api_key': None
            }
        }

        if not os.path.exists(self.config_path):
            logger.info(f"Config file not found at {self.config_path}, using defaults")
            self._save_config(default_config)
            return default_config

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # Merge with defaults for any missing keys
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value

            logger.info(f"Loaded configuration from {self.config_path}")
            return config

        except Exception as e:
            logger.error(f"Failed to load config: {e}, using defaults")
            return default_config

    def _save_config(self, config: Dict[str, Any]) -> None:
        """
        Save configuration to file.

        Args:
            config: Configuration dictionary to save
        """
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved configuration to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def initialize_orchestrator(self) -> Optional[AIOrchestrator]:
        """
        Initialize the AI Orchestrator with configured models.

        Returns:
            Initialized AIOrchestrator instance or None if failed
        """
        if not self.use_orchestrator:
            logger.info("Orchestrator disabled in configuration")
            return None

        try:
            # Create orchestrator with custom config
            orchestrator_config = OrchestratorConfig()

            # Override default values with config
            orchestrator_cfg = self.config.get('orchestrator', {})
            for key, value in orchestrator_cfg.items():
                if hasattr(orchestrator_config, key):
                    setattr(orchestrator_config, key, value)

            self.orchestrator = AIOrchestrator(orchestrator_config)

            # Register models from config
            for model_config in self.config.get('models', []):
                if model_config.get('enabled', True):
                    model = AIModel(
                        name=model_config['name'],
                        provider=model_config['provider'],
                        cost_per_1m_tokens=model_config['cost_per_1m_tokens'],
                        avg_response_time=model_config['avg_response_time']
                    )
                    self.orchestrator.register_model(model)
                    logger.info(f"Registered model: {model_config['name']}")

            logger.info("AI Orchestrator initialized successfully")
            return self.orchestrator

        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {e}")
            self.orchestrator = None
            return None

    def is_feature_enabled(self, feature_name: str) -> bool:
        """
        Check if a feature flag is enabled.

        Args:
            feature_name: Name of the feature flag

        Returns:
            True if enabled, False otherwise
        """
        return self.feature_flags.get(feature_name, True)

    async def fetch_data_with_collaboration(
        self,
        prompt: str,
        data_type: str,
        quality_threshold: float = 0.8,
        cost_limit: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fetch data using AI collaboration (new or legacy system).

        This method provides backward compatibility with the old
        fetch_data_with_collaboration function.

        Args:
            prompt: Prompt for data fetching
            data_type: Type of data to fetch ('gpu', 'token', 'grid_load')
            quality_threshold: Minimum quality threshold
            cost_limit: Maximum cost limit
            **kwargs: Additional arguments

        Returns:
            Dictionary with fetched data and metadata
        """
        logger.info(
            f"fetch_data_with_collaboration called: "
            f"data_type={data_type}, quality={quality_threshold}, cost={cost_limit}"
        )

        # Determine which system to use
        if self.use_orchestrator and self.orchestrator:
            return await self._fetch_with_orchestrator(
                prompt=prompt,
                data_type=data_type,
                quality_threshold=quality_threshold,
                cost_limit=cost_limit,
                **kwargs
            )
        elif self._is_legacy_enabled():
            return await self._fetch_with_legacy(
                prompt=prompt,
                data_type=data_type,
                **kwargs
            )
        else:
            raise RuntimeError("No data fetching system available")

    async def _fetch_with_orchestrator(
        self,
        prompt: str,
        data_type: str,
        quality_threshold: float,
        cost_limit: Optional[float],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fetch data using the new AI Orchestrator.

        Args:
            prompt: Prompt for data fetching
            data_type: Type of data to fetch
            quality_threshold: Minimum quality threshold
            cost_limit: Maximum cost limit
            **kwargs: Additional arguments

        Returns:
            Dictionary with fetched data and metadata
        """
        if not self.orchestrator:
            raise RuntimeError("Orchestrator not initialized")

        try:
            # Process request through orchestrator
            result = await self.orchestrator.process_request(
                prompt=prompt,
                quality_threshold=quality_threshold,
                cost_limit=cost_limit,
                model_call_func=kwargs.get('model_call_func')
            )

            # Parse result data
            if isinstance(result.data, str):
                try:
                    data = json.loads(result.data)
                except json.JSONDecodeError:
                    data = result.data
            else:
                data = result.data

            return {
                'success': True,
                'data': data,
                'metadata': {
                    'contributing_models': result.contributing_models,
                    'confidence_scores': result.confidence_scores,
                    'task_type': result.metadata.get('task_type'),
                    'request_id': result.metadata.get('request_id'),
                    'stage': result.metadata.get('stage'),
                    'flagged_for_review': result.flagged_for_review
                },
                'system': 'orchestrator',
                'timestamp': kwargs.get('timestamp')
            }

        except Exception as e:
            logger.error(f"Orchestrator fetch failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'system': 'orchestrator'
            }

    async def _fetch_with_legacy(
        self,
        prompt: str,
        data_type: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fetch data using the legacy system.

        Args:
            prompt: Prompt for data fetching
            data_type: Type of data to fetch
            **kwargs: Additional arguments

        Returns:
            Dictionary with fetched data and metadata
        """
        logger.warning("Using legacy system for data fetching")

        # TODO: Implement legacy system integration
        # For now, return a placeholder response
        return {
            'success': True,
            'data': [],
            'metadata': {
                'system': 'legacy',
                'message': 'Legacy system not yet implemented'
            },
            'timestamp': kwargs.get('timestamp')
        }

    def _is_legacy_enabled(self) -> bool:
        """Check if legacy system is enabled."""
        return self.config.get('legacy_system', {}).get('enabled', False)

    def update_config(self, updates: Dict[str, Any]) -> None:
        """
        Update configuration dynamically.

        Args:
            updates: Dictionary of configuration updates
        """
        self.config.update(updates)
        self._save_config(self.config)

        # Update feature flags if present
        if 'feature_flags' in updates:
            self.feature_flags = updates['feature_flags']

        logger.info(f"Configuration updated: {list(updates.keys())}")

    def get_config(self) -> Dict[str, Any]:
        """
        Get current configuration.

        Returns:
            Current configuration dictionary
        """
        return self.config

    def toggle_orchestrator(self, enabled: bool) -> None:
        """
        Toggle orchestrator usage on/off.

        Args:
            enabled: Whether to enable orchestrator
        """
        self.use_orchestrator = enabled
        self.config['use_orchestrator'] = enabled
        self._save_config(self.config)

        status = "enabled" if enabled else "disabled"
        logger.info(f"Orchestrator {status}")

    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of the migration adapter.

        Returns:
            Status dictionary
        """
        return {
            'orchestrator_enabled': self.use_orchestrator,
            'orchestrator_initialized': self.orchestrator is not None,
            'legacy_enabled': self._is_legacy_enabled(),
            'feature_flags': self.feature_flags,
            'registered_models': (
                list(self.orchestrator.models.keys())
                if self.orchestrator else []
            ),
            'config_path': self.config_path
        }


# Convenience function for backward compatibility
async def fetch_data_with_collaboration(
    prompt: str,
    data_type: str = 'gpu',
    quality_threshold: float = 0.8,
    cost_limit: Optional[float] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Backward compatible wrapper for fetch_data_with_collaboration.

    This function maintains compatibility with existing code while
    using the new AI Orchestrator under the hood.

    Args:
        prompt: Prompt for data fetching
        data_type: Type of data to fetch ('gpu', 'token', 'grid_load')
        quality_threshold: Minimum quality threshold
        cost_limit: Maximum cost limit
        **kwargs: Additional arguments

    Returns:
        Dictionary with fetched data and metadata
    """
    adapter = MigrationAdapter()
    adapter.initialize_orchestrator()

    return await adapter.fetch_data_with_collaboration(
        prompt=prompt,
        data_type=data_type,
        quality_threshold=quality_threshold,
        cost_limit=cost_limit,
        **kwargs
    )
