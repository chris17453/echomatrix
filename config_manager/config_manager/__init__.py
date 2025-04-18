import sys
from .config import Config, setup_file_logging, DEFAULT_SEARCH_PATHS
from .errors import ConfigError, ConfigFileError, ConfigFormatError, ConfigValidationError
from .dot_notation import dict_to_namespace, namespace_to_dict, deep_merge


def config_manager(config_path=None, default_config=None, **kwargs):
    """
    Factory function to create a Config instance.
    
    Args:
        config_path: Path to the configuration file
        default_config: Dictionary of default configuration values
        **kwargs: Additional arguments to pass to the Config constructor
        
    Returns:
        Config instance
    """
    return Config(config_path=config_path, default_config=default_config, **kwargs)


__all__ = [
    'Config', 
    'setup_file_logging',
    'DEFAULT_SEARCH_PATHS',
    'ConfigError',
    'ConfigFileError',
    'ConfigFormatError',
    'ConfigValidationError',
    'dict_to_namespace',
    'namespace_to_dict', 
    'deep_merge',
    'config_manager'
]


