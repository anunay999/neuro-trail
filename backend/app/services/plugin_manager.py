import importlib
import importlib.util
import inspect
import os
import logging
from typing import Dict, Any, Type, List, Optional, TypeVar

from app.core.plugin_base import PluginBase
from app.core.exceptions import PluginNotFoundError, PluginInitializationError
from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Type variable for plugins
T = TypeVar('T', bound=PluginBase)


class PluginManager:
    """Manager for discovering and loading plugins"""
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one instance exists"""
        if cls._instance is None:
            cls._instance = super(PluginManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize plugin manager if not already initialized"""
        if not getattr(self, "_initialized", False):
            # Initialize plugin registries
            self._plugins: Dict[str, Dict[str, Type[PluginBase]]] = {}
            self._active_plugins: Dict[str, Dict[str, PluginBase]] = {}
            self._initialized = True
    
    def discover_plugins(self) -> None:
        """
        Discover plugins in the plugins directory
        """
        logger.info("Discovering plugins...")
        
        # Plugin directories to check
        plugin_dirs = [
            # Built-in plugins
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "plugins"),
            # External plugins directory from settings
            settings.PLUGINS_DIR,
        ]
        
        for plugin_dir in plugin_dirs:
            if not os.path.exists(plugin_dir):
                logger.warning(f"Plugin directory not found: {plugin_dir}")
                continue
            
            # Walk through all subdirectories
            for subdir in next(os.walk(plugin_dir))[1]:
                # Skip hidden directories
                if subdir.startswith('.') or subdir.startswith('__'):
                    continue
                
                plugin_type_dir = os.path.join(plugin_dir, subdir)
                self._discover_plugins_in_dir(plugin_type_dir, subdir)
    
    def _discover_plugins_in_dir(self, directory: str, plugin_type: str) -> None:
        """
        Discover plugins in a specific directory
        
        Args:
            directory: Directory to search for plugins
            plugin_type: Type of plugins in this directory
        """
        if not os.path.exists(directory):
            return
        
        logger.info(f"Scanning for {plugin_type} plugins in {directory}")
        
        # Initialize plugin type in registry if not exists
        if plugin_type not in self._plugins:
            self._plugins[plugin_type] = {}
        
        # Walk through all Python files
        for filename in os.listdir(directory):
            if filename.startswith('__') or not filename.endswith('.py'):
                continue
            
            # Get module name from filename
            module_name = filename[:-3]  # Remove .py extension
            full_path = os.path.join(directory, filename)
            
            # Try to load the module
            try:
                spec = importlib.util.spec_from_file_location(
                    f"plugins.{plugin_type}.{module_name}", full_path
                )
                if spec is None or spec.loader is None:
                    continue
                
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Find plugin classes in the module
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and issubclass(obj, PluginBase) 
                        and obj != PluginBase and obj.__module__ == module.__name__):
                        # Register plugin
                        if hasattr(obj, 'plugin_name') and obj.plugin_name != 'base':
                            plugin_name = obj.plugin_name
                            self._plugins[plugin_type][plugin_name] = obj
                            logger.info(f"Discovered plugin: {plugin_type}.{plugin_name}")
            
            except Exception as e:
                logger.error(f"Error loading plugin module {module_name}: {e}")
    
    def get_plugin_class(self, plugin_type: str, plugin_name: str) -> Type[PluginBase]:
        """
        Get a plugin class by type and name
        
        Args:
            plugin_type: Type of plugin
            plugin_name: Name of plugin
            
        Returns:
            Type[PluginBase]: Plugin class
            
        Raises:
            PluginNotFoundError: If plugin not found
        """
        if plugin_type not in self._plugins or plugin_name not in self._plugins[plugin_type]:
            raise PluginNotFoundError(f"Plugin not found: {plugin_type}.{plugin_name}")
        
        return self._plugins[plugin_type][plugin_name]
    
    def get_available_plugins(self, plugin_type: Optional[str] = None) -> Dict[str, List[str]]:
        """
        Get available plugins, optionally filtered by type
        
        Args:
            plugin_type: Optional type to filter by
            
        Returns:
            Dict[str, List[str]]: Dictionary of plugin types to lists of plugin names
        """
        result = {}
        
        if plugin_type:
            if plugin_type in self._plugins:
                result[plugin_type] = list(self._plugins[plugin_type].keys())
        else:
            for p_type, plugins in self._plugins.items():
                result[p_type] = list(plugins.keys())
        
        return result
    
    async def initialize_plugin(
        self, 
        plugin_type: str, 
        plugin_name: str, 
        **kwargs
    ) -> PluginBase:
        """
        Initialize a plugin instance
        
        Args:
            plugin_type: Type of plugin
            plugin_name: Name of plugin
            **kwargs: Additional initialization parameters
            
        Returns:
            PluginBase: Initialized plugin instance
            
        Raises:
            PluginNotFoundError: If plugin not found
            PluginInitializationError: If plugin initialization fails
        """
        # Get plugin class
        plugin_class = self.get_plugin_class(plugin_type, plugin_name)
        
        # Check if already active
        if (plugin_type in self._active_plugins and 
            plugin_name in self._active_plugins[plugin_type]):
            return self._active_plugins[plugin_type][plugin_name]
        
        # Initialize plugin
        try:
            plugin_instance = plugin_class()
            if not await plugin_instance.initialize(**kwargs):
                raise PluginInitializationError(
                    f"Failed to initialize plugin: {plugin_type}.{plugin_name}"
                )
            
            # Store active plugin
            if plugin_type not in self._active_plugins:
                self._active_plugins[plugin_type] = {}
            
            self._active_plugins[plugin_type][plugin_name] = plugin_instance
            logger.info(f"Initialized plugin: {plugin_type}.{plugin_name}")
            
            return plugin_instance
        
        except Exception as e:
            logger.error(f"Error initializing plugin {plugin_type}.{plugin_name}: {e}")
            raise PluginInitializationError(f"Error initializing plugin: {str(e)}")
    
    async def get_plugin(
        self, 
        plugin_type: str, 
        plugin_name: str,
        init_if_not_active: bool = True,
        **kwargs
    ) -> PluginBase:
        """
        Get an active plugin instance, initializing if necessary
        
        Args:
            plugin_type: Type of plugin
            plugin_name: Name of plugin
            init_if_not_active: Whether to initialize if not active
            **kwargs: Additional initialization parameters
            
        Returns:
            PluginBase: Plugin instance
            
        Raises:
            PluginNotFoundError: If plugin not found
        """
        # Check if already active
        if (plugin_type in self._active_plugins and 
            plugin_name in self._active_plugins[plugin_type]):
            return self._active_plugins[plugin_type][plugin_name]
        
        # Initialize if requested
        if init_if_not_active:
            return await self.initialize_plugin(plugin_type, plugin_name, **kwargs)
        
        # Not active and not initializing
        raise PluginNotFoundError(
            f"Plugin not active: {plugin_type}.{plugin_name}"
        )
    
    async def get_plugin_by_type(
        self, 
        plugin_type: str, 
        plugin_class: Type[T],
        **kwargs
    ) -> Optional[T]:
        """
        Get the first active plugin of a specific type and class
        
        Args:
            plugin_type: Type of plugin
            plugin_class: Class to filter by
            **kwargs: Additional initialization parameters
            
        Returns:
            Optional[T]: Plugin instance or None if not found
        """
        if plugin_type not in self._active_plugins:
            return None
        
        for plugin in self._active_plugins[plugin_type].values():
            if isinstance(plugin, plugin_class):
                return plugin
        
        # Try to find in available plugins
        if plugin_type in self._plugins:
            for plugin_name, plugin_cls in self._plugins[plugin_type].items():
                if issubclass(plugin_cls, plugin_class):
                    # Initialize and return
                    return await self.initialize_plugin(plugin_type, plugin_name, **kwargs)
        
        return None
    
    async def shutdown_plugin(self, plugin_type: str, plugin_name: str) -> bool:
        """
        Shutdown a plugin
        
        Args:
            plugin_type: Type of plugin
            plugin_name: Name of plugin
            
        Returns:
            bool: True if successful, False otherwise
        """
        if (plugin_type in self._active_plugins and 
            plugin_name in self._active_plugins[plugin_type]):
            
            plugin = self._active_plugins[plugin_type][plugin_name]
            try:
                if await plugin.shutdown():
                    del self._active_plugins[plugin_type][plugin_name]
                    logger.info(f"Shutdown plugin: {plugin_type}.{plugin_name}")
                    return True
            except Exception as e:
                logger.error(f"Error shutting down plugin {plugin_type}.{plugin_name}: {e}")
        
        return False
    
    async def shutdown_all(self) -> None:
        """Shutdown all active plugins"""
        for plugin_type, plugins in self._active_plugins.items():
            for plugin_name in list(plugins.keys()):
                await self.shutdown_plugin(plugin_type, plugin_name)

# Singleton instance
plugin_manager = PluginManager()