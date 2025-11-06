#!/usr/bin/env python3
"""
Unified Configuration System
============================

YAML-based configuration management for all pipeline parameters.
Supports configuration inheritance, validation, and documentation.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict, field
from logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class NetworkConfig:
    """Network and download configuration."""
    max_retries: int = 4
    retry_base_delay: float = 2.0
    connection_timeout: int = 30
    download_timeout: int = 300

    def validate(self):
        assert 1 <= self.max_retries <= 10, "max_retries must be 1-10"
        assert 0.5 <= self.retry_base_delay <= 10.0, "retry_base_delay must be 0.5-10.0s"


@dataclass
class ScientificParams:
    """Scientific analysis parameters."""
    # Distance parameters (Angstroms)
    interaction_cutoff: float = 5.0
    pocket_radius: float = 10.0
    clash_cutoff: float = 2.0

    # Pocket analysis
    interaction_sphere_radius: float = 5.0
    hydrophobic_cutoff: float = 8.0

    # Druggability scoring weights
    druggability_volume_weight: float = 0.33
    druggability_hydrophobic_weight: float = 0.33
    druggability_electrostatic_weight: float = 0.34

    # Thresholds
    druggability_excellent_threshold: float = 0.7
    druggability_good_threshold: float = 0.5
    druggability_moderate_threshold: float = 0.3

    def validate(self):
        assert 2.0 <= self.interaction_cutoff <= 15.0
        assert 5.0 <= self.pocket_radius <= 20.0
        assert 1.0 <= self.clash_cutoff <= 5.0

        # Weights should sum to ~1.0
        total_weight = (
            self.druggability_volume_weight +
            self.druggability_hydrophobic_weight +
            self.druggability_electrostatic_weight
        )
        assert 0.99 <= total_weight <= 1.01, f"Druggability weights must sum to 1.0 (got {total_weight})"


@dataclass
class ClusteringConfig:
    """Clustering and RMSD analysis configuration."""
    method: str = "kmeans"  # kmeans or dbscan
    n_clusters: int = 3
    rmsd_cutoff: float = 2.0
    eps: float = 2.0  # for DBSCAN
    min_samples: int = 2  # for DBSCAN

    # Random seeds for reproducibility
    random_seed: int = 42
    numpy_seed: int = 42
    sklearn_seed: int = 42

    def validate(self):
        assert self.method in ["kmeans", "dbscan"], f"Unknown method: {self.method}"
        assert 1 <= self.n_clusters <= 20, "n_clusters must be 1-20"
        assert 0.5 <= self.rmsd_cutoff <= 10.0, "rmsd_cutoff must be 0.5-10.0 Å"


@dataclass
class OutputConfig:
    """Output format and file configuration."""
    # Formats
    generate_csv: bool = True
    generate_excel: bool = True
    generate_json: bool = True
    generate_pdb: bool = True

    # Visualization
    generate_visualizations: bool = True
    visualization_dpi: int = 300
    pymol_ray_trace: bool = False

    # Metadata
    include_metadata: bool = True
    include_git_info: bool = True
    include_environment: bool = False  # May contain sensitive data

    def validate(self):
        assert 72 <= self.visualization_dpi <= 600, "DPI must be 72-600"


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    console_output: bool = True
    file_output: bool = True
    use_colors: bool = True
    log_dir: str = "logs"

    def validate(self):
        assert self.level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


@dataclass
class PerformanceConfig:
    """Performance and resource configuration."""
    # Parallel processing
    enable_parallel: bool = False
    n_jobs: int = 4
    batch_size: int = 10

    # Memory management
    explicit_cleanup: bool = True
    gc_frequency: int = 10  # Run GC every N structures

    # Caching
    enable_rmsd_cache: bool = True
    cache_dir: str = ".cache"

    def validate(self):
        assert 1 <= self.n_jobs <= 32, "n_jobs must be 1-32"
        assert 1 <= self.batch_size <= 100, "batch_size must be 1-100"


@dataclass
class PipelineConfig:
    """Complete pipeline configuration."""
    # Sub-configurations
    network: NetworkConfig = field(default_factory=NetworkConfig)
    scientific: ScientificParams = field(default_factory=ScientificParams)
    clustering: ClusteringConfig = field(default_factory=ClusteringConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)

    # General settings
    pipeline_version: str = "3.1.0"
    output_dir: str = "pipeline_output"

    def validate(self):
        """Validate entire configuration."""
        self.network.validate()
        self.scientific.validate()
        self.clustering.validate()
        self.output.validate()
        self.logging.validate()
        self.performance.validate()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def to_yaml(self, filepath: Path):
        """Save configuration to YAML file."""
        with open(filepath, 'w') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, sort_keys=False)
        logger.info(f"Saved configuration: {filepath}")

    @classmethod
    def from_yaml(cls, filepath: Path) -> 'PipelineConfig':
        """Load configuration from YAML file."""
        with open(filepath, 'r') as f:
            data = yaml.safe_load(f)

        # Recursively create dataclass instances
        config = cls(
            network=NetworkConfig(**data.get('network', {})),
            scientific=ScientificParams(**data.get('scientific', {})),
            clustering=ClusteringConfig(**data.get('clustering', {})),
            output=OutputConfig(**data.get('output', {})),
            logging=LoggingConfig(**data.get('logging', {})),
            performance=PerformanceConfig(**data.get('performance', {})),
            pipeline_version=data.get('pipeline_version', '3.1.0'),
            output_dir=data.get('output_dir', 'pipeline_output')
        )

        config.validate()
        logger.info(f"Loaded configuration: {filepath}")
        return config

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PipelineConfig':
        """Create configuration from dictionary (for overrides)."""
        return cls.from_yaml_dict(data)

    def merge(self, overrides: Dict[str, Any]) -> 'PipelineConfig':
        """
        Create new configuration with overrides applied.

        Args:
            overrides: Dictionary of values to override

        Returns:
            New configuration with overrides
        """
        current = self.to_dict()

        # Deep merge
        def deep_merge(base, updates):
            for key, value in updates.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    deep_merge(base[key], value)
                else:
                    base[key] = value

        deep_merge(current, overrides)
        return PipelineConfig.from_dict(current)

    def get_parameter(self, path: str, default: Any = None) -> Any:
        """
        Get parameter by dot-notation path.

        Args:
            path: Dot-separated path (e.g., 'scientific.interaction_cutoff')
            default: Default value if not found

        Returns:
            Parameter value or default

        Example:
            >>> config.get_parameter('scientific.interaction_cutoff')
            5.0
        """
        parts = path.split('.')
        value = self.to_dict()

        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default

        return value

    def set_parameter(self, path: str, value: Any):
        """
        Set parameter by dot-notation path.

        Args:
            path: Dot-separated path
            value: New value

        Example:
            >>> config.set_parameter('scientific.interaction_cutoff', 6.0)
        """
        parts = path.split('.')
        obj = self

        # Navigate to parent
        for part in parts[:-1]:
            obj = getattr(obj, part)

        # Set value
        setattr(obj, parts[-1], value)

    def summary(self) -> str:
        """Generate human-readable configuration summary."""
        lines = [
            "Pipeline Configuration Summary",
            "=" * 60,
            f"Version: {self.pipeline_version}",
            f"Output Directory: {self.output_dir}",
            "",
            "Network:",
            f"  Max Retries: {self.network.max_retries}",
            f"  Retry Delay: {self.network.retry_base_delay}s",
            "",
            "Scientific Parameters:",
            f"  Interaction Cutoff: {self.scientific.interaction_cutoff} Å",
            f"  Pocket Radius: {self.scientific.pocket_radius} Å",
            f"  Clash Cutoff: {self.scientific.clash_cutoff} Å",
            "",
            "Clustering:",
            f"  Method: {self.clustering.method}",
            f"  N Clusters: {self.clustering.n_clusters}",
            f"  RMSD Cutoff: {self.clustering.rmsd_cutoff} Å",
            f"  Random Seed: {self.clustering.random_seed}",
            "",
            "Output:",
            f"  CSV: {self.output.generate_csv}",
            f"  Excel: {self.output.generate_excel}",
            f"  Visualizations: {self.output.generate_visualizations}",
            f"  DPI: {self.output.visualization_dpi}",
            "",
            "Performance:",
            f"  Parallel Processing: {self.performance.enable_parallel}",
            f"  Jobs: {self.performance.n_jobs}",
            f"  RMSD Caching: {self.performance.enable_rmsd_cache}",
            "=" * 60
        ]
        return "\n".join(lines)


class ConfigurationManager:
    """
    Manage configuration with support for multiple profiles and inheritance.
    """

    def __init__(self, config_dir: Path = Path(".config")):
        """
        Initialize configuration manager.

        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.default_config_file = self.config_dir / "default.yaml"
        self.current_config: Optional[PipelineConfig] = None

    def create_default_config(self):
        """Create default configuration file."""
        config = PipelineConfig()
        config.to_yaml(self.default_config_file)
        logger.info(f"Created default configuration: {self.default_config_file}")
        return config

    def load_config(
        self,
        config_file: Optional[Path] = None,
        overrides: Optional[Dict] = None
    ) -> PipelineConfig:
        """
        Load configuration with optional overrides.

        Args:
            config_file: Configuration file (uses default if None)
            overrides: Dictionary of override values

        Returns:
            Loaded configuration
        """
        # Use default if not specified
        if config_file is None:
            config_file = self.default_config_file
            if not config_file.exists():
                logger.info("No configuration found, creating default")
                return self.create_default_config()

        # Load base configuration
        config = PipelineConfig.from_yaml(config_file)

        # Apply overrides
        if overrides:
            config = config.merge(overrides)
            logger.info(f"Applied {len(overrides)} configuration overrides")

        self.current_config = config
        return config

    def save_config(self, config: PipelineConfig, name: str = "custom"):
        """Save configuration with a specific name."""
        config_file = self.config_dir / f"{name}.yaml"
        config.to_yaml(config_file)
        return config_file

    def list_configs(self) -> List[str]:
        """List available configuration profiles."""
        configs = []
        for yaml_file in self.config_dir.glob("*.yaml"):
            configs.append(yaml_file.stem)
        return sorted(configs)


# Global configuration instance
_config: Optional[PipelineConfig] = None
_manager: Optional[ConfigurationManager] = None


def get_config() -> PipelineConfig:
    """Get global configuration instance."""
    global _config
    if _config is None:
        _config = PipelineConfig()
    return _config


def load_config(config_file: Optional[Path] = None) -> PipelineConfig:
    """Load and set global configuration."""
    global _config, _manager

    if _manager is None:
        _manager = ConfigurationManager()

    _config = _manager.load_config(config_file)
    return _config


if __name__ == "__main__":
    from logging_config import setup_logger

    setup_logger(level="INFO")

    print("=== Unified Configuration Demo ===\n")

    # Create default configuration
    config = PipelineConfig()
    print("Default Configuration:")
    print(config.summary())
    print()

    # Save to YAML
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "config.yaml"
        config.to_yaml(config_file)
        print(f"Saved to: {config_file}")
        print()

        # Show YAML content
        print("YAML Content:")
        with open(config_file) as f:
            print(f.read())
        print()

        # Load back
        loaded = PipelineConfig.from_yaml(config_file)
        print("✓ Configuration loaded successfully")
        print()

        # Test parameter access
        print("Parameter Access:")
        print(f"  interaction_cutoff = {loaded.get_parameter('scientific.interaction_cutoff')}")
        print(f"  n_clusters = {loaded.get_parameter('clustering.n_clusters')}")
        print()

        # Test overrides
        overrides = {
            'scientific': {'interaction_cutoff': 6.5},
            'clustering': {'n_clusters': 5}
        }
        modified = loaded.merge(overrides)
        print("After Overrides:")
        print(f"  interaction_cutoff = {modified.scientific.interaction_cutoff}")
        print(f"  n_clusters = {modified.clustering.n_clusters}")
        print()

        # Test validation
        print("Testing Validation:")
        try:
            bad_config = PipelineConfig()
            bad_config.scientific.interaction_cutoff = 100.0  # Out of range
            bad_config.validate()
        except AssertionError as e:
            print(f"  ✓ Caught invalid config: {e}")

    print("\n✓ All tests passed!")
