#!/usr/bin/env python3
"""
Command-line interface for the config_manager package.
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

from .config import Config, DEFAULT_SEARCH_PATHS
from .errors import ConfigError

def setup_parser() -> argparse.ArgumentParser:
    """
    Set up the argument parser for the CLI.
    
    Returns:
        ArgumentParser: The configured argument parser
    """
    parser = argparse.ArgumentParser(
        description='Config Manager CLI - manipulate configuration files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  config_manager get config.yaml app.name
  config_manager get --format=json config.yaml server
  config_manager set config.yaml app.debug true
  config_manager create --format=yaml default_config.yaml
  config_manager validate --required=app.name,server.port config.yaml
  config_manager convert config.ini config.yaml
  config_manager list config.yaml
  config_manager env MYAPP_ --format=json
        """
    )
    
    # Global arguments
    parser.add_argument('--verbose', '-v', action='count', default=0,
                      help='Increase verbosity (can be used multiple times)')
    parser.add_argument('--format', choices=['yaml', 'json', 'ini'], 
                      help='Specify output format')
    
    # Create subparsers for commands
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # 'get' command
    get_parser = subparsers.add_parser('get', help='Get configuration values')
    get_parser.add_argument('config_file', help='Path to the configuration file')
    get_parser.add_argument('key', nargs='?', default=None, 
                        help='Dot notation key to retrieve (e.g., app.debug)')
    get_parser.add_argument('--default', help='Default value if key not found')
    get_parser.add_argument('--format', choices=['yaml', 'json', 'ini'], 
                        help='Specify output format')  # Add format option to get subparser
                        
    # 'set' command
    set_parser = subparsers.add_parser('set', help='Set configuration values')
    set_parser.add_argument('config_file', help='Path to the configuration file')
    set_parser.add_argument('key', help='Dot notation key to set (e.g., app.debug)')
    set_parser.add_argument('value', help='Value to set')
    set_parser.add_argument('--create', action='store_true', 
                          help='Create file if it does not exist')
    
    # 'create' command
    create_parser = subparsers.add_parser('create', help='Create a new configuration file')
    create_parser.add_argument('output_file', help='Path to save the new configuration file')
    create_parser.add_argument('--template', help='Path to a template configuration file')
    create_parser.add_argument('--vars', help='JSON string of variables to set')
    
    # 'validate' command
    validate_parser = subparsers.add_parser('validate', help='Validate a configuration file')
    validate_parser.add_argument('config_file', help='Path to the configuration file')
    validate_parser.add_argument('--required', help='Comma-separated list of required keys')
    
    # 'convert' command
    convert_parser = subparsers.add_parser('convert', help='Convert configuration between formats')
    convert_parser.add_argument('input_file', help='Path to the input configuration file')
    convert_parser.add_argument('output_file', help='Path to save the converted configuration file')
    
    # 'list' command
    list_parser = subparsers.add_parser('list', help='List all configuration values')
    list_parser.add_argument('config_file', help='Path to the configuration file')
    list_parser.add_argument('--section', help='List only values in this section')
    
    # 'env' command
    env_parser = subparsers.add_parser('env', help='Get configuration from environment variables')
    env_parser.add_argument('prefix', help='Environment variable prefix (e.g., APP_)')
    
    return parser

def setup_logging(verbosity: int) -> None:
    """
    Set up logging based on verbosity level.
    
    Args:
        verbosity: Verbosity level (0=WARNING, 1=INFO, 2+=DEBUG)
    """
    log_level = logging.WARNING
    if verbosity == 1:
        log_level = logging.INFO
    elif verbosity >= 2:
        log_level = logging.DEBUG
        
    logging.basicConfig(
        level=log_level,
        format='%(levelname)s: %(message)s'
    )
def format_output(data: Any, format_type: Optional[str] = None) -> str:
    """
    Format data for output based on the specified format.
    
    Args:
        data: Data to format
        format_type: Output format (yaml, json, or None for default)
        
    Returns:
        Formatted string representation of the data
    """
    # First, convert SimpleNamespace to dict if needed
    from types import SimpleNamespace
    if isinstance(data, SimpleNamespace):
        from config_manager.dot_notation import namespace_to_dict
        data = namespace_to_dict(data)
    
    if format_type == 'yaml':
        import yaml
        return yaml.dump(data, default_flow_style=False)
    elif format_type == 'json':
        return json.dumps(data, indent=2)
    elif format_type == 'ini' and isinstance(data, dict):
        import configparser
        parser = configparser.ConfigParser()
        
        # Add sections and values
        for section, values in data.items():
            if not isinstance(values, dict):
                continue
                
            parser.add_section(section)
            for key, value in values.items():
                if not isinstance(value, (dict, list)):
                    parser.set(section, key, str(value))
        
        # Write to string
        from io import StringIO
        output = StringIO()
        parser.write(output)
        return output.getvalue()
    else:
        # Default pretty print
        if isinstance(data, dict):
            return _format_dict(data)
        else:
            return str(data)

def _format_dict(data: Dict, indent: int = 0) -> str:
    """
    Format a dictionary for pretty printing.
    
    Args:
        data: Dictionary to format
        indent: Current indentation level
        
    Returns:
        Formatted string representation of the dictionary
    """
    from types import SimpleNamespace
    
    lines = []
    if isinstance(data, SimpleNamespace):
        # Convert SimpleNamespace to dict first
        data = vars(data)
        
    for key, value in data.items():
        if isinstance(value, dict) or isinstance(value, SimpleNamespace):
            lines.append(' ' * indent + f"{key}:")
            if isinstance(value, SimpleNamespace):
                value_dict = vars(value)
                lines.append(_format_dict(value_dict, indent + 2))
            else:
                lines.append(_format_dict(value, indent + 2))
        else:
            lines.append(' ' * indent + f"{key}: {value}")
    return '\n'.join(lines)

def convert_value(value: str) -> Any:
    """
    Convert string value to appropriate type.
    
    Args:
        value: String value to convert
        
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

def cmd_get(args: argparse.Namespace) -> int:
    """
    Handle the 'get' command.
    
    Args:
        args: Command line arguments
        
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        config = Config(config_path=args.config_file)
        
        if args.key:
            # Get a specific key
            value = config.get(args.key, args.default)
            if value is None and args.default is not None:
                value = convert_value(args.default)
                
            if value is None:
                print(f"Key '{args.key}' not found in configuration")
                return 1
        else:
            # Get entire config
            value = config.get_config()
        
        # Convert SimpleNamespace to dict for formatting
        from types import SimpleNamespace
        if isinstance(value, SimpleNamespace):
            import config_manager.dot_notation as dn
            value = dn.namespace_to_dict(value)
            
        print(format_output(value, args.format))
        return 0
        
    except ConfigError as e:
        logging.error(f"Error: {e}")
        return 1

def cmd_set(args: argparse.Namespace) -> int:
    """
    Handle the 'set' command.
    
    Args:
        args: Command line arguments
        
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        # Check if file exists
        if not os.path.exists(args.config_file) and not args.create:
            logging.error(f"Config file {args.config_file} does not exist. "
                         f"Use --create to create a new file.")
            return 1
            
        # Create empty config if file doesn't exist
        if not os.path.exists(args.config_file) and args.create:
            config = Config()
        else:
            config = Config(config_path=args.config_file)
            
        # Convert and set the value
        converted_value = convert_value(args.value)
        config.set(args.key, converted_value)
        
        # Save the config
        config.save(args.config_file)
        logging.info(f"Updated {args.key} = {converted_value} in {args.config_file}")
        return 0
        
    except ConfigError as e:
        logging.error(f"Error: {e}")
        return 1

def cmd_create(args: argparse.Namespace) -> int:
    """
    Handle the 'create' command.
    
    Args:
        args: Command line arguments
        
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        # Start with empty config or template
        if args.template:
            config = Config(config_path=args.template)
        else:
            config = Config()
            
        # Apply variables if provided
        if args.vars:
            try:
                variables = json.loads(args.vars)
                for key, value in variables.items():
                    config.set(key, value)
            except json.JSONDecodeError:
                logging.error("Invalid JSON in --vars parameter")
                return 1
                
        # Determine format from file extension if not specified
        format = args.format
        if not format:
            ext = os.path.splitext(args.output_file)[1].lower()
            if ext in ['.yml', '.yaml']:
                format = 'yaml'
            elif ext == '.json':
                format = 'json'
            elif ext in ['.ini', '.conf']:
                format = 'ini'
                
        # Save with the determined format
        config._format = format
        config.save(args.output_file)
        logging.info(f"Created new configuration file: {args.output_file}")
        return 0
        
    except ConfigError as e:
        logging.error(f"Error: {e}")
        return 1

def cmd_validate(args: argparse.Namespace) -> int:
    """
    Handle the 'validate' command.
    
    Args:
        args: Command line arguments
        
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        required_keys = []
        if args.required:
            required_keys = args.required.split(',')
            
        config = Config(config_path=args.config_file, 
                       required_keys=required_keys)
        
        # If we get here, validation passed
        logging.info(f"Configuration file {args.config_file} is valid")
        if required_keys:
            logging.info(f"All required keys present: {', '.join(required_keys)}")
            
        return 0
        
    except ConfigError as e:
        # Print to stderr as well as logging
        print(f"Validation error: {e}", file=sys.stderr)
        logging.error(f"Validation error: {e}")
        return 1

def cmd_convert(args: argparse.Namespace) -> int:
    """
    Handle the 'convert' command.
    
    Args:
        args: Command line arguments
        
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        # Load the input file
        config = Config(config_path=args.input_file)
        
        # Determine output format from extension if not specified
        format = args.format
        if not format:
            ext = os.path.splitext(args.output_file)[1].lower()
            if ext in ['.yml', '.yaml']:
                format = 'yaml'
            elif ext == '.json':
                format = 'json'
            elif ext in ['.ini', '.conf']:
                format = 'ini'
                
        # Save with the determined format
        config._format = format
        config.save(args.output_file)
        logging.info(f"Converted {args.input_file} to {args.output_file}")
        return 0
        
    except ConfigError as e:
        logging.error(f"Error: {e}")
        return 1

def cmd_list(args: argparse.Namespace) -> int:
    """
    Handle the 'list' command.
    
    Args:
        args: Command line arguments
        
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        config = Config(config_path=args.config_file)
        
        if args.section:
            # List items in a specific section
            items = config.get_section_items(args.section)
            if not items:
                logging.warning(f"Section '{args.section}' not found or empty")
                return 1
                
            # Format the items
            if args.format:
                data = {args.section: dict(items)}
                print(format_output(data, args.format))
            else:
                print(f"{args.section}:")
                for key, value in items:
                    print(f"  {key}: {value}")
        else:
            # List all configuration
            data = config.get_config()
            print(format_output(data, args.format))
            
        return 0
        
    except ConfigError as e:
        logging.error(f"Error: {e}")
        return 1

def cmd_env(args: argparse.Namespace) -> int:
    """
    Handle the 'env' command.
    
    Args:
        args: Command line arguments
        
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        # Create config from environment variables
        config = Config.from_env(args.prefix)
        
        # Get and format the config
        data = config.get_config()
        print(format_output(data, args.format))
        return 0
        
    except ConfigError as e:
        logging.error(f"Error: {e}")
        return 1

def main() -> int:
    """
    Main entry point for the CLI.
    
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    parser = setup_parser()
    args = parser.parse_args()
    
    # Set up logging based on verbosity
    setup_logging(args.verbose)
    
    # Execute the requested command
    if args.command == 'get':
        return cmd_get(args)
    elif args.command == 'set':
        return cmd_set(args)
    elif args.command == 'create':
        return cmd_create(args)
    elif args.command == 'validate':
        return cmd_validate(args)
    elif args.command == 'convert':
        return cmd_convert(args)
    elif args.command == 'list':
        return cmd_list(args)
    elif args.command == 'env':
        return cmd_env(args)
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    sys.exit(main())
