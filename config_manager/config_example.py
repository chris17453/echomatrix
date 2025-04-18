#!/usr/bin/env python3
"""
Example usage of the config_manager module
"""

import os
import sys
from config_manager import Config, setup_file_logging

# Set up logging to file if running as root
if os.geteuid() == 0:
    setup_file_logging(app_name='myapp')

# Default configuration
default_config = {
    'app': {
        'name': 'MyApp',
        'version': '1.0.0',
        'debug': False
    },
    'server': {
        'host': '127.0.0.1',
        'port': 8080,
        'timeout': 30
    },
    'database': {
        'url': 'sqlite:///app.db',
        'pool_size': 5,
        'timeout': 10
    },
    'logging': {
        'level': 'INFO',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    }
}

# Search paths - follows XDG Base Directory Specification
search_paths = [
    os.path.join(os.getcwd(), 'config'),
    os.path.expanduser('~/.config/myapp'),
    '/etc/myapp'
]

def main():
    # Initialize the configuration
    try:
        config = Config(
            default_config=default_config,
            search_paths=search_paths,
            env_prefix='MYAPP_',
            required_keys=['app.name', 'server.host', 'server.port'],
            log_level=20  # INFO level
        )
        
        # Access configuration using dot notation
        print(f"App name: {config.app.name}")
        print(f"Server: {config.server.host}:{config.server.port}")
        
        # Get a specific value with a default
        debug_mode = config.get('app.debug', False)
        print(f"Debug mode: {debug_mode}")
        
        # Iterate through sections
        print("\nDatabase configuration:")
        for key, value in config.items('database'):
            print(f"  {key}: {value}")
        
        # Modify a configuration value
        config.set('app.debug', True)
        print(f"\nUpdated debug mode: {config.app.debug}")
        
        # Save the configuration
        if len(sys.argv) > 1 and sys.argv[1] == '--save':
            config.save('config.yaml')
            print("Configuration saved to config.yaml")
            
    except Exception as e:
        print(f"Error: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
