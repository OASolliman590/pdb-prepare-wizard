"""
Configuration management for post-docking analysis pipeline.
Supports both JSON and YAML configuration files.
"""
import os
from pathlib import Path
import json
from typing import Dict, Any
import yaml

# Default configuration
DEFAULT_CONFIG = {
    # Analysis Parameters
    "analysis": {
        "docking_types": ["vina", "gnina"],
        "comparative_benchmark": "*",
        "binding_affinity_analysis": True,
        "rmsd_analysis": True,
        "generate_visualizations": True,
        "extract_poses": True
    },
    
    # Input/Output Directories
    "paths": {
        "input_dir": "",
        "output_dir": "./post_docking_results",
        "receptors_dir": "",
        "gnina_out_dir": ""
    },
    
    # Pose Extraction Parameters
    "pose_extraction": {
        "extract_all_poses": False,
        "best_pose_criteria": "affinity",
        "output_formats": ["pdb"]
    },
    
    # Binding Affinity Analysis Parameters
    "binding_affinity": {
        "strong_binder_threshold": -8.0,
        "top_performers_count": 10,
        "analyze_by_protein": True,
        "analyze_by_ligand": True
    },
    
    # RMSD Analysis Parameters
    "rmsd": {
        "clustering_method": "kmeans",
        "kmeans_clusters": 3,
        "dbscan_epsilon": 2.0,
        "dbscan_min_samples": 2
    },
    
    # Visualization Parameters
    "visualization": {
        "output_formats": ["png"],
        "dpi": 300,
        "generate_3d": True,
        "generate_2d_interactions": True
    },
    
    # Advanced Options
    "advanced": {
        "fix_chains": False,
        "run_additional_docking": False,
        "directory_structure": "AUTO",
        "receptor_pattern": "*receptor*.pdb",
        "ligand_pattern": "*ligand*.sdf",
        "docking_result_pattern": "*out*.pdbqt"
    }
}

class ConfigManager:
    """
    Configuration manager for the post-docking analysis pipeline.
    Supports both JSON and YAML configuration files.
    """
    
    def __init__(self, config_file: str = None):
        """
        Initialize the configuration manager.
        
        Parameters
        ----------
        config_file : str, optional
            Path to configuration file
        """
        self.config = self._deep_copy_dict(DEFAULT_CONFIG)
        
        if config_file:
            self.load_config(config_file)
    
    def _deep_copy_dict(self, d):
        """Create a deep copy of a dictionary."""
        if isinstance(d, dict):
            return {k: self._deep_copy_dict(v) for k, v in d.items()}
        elif isinstance(d, list):
            return [self._deep_copy_dict(item) for item in d]
        else:
            return d
    
    def load_config(self, config_file: str):
        """
        Load configuration from a file (JSON or YAML).
        
        Parameters
        ----------
        config_file : str
            Path to configuration file
        """
        config_path = Path(config_file)
        if not config_path.exists():
            print(f"⚠️  Configuration file not found: {config_file}")
            return
        
        try:
            with open(config_path, 'r') as f:
                if config_file.endswith('.yaml') or config_file.endswith('.yml'):
                    file_config = yaml.safe_load(f)
                else:
                    file_config = json.load(f)
            
            # Update default config with file config
            self._update_nested_dict(self.config, file_config)
            print(f"✅ Configuration loaded from: {config_file}")
        except Exception as e:
            print(f"❌ Error loading configuration file: {e}")
    
    def _update_nested_dict(self, base_dict, update_dict):
        """Update nested dictionary values."""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._update_nested_dict(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def save_config(self, config_file: str):
        """
        Save current configuration to a file.
        
        Parameters
        ----------
        config_file : str
            Path to configuration file
        """
        config_path = Path(config_file)
        try:
            with open(config_path, 'w') as f:
                if config_file.endswith('.yaml') or config_file.endswith('.yml'):
                    yaml.dump(self.config, f, indent=2, default_flow_style=False)
                else:
                    json.dump(self.config, f, indent=2)
            print(f"✅ Configuration saved to: {config_file}")
        except Exception as e:
            print(f"❌ Error saving configuration file: {e}")
    
    def get(self, key_path: str, default=None):
        """
        Get a configuration value using dot notation (e.g., 'analysis.docking_types').
        
        Parameters
        ----------
        key_path : str
            Configuration key path (dot-separated)
        default : any, optional
            Default value if key not found
            
        Returns
        -------
        any
            Configuration value
        """
        keys = key_path.split('.')
        current = self.config
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value):
        """
        Set a configuration value using dot notation.
        
        Parameters
        ----------
        key_path : str
            Configuration key path (dot-separated)
        value : any
            Configuration value
        """
        keys = key_path.split('.')
        current = self.config
        
        # Navigate to the parent dictionary
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set the final value
        current[keys[-1]] = value
    
    def update(self, config_dict: Dict[str, Any]):
        """
        Update multiple configuration values.
        
        Parameters
        ----------
        config_dict : Dict[str, Any]
            Dictionary of configuration values to update
        """
        self._update_nested_dict(self.config, config_dict)

def load_config(config_file: str = None):
    """
    Load configuration from a file or return default configuration.
    
    Parameters
    ----------
    config_file : str, optional
        Path to configuration file
        
    Returns
    -------
    ConfigManager
        Configuration manager instance
    """
    return ConfigManager(config_file)