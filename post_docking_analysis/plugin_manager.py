"""
Plugin architecture for post-docking analysis pipeline.

This module provides a framework for extending the pipeline with custom analysis modules.
"""
import importlib
import pkgutil
from pathlib import Path
from typing import Dict, List, Any, Callable
import inspect

class PluginManager:
    """
    Plugin manager for loading and executing analysis plugins.
    """
    
    def __init__(self, plugin_dirs: List[str] = None):
        """
        Initialize plugin manager.
        
        Parameters
        ----------
        plugin_dirs : List[str], optional
            List of directories to search for plugins
        """
        self.plugin_dirs = plugin_dirs or []
        self.plugins = {}
        self.loaded_modules = {}
        
    def discover_plugins(self) -> Dict[str, Dict[str, Any]]:
        """
        Discover available plugins.
        
        Returns
        -------
        Dict[str, Dict[str, Any]]
            Dictionary of discovered plugins
        """
        discovered_plugins = {}
        
        # Add built-in plugin directories
        builtin_dirs = [
            Path(__file__).parent / "plugins",
            Path(__file__).parent / "analysis_modules"
        ]
        
        # Combine with user-specified directories
        all_dirs = self.plugin_dirs + [str(d) for d in builtin_dirs]
        
        for plugin_dir in all_dirs:
            plugin_path = Path(plugin_dir)
            if plugin_path.exists():
                # Discover Python modules in the directory
                for module_info in pkgutil.iter_modules([str(plugin_path)]):
                    module_name = module_info.name
                    try:
                        # Import the module
                        spec = importlib.util.spec_from_file_location(
                            module_name, plugin_path / f"{module_name}.py"
                        )
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        
                        # Check if module has required plugin functions
                        if hasattr(module, 'analyze') and callable(module.analyze):
                            # Get plugin metadata
                            plugin_info = {
                                'name': getattr(module, 'PLUGIN_NAME', module_name),
                                'version': getattr(module, 'PLUGIN_VERSION', '1.0.0'),
                                'description': getattr(module, 'PLUGIN_DESCRIPTION', ''),
                                'author': getattr(module, 'PLUGIN_AUTHOR', 'Unknown'),
                                'module': module,
                                'path': plugin_path / f"{module_name}.py"
                            }
                            
                            discovered_plugins[module_name] = plugin_info
                            self.loaded_modules[module_name] = module
                            
                    except Exception as e:
                        print(f"⚠️  Failed to load plugin {module_name}: {e}")
        
        return discovered_plugins
    
    def load_plugins(self):
        """Load all discovered plugins."""
        self.plugins = self.discover_plugins()
        print(f"✅ Loaded {len(self.plugins)} plugins")
        
        # Print plugin information
        if self.plugins:
            print("🔌 Available plugins:")
            for name, info in self.plugins.items():
                print(f"  • {info['name']} v{info['version']} - {info['description']}")
    
    def execute_plugin(self, plugin_name: str, data: Dict[str, Any], 
                      output_dir: Path, config: Dict = None) -> Dict[str, Any]:
        """
        Execute a specific plugin.
        
        Parameters
        ----------
        plugin_name : str
            Name of the plugin to execute
        data : Dict[str, Any]
            Input data for the plugin
        output_dir : Path
            Output directory for plugin results
        config : Dict, optional
            Configuration for the plugin
            
        Returns
        -------
        Dict[str, Any]
            Results from the plugin execution
        """
        if plugin_name not in self.plugins:
            raise ValueError(f"Plugin '{plugin_name}' not found")
        
        plugin = self.plugins[plugin_name]
        module = plugin['module']
        
        print(f"⚙️  Executing plugin: {plugin['name']}")
        
        try:
            # Execute the plugin's analyze function
            if hasattr(module, 'analyze') and callable(module.analyze):
                results = module.analyze(data, output_dir, config or {})
                print(f"✅ Plugin '{plugin['name']}' executed successfully")
                return results
            else:
                raise ValueError(f"Plugin '{plugin_name}' does not have an 'analyze' function")
                
        except Exception as e:
            print(f"❌ Error executing plugin '{plugin_name}': {e}")
            raise
    
    def execute_all_plugins(self, data: Dict[str, Any], output_dir: Path, 
                           config: Dict = None) -> Dict[str, Any]:
        """
        Execute all loaded plugins.
        
        Parameters
        ----------
        data : Dict[str, Any]
            Input data for the plugins
        output_dir : Path
            Output directory for plugin results
        config : Dict, optional
            Configuration for the plugins
            
        Returns
        -------
        Dict[str, Any]
            Combined results from all plugin executions
        """
        all_results = {}
        
        for plugin_name in self.plugins:
            try:
                results = self.execute_plugin(plugin_name, data, output_dir, config)
                all_results[plugin_name] = results
            except Exception as e:
                print(f"⚠️  Plugin '{plugin_name}' failed: {e}")
                all_results[plugin_name] = {'error': str(e)}
        
        return all_results

# Example plugin interface
def create_plugin_template(plugin_name: str, plugin_dir: Path = None):
    """
    Create a template for a new analysis plugin.
    
    Parameters
    ----------
    plugin_name : str
        Name of the plugin
    plugin_dir : Path, optional
        Directory to create the plugin in
    """
    if plugin_dir is None:
        plugin_dir = Path(__file__).parent / "plugins"
    
    plugin_dir.mkdir(exist_ok=True)
    
    template = f'''"""
{plugin_name.title()} Analysis Plugin
"""

PLUGIN_NAME = "{plugin_name.title()} Analyzer"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Analysis plugin for {plugin_name}"
PLUGIN_AUTHOR = "Your Name"

def analyze(data: dict, output_dir: Path, config: dict) -> dict:
    """
    Analyze docking data.
    
    Parameters
    ----------
    data : dict
        Input data from the pipeline
    output_dir : Path
        Output directory for results
    config : dict
        Plugin configuration
        
    Returns
    -------
    dict
        Analysis results
    """
    # Your analysis code here
    results = {{
        "plugin": PLUGIN_NAME,
        "status": "completed",
        "results": []
    }}
    
    return results
'''
    
    plugin_file = plugin_dir / f"{plugin_name.lower()}_plugin.py"
    with open(plugin_file, 'w') as f:
        f.write(template)
    
    print(f"✅ Created plugin template: {plugin_file}")
    return plugin_file

# Integration with the main pipeline
def integrate_plugins(pipeline, plugin_dirs: List[str] = None):
    """
    Integrate plugins with the main pipeline.
    
    Parameters
    ----------
    pipeline : PostDockingAnalysisPipeline
        The main pipeline instance
    plugin_dirs : List[str], optional
        List of directories to search for plugins
    """
    print("🔌 Integrating plugins with pipeline...")
    
    # Create plugin manager
    plugin_manager = PluginManager(plugin_dirs)
    
    # Load plugins
    plugin_manager.load_plugins()
    
    # Store plugin manager in pipeline
    pipeline.plugin_manager = plugin_manager
    
    print("✅ Plugin integration completed")
    return plugin_manager