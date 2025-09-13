"""
Configuration management for post-docking analysis pipeline.
"""
import os
from pathlib import Path
import json
from typing import Dict, Any

# Default configuration
DEFAULT_CONFIG = {
    # Input/Output Directories
    "input_dir": "",
    "output_dir": "./post_docking_results",
    
    # Structure Processing
    "split_complexes": True,
    "extract_apo_proteins": True,
    "extract_ligands": True,
    
    # Analysis Parameters
    "analyze_binding_affinity": True,
    "generate_visualizations": True,
    "create_summary_reports": True,
    
    # File Format Options
    "output_csv": True,
    "output_excel": True,
    "output_pdb": True,
    "output_mol2": True,
    
    # Advanced Options
    "fix_chains": False,
    "run_additional_docking": False,
    
    # Scoring Function Options
    "use_vina_score": True,
    "use_cnn_score": True,
    
    # Directory Structure Options
    "directory_structure": "AUTO",  # AUTO, SINGLE_FOLDER, or MULTI_FOLDER
    
    # For MULTI_FOLDER structure, specify patterns
    "receptor_pattern": "*receptor*.pdb",
    "ligand_pattern": "*ligand*.sdf",
    "docking_result_pattern": "*out*.pdbqt"
}

class ConfigManager:
    """
    Configuration manager for the post-docking analysis pipeline.
    """
    
    def __init__(self, config_file: str = None):
        """
        Initialize the configuration manager.
        
        Parameters
        ----------
        config_file : str, optional
            Path to configuration file
        """
        self.config = DEFAULT_CONFIG.copy()
        
        if config_file:
            self.load_config(config_file)
    
    def load_config(self, config_file: str):
        """
        Load configuration from a file.
        
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
                file_config = json.load(f)
            
            # Update default config with file config
            self.config.update(file_config)
            print(f"✅ Configuration loaded from: {config_file}")
        except Exception as e:
            print(f"❌ Error loading configuration file: {e}")
    
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
                json.dump(self.config, f, indent=2)
            print(f"✅ Configuration saved to: {config_file}")
        except Exception as e:
            print(f"❌ Error saving configuration file: {e}")
    
    def get(self, key: str, default=None):
        """
        Get a configuration value.
        
        Parameters
        ----------
        key : str
            Configuration key
        default : any, optional
            Default value if key not found
            
        Returns
        -------
        any
            Configuration value
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value):
        """
        Set a configuration value.
        
        Parameters
        ----------
        key : str
            Configuration key
        value : any
            Configuration value
        """
        self.config[key] = value
    
    def update(self, config_dict: Dict[str, Any]):
        """
        Update multiple configuration values.
        
        Parameters
        ----------
        config_dict : Dict[str, Any]
            Dictionary of configuration values to update
        """
        self.config.update(config_dict)

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