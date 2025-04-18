# Config Manager

A flexible and powerful configuration management library for Python applications, designed with simplicity and extensibility in mind.

## Features

- **Multiple file formats**: YAML, JSON, INI/ConfigParser support
- **Dot notation access**: Access nested config values with simple dot notation
- **Environment variable overrides**: Override config values with environment variables
- **Flexible search paths**: Automatically find config files in typical system locations
- **Validation**: Ensure required configuration keys are present
- **Default configuration**: Provide fallback values when needed
- **Fedora/CentOS optimized**: Default paths follow Linux filesystem hierarchy standard
- **Command-line interface**: Manage configurations directly from the terminal

## Installation

```bash
pip install config_manager
```

## Quick Start

```python
from config_manager import config_manager

# Basic usage with a config file
config = config_manager('config.yaml')

# Access configuration values using dot notation
print(f"Server running on {config.server.host}:{config.server.port}")

# Access with a default value if the key doesn't exist
debug = config.get('app.debug', False)
```

## Advanced Usage

```python
from config_manager import config_manager, Config

# Create a configuration with more options
config = config_manager(
    config_path='config.yaml',
    default_config={
        'app': {
            'name': 'MyApp',
            'version': '1.0.0',
            'debug': False
        },
        'server': {
            'host': '127.0.0.1',
            'port': 8080
        }
    },
    env_prefix='MYAPP_',
    required_keys=['app.name', 'server.host', 'server.port']
)

# Access nested configuration
print(f"App name: {config.app.name}")
print(f"Server: {config.server.host}:{config.server.port}")

# Update configuration values
config.set('app.debug', True)

# Save configuration to a file
config.save('new_config.yaml')

# Create a configuration from a dictionary
conf_dict = {
    'database': {
        'url': 'postgresql://user:pass@localhost/db',
        'pool_size': 5
    }
}
db_config = Config.from_dict(conf_dict)

# Create a configuration from environment variables only
env_config = Config.from_env('MYAPP_')
```

## Command-line Interface

Config Manager comes with a powerful CLI for managing configuration files from the terminal:

```bash
# Get configuration values
config_manager get config.yaml app.name
config_manager get --format=json config.yaml server

# Set configuration values
config_manager set config.yaml app.debug true
config_manager set --create config.yaml database.url "postgresql://localhost/mydb"

# Create a new configuration file
config_manager create --format=yaml default_config.yaml
config_manager create --template=template.yaml --vars='{"app.name":"MyApp"}' config.yaml

# Validate configuration files
config_manager validate --required=app.name,server.port config.yaml

# Convert between formats
config_manager convert config.ini config.yaml

# List all configuration values
config_manager list config.yaml
config_manager list --section=server --format=json config.yaml

# Show configuration from environment variables
config_manager env MYAPP_ --format=yaml
```

Use the `--verbose` or `-v` flag to increase output verbosity. For full help, run:

```bash
config_manager --help
```

## Environment Variables

Environment variables can override configuration values. For example:

```bash
# Set environment variables (on Linux/macOS)
export MYAPP_SERVER__HOST=0.0.0.0
export MYAPP_SERVER__PORT=9000
export MYAPP_APP__DEBUG=true

# Double underscores (__) are used for nested keys
```

Then in your Python code:

```python
config = config_manager(
    config_path='config.yaml',
    env_prefix='MYAPP_'
)

# Environment variables override the config file values
print(config.server.host)  # Outputs: 0.0.0.0
print(config.server.port)  # Outputs: 9000
print(config.app.debug)    # Outputs: True
```

## Logging

The config manager includes built-in logging capabilities:

```python
import logging
from config_manager import config_manager, setup_file_logging

# Setup file logging (optional)
setup_file_logging(log_dir='/var/log', app_name='myapp', log_level=logging.INFO)

# Set log level for console output
config = config_manager('config.yaml', log_level=logging.DEBUG)
```

## License

This project is licensed under the BSD 3-Clause License - see the LICENSE file for details.
