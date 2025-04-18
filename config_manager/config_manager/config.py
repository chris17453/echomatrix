import os
import sys
import yaml
import json
import logging
import configparser
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Union, Tuple

from .dot_notation import dict_to_namespace, namespace_to_dict, deep_merge
from .errors import ConfigError,  ConfigFileError,  ConfigFormatError,  ConfigValidationError

# Set up default logging for the module
logger = logging.getLogger('config_manager')
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.WARNING)  


class Config:
    """
    Flexible configuration manager that supports multiple file formats,
    environment variable overrides, and dot notation access.
    """
    
    def __init__(self, 
                 config_path: Optional[Union[str, Path]] = None,
                 default_config: Optional[Dict] = None,
                 env_prefix: Optional[str] = None,
                 search_paths: Optional[List[str]] = None,
                 format: Optional[str] = None,
                 required_keys: Optional[List[str]] = None,
                 log_level: int = logging.WARNING):
        """
        Initialize the configuration manager
        
        Args:
            config_path: Path to the configuration file
            default_config: Dictionary of default configuration values
            env_prefix: Prefix for environment variables (e.g., 'APP_')
            search_paths: List of paths to search for config files
            format: Format of the config file ('yaml', 'json', 'ini')
            required_keys: List of keys that must be present in the config
            log_level: Logging level for the config module
        
        Raises:
            ConfigFileError: If the config file cannot be found or read
            ConfigFormatError: If the config file format is invalid
            ConfigValidationError: If required keys are missing
        """
        # Configure logging
        logger.setLevel(log_level)
        
        # Initialize config properties
        self._config_path = config_path
        self._env_prefix = env_prefix
        self._default_config = default_config or {}
        self._format = format
        self._required_keys = required_keys or []
        
        # If no config path is provided, try to find a config file
        if self._config_path is None and search_paths:
            self._config_path = self._find_config_file(search_paths)
        
        # Start with default config
        merged_config = self._default_config.copy()
        
        # Try to load user config if path is provided
        if self._config_path:
            try:
                user_config = self._load_config_file(self._config_path)
                # Deep merge user config into default config
                deep_merge(merged_config, user_config)
            except (IOError, yaml.YAMLError, json.JSONDecodeError) as e:
                error_msg = f"Error loading config file {self._config_path}: {str(e)}"
                logger.error(error_msg)
                raise ConfigFileError(error_msg) from e
        
        # Apply environment variable overrides if prefix is provided
        if self._env_prefix:
            env_config = self._load_from_env()
            deep_merge(merged_config, env_config)
        
        # Validate required keys if specified
        if self._required_keys:
            self._validate_required_keys(merged_config)
        
        # Set attributes from merged config
        for key, value in merged_config.items():
            if isinstance(value, dict):
                # Convert dictionaries to namespaces for dot notation
                setattr(self, key, dict_to_namespace(value))
            else:
                setattr(self, key, value)
    
    def _find_config_file(self, search_paths: List[str]) -> Optional[str]:
        """
        Search for a config file in the provided paths
        
        Args:
            search_paths: List of paths to search
            
        Returns:
            Path to the config file if found, None otherwise
        """
        extensions = ['.yaml', '.yml', '.json', '.ini', '.conf']
        base_names = ['config', 'settings', 'app_config']
        
        for path in search_paths:
            for base in base_names:
                for ext in extensions:
                    file_path = os.path.join(path, f"{base}{ext}")
                    if os.path.isfile(file_path):
                        logger.info(f"Found config file at {file_path}")
                        return file_path
        
        logger.warning("No config file found in search paths")
        return None
    
    def _load_config_file(self, config_path: Union[str, Path]) -> Dict:
        """
        Load a configuration file based on its extension
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            Dictionary containing the configuration values
            
        Raises:
            ConfigFileError: If the file cannot be read
            ConfigFormatError: If the file format is invalid
        """
        path = Path(config_path)
        
        if not path.exists():
            error_msg = f"Config file does not exist: {path}"
            logger.error(error_msg)
            raise ConfigFileError(error_msg)
        
        # Determine format from file extension or specified format
        format = self._format
        if not format:
            ext = path.suffix.lower()
            if ext in ['.yml', '.yaml']:
                format = 'yaml'
            elif ext == '.json':
                format = 'json'
            elif ext in ['.ini', '.conf']:
                format = 'ini'
            else:
                format = 'yaml'  # Default to YAML
        
        # Load the file based on its format
        try:
            with open(path, 'r') as f:
                if format == 'yaml':
                    config = yaml.safe_load(f) or {}
                elif format == 'json':
                    config = json.load(f)
                elif format == 'ini':
                    parser = configparser.ConfigParser()
                    parser.read(path)
                    config = {section: dict(parser.items(section)) 
                              for section in parser.sections()}
                else:
                    error_msg = f"Unsupported config format: {format}"
                    logger.error(error_msg)
                    raise ConfigFormatError(error_msg)
                    
            logger.info(f"Loaded config from {path}")
            return config
        except Exception as e:
            error_msg = f"Error reading config file {path}: {str(e)}"
            logger.error(error_msg)
            raise ConfigFileError(error_msg) from e
    
    def _load_from_env(self) -> Dict:
        """
        Load configuration from environment variables
        
        Returns:
            Dictionary of configuration values from environment variables
        """
        if not self._env_prefix:
            return {}
            
        env_config = {}
        prefix_len = len(self._env_prefix)
        
        for key, value in os.environ.items():
            if key.startswith(self._env_prefix):
                # Remove prefix and convert to lowercase
                config_key = key[prefix_len:].lower()
                
                # Handle nested keys using double underscore
                if '__' in config_key:
                    parts = config_key.split('__')
                    current = env_config
                    for part in parts[:-1]:
                        if part not in current:
                            current[part] = {}
                        current = current[part]
                    current[parts[-1]] = self._convert_env_value(value)
                else:
                    env_config[config_key] = self._convert_env_value(value)
        
        logger.debug(f"Loaded configuration from environment variables: {env_config}")
        return env_config
    
    def _convert_env_value(self, value: str) -> Any:
        """
        Convert environment variable string value to appropriate type
        
        Args:
            value: String value from environment variable
            
        Returns:
            Converted value (bool, int, float, or string)
        """
        # Convert boolean values
        if value.lower() in ('true', 'yes', '1'):
            return True
        if value.lower() in ('false', 'no', '0'):
            return False
            
        # Try to convert to numeric values
        try:
            if '.' in value:
                return float(value)
            return int(value)
        except ValueError:
            # Return as string if not numeric
            return value
    
    def _validate_required_keys(self, config: Dict) -> None:
        """
        Validate that required keys are present in the configuration
        
        Args:
            config: Configuration dictionary to validate
            
        Raises:
            ConfigValidationError: If required keys are missing
        """
        missing_keys = []
        
        for key in self._required_keys:
            if '.' in key:
                # Handle nested keys
                parts = key.split('.')
                current = config
                for part in parts:
                    if not isinstance(current, dict) or part not in current:
                        missing_keys.append(key)
                        break
                    current = current[part]
            elif key not in config:
                missing_keys.append(key)
        
        if missing_keys:
            error_msg = f"Missing required configuration keys: {', '.join(missing_keys)}"
            logger.error(error_msg)
            raise ConfigValidationError(error_msg)
    
    def save(self, config_path: Optional[Union[str, Path]] = None) -> None:
        """
        Save the current configuration to a file
        
        Args:
            config_path: Path to save the configuration to (defaults to original path)
            
        Raises:
            ConfigFileError: If the file cannot be written
        """
        path = Path(config_path or self._config_path)
        if not path:
            error_msg = "No config path specified for saving"
            logger.error(error_msg)
            raise ConfigFileError(error_msg)
        
        # Create directory if it doesn't exist
        os.makedirs(path.parent, exist_ok=True)
        
        # Convert to dictionary
        config_dict = self.get_config()
        
        # Determine format from file extension
        format = self._format
        if not format:
            ext = path.suffix.lower()
            if ext in ['.yml', '.yaml']:
                format = 'yaml'
            elif ext == '.json':
                format = 'json'
            elif ext in ['.ini', '.conf']:
                format = 'ini'
            else:
                format = 'yaml'  # Default to YAML
        
        try:
            with open(path, 'w') as f:
                if format == 'yaml':
                    yaml.safe_dump(config_dict, f, default_flow_style=False)
                elif format == 'json':
                    json.dump(config_dict, f, indent=2)
                elif format == 'ini':
                    parser = configparser.ConfigParser()
                    for section, values in config_dict.items():
                        parser.add_section(section)
                        if isinstance(values, dict):
                            for key, value in values.items():
                                if not isinstance(value, (dict, list)):
                                    parser.set(section, key, str(value))
                    parser.write(f)
                else:
                    error_msg = f"Unsupported config format for saving: {format}"
                    logger.error(error_msg)
                    raise ConfigFormatError(error_msg)
                    
            logger.info(f"Saved config to {path}")
        except Exception as e:
            error_msg = f"Error saving config to {path}: {str(e)}"
            logger.error(error_msg)
            raise ConfigFileError(error_msg) from e
    
    def get_config(self) -> Dict:
        """
        Get the entire configuration as a dictionary
        
        Returns:
            Dictionary containing all configuration values
        """
        config_data = {}
        for key in self._default_config:
            attr = getattr(self, key, None)
            if isinstance(attr, SimpleNamespace):
                config_data[key] = namespace_to_dict(attr)
            else:
                config_data[key] = attr
                
        # Add any additional attributes that weren't in default config
        for key in dir(self):
            if not key.startswith('_') and key not in config_data:
                attr = getattr(self, key, None)
                if not callable(attr):
                    if isinstance(attr, SimpleNamespace):
                        config_data[key] = namespace_to_dict(attr)
                    else:
                        config_data[key] = attr
                        
        return config_data
    
    def get(self, key: Optional[str] = None, default: Any = None) -> Any:
        """
        Get configuration value by key or the entire config if key is None
        
        Args:
            key: Dot notation path to the config value (e.g., 'server.port')
            default: Value to return if key is not found
            
        Returns:
            The requested configuration value or default if not found
        """
        if key is None:
            return self.get_config()
            
        # Handle dot notation (e.g., 'server.port')
        parts = key.split('.')
        result = self
        
        try:
            for part in parts:
                result = getattr(result, part)
            return result
        except (AttributeError, KeyError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value
        
        Args:
            key: Dot notation path to the config value (e.g., 'server.port')
            value: Value to set
        """
        if '.' not in key:
            setattr(self, key, value)
            return
            
        # Handle dot notation for nested keys
        parts = key.split('.')
        current = self
        
        # Navigate to the parent object
        for part in parts[:-1]:
            if not hasattr(current, part):
                # Create intermediate objects if they don't exist
                setattr(current, part, SimpleNamespace())
            current = getattr(current, part)
            
        # Set the value on the parent object
        setattr(current, parts[-1], value)
    
    def update(self, data: Dict, prefix: Optional[str] = None) -> None:
        """
        Update multiple configuration values
        
        Args:
            data: Dictionary of values to update
            prefix: Optional prefix for all keys
        """
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                # Recursively update nested dictionaries
                self.update(value, full_key)
            else:
                self.set(full_key, value)
    
    def __iter__(self):
        """
        Make the Config object iterable at the top level
        
        Returns:
            Iterator of (key, value) pairs for top-level attributes
        """
        for key in vars(self):
            if not key.startswith('_'):
                yield key, getattr(self, key)
    
    def items(self, section: Optional[str] = None) -> List[Tuple[str, Any]]:
        """
        Get items in a specific section or all top-level items
        
        Args:
            section: Section name to get items from
            
        Returns:
            List of (key, value) tuples
        """
        if section is None:
            # Return top-level items (excluding internal attributes)
            return [(k, v) for k, v in vars(self).items() if not k.startswith('_')]
        
        # Get the section
        section_obj = getattr(self, section, None)
        if section_obj is None:
            return []
            
        if isinstance(section_obj, SimpleNamespace):
            return list(section_obj.__dict__.items())
        
        return []
    
    def get_section_items(self, path: str) -> List[Tuple[str, Any]]:
        """
        Get items from a nested section using dot notation
        
        Args:
            path: Dot notation path to the section (e.g., 'app.server.settings')
            
        Returns:
            List of (key, value) tuples or empty list if path not found
        """
        section = self.get(path)
        
        if section is None:
            return []
            
        if isinstance(section, SimpleNamespace):
            return list(section.__dict__.items())
        
        # If it's a dict, return its items
        if isinstance(section, dict):
            return list(section.items())
            
        # If it's a single value, not a container, return empty list
        return []
    
    def reload(self) -> None:
        """
        Reload configuration from the source file
        
        Raises:
            ConfigFileError: If the config file cannot be reloaded
        """
        if not self._config_path:
            logger.warning("No config path specified for reloading")
            return
            
        logger.info(f"Reloading configuration from {self._config_path}")
        
        # Create a new instance with the same parameters
        new_config = Config(
            config_path=self._config_path,
            default_config=self._default_config,
            env_prefix=self._env_prefix,
            format=self._format,
            required_keys=self._required_keys
        )
        
        # Update this instance with the new values
        config_dict = new_config.get_config()
        for key, value in config_dict.items():
            if isinstance(value, dict):
                setattr(self, key, dict_to_namespace(value))
            else:
                setattr(self, key, value)
                
        logger.info("Configuration reloaded successfully")
    
    @classmethod
    def from_dict(cls, config_dict: Dict, **kwargs) -> 'Config':
        """
        Create a Config instance from a dictionary
        
        Args:
            config_dict: Dictionary containing configuration values
            **kwargs: Additional arguments to pass to the Config constructor
            
        Returns:
            Config instance
        """
        instance = cls(default_config=config_dict, **kwargs)
        return instance
    
    @classmethod
    def from_env(cls, env_prefix: str, **kwargs) -> 'Config':
        """
        Create a Config instance from environment variables
        
        Args:
            env_prefix: Prefix for environment variables
            **kwargs: Additional arguments to pass to the Config constructor
            
        Returns:
            Config instance
        """
        instance = cls(env_prefix=env_prefix, **kwargs)
        return instance


def setup_file_logging(log_dir: str = '/var/log', 
                       app_name: str = 'app',
                       log_level: int = logging.INFO) -> None:
    """
    Set up file logging for the config manager
    
    Args:
        log_dir: Directory to store log files
        app_name: Name of the application (used in log file name)
        log_level: Logging level
    """
    log_path = os.path.join(log_dir, f'{app_name}')
    os.makedirs(log_path, exist_ok=True)
    
    file_handler = logging.FileHandler(os.path.join(log_path, 'config_manager.log'))
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.setLevel(log_level)
    
    logger.info(f"File logging set up at {os.path.join(log_path, 'config_manager.log')}")


# Default search paths for configuration files on Fedora/CentOS systems
DEFAULT_SEARCH_PATHS = [
    os.path.expanduser('~/.config'),
    '/etc',
    '/etc/app',
    os.getcwd(),
]
