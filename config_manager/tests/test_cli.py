import os
import sys
import pytest
import tempfile
import shutil
import yaml
import json
import subprocess
from pathlib import Path

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config_manager.cli import main, setup_parser, cmd_get, cmd_set, cmd_create, cmd_validate


class TestCLI:
    """Test the command-line interface"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Sample configuration for testing
        self.sample_config = {
            'app': {
                'name': 'TestApp',
                'version': '1.0.0',
                'debug': True
            },
            'server': {
                'host': '127.0.0.1',
                'port': 8000,
                'timeout': 30
            }
        }
        
        # Create temporary config file
        self.yaml_path = os.path.join(self.temp_dir, 'config.yaml')
        with open(self.yaml_path, 'w') as f:
            yaml.dump(self.sample_config, f)
    
    def teardown_method(self):
        """Tear down test fixtures"""
        shutil.rmtree(self.temp_dir)
    
    def run_cli(self, args):
        """
        Run the CLI with given arguments
        
        Args:
            args: List of CLI arguments
            
        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        # Save original stdout and stderr
        old_stdout, old_stderr = sys.stdout, sys.stderr
        from io import StringIO
        sys.stdout = stdout = StringIO()
        sys.stderr = stderr = StringIO()        

        exit_code = 0
        try:
            # Run the CLI
            parser = setup_parser()
            parsed_args = parser.parse_args(args)
            
            # Execute the command
            if parsed_args.command == 'get':
                exit_code = cmd_get(parsed_args)
            elif parsed_args.command == 'set':
                exit_code = cmd_set(parsed_args)
            elif parsed_args.command == 'create':
                exit_code = cmd_create(parsed_args)
            elif parsed_args.command == 'validate':
                exit_code = cmd_validate(parsed_args)
            else:
                exit_code = 1
        except SystemExit as e:
            exit_code = e.code
        except Exception as e:
            print(f"Error: {e}", file=stderr)
            exit_code = 1
        finally:
            # Restore stdout and stderr
            sys.stdout, sys.stderr = old_stdout, old_stderr
        
        return exit_code, stdout.getvalue(), stderr.getvalue()
    
    def test_get_command(self):
        """Test the 'get' command"""
        # Get a specific value
        exit_code, stdout, stderr = self.run_cli(['get', self.yaml_path, 'app.name'])
        assert exit_code == 0
        assert stdout.strip() == 'TestApp'
        
        # Get a section
        exit_code, stdout, stderr = self.run_cli(['get', self.yaml_path, 'server'])
        assert exit_code == 0
        assert 'host: 127.0.0.1' in stdout
        assert 'port: 8000' in stdout
        
        # Get with JSON format
        # Move the format flag to the correct position
        exit_code, stdout, stderr = self.run_cli(['get', self.yaml_path, 'app', '--format', 'json'])
        assert exit_code == 0
        app_data = json.loads(stdout)
        assert app_data['name'] == 'TestApp'
        assert app_data['version'] == '1.0.0'
                
    def test_set_command(self):
        """Test the 'set' command"""
        # Set an existing value
        exit_code, stdout, stderr = self.run_cli(['set', self.yaml_path, 'app.name', 'NewName'])
        assert exit_code == 0
        
        # Verify the change
        exit_code, stdout, stderr = self.run_cli(['get', self.yaml_path, 'app.name'])
        assert stdout.strip() == 'NewName'
        
        # Set a new nested value
        exit_code, stdout, stderr = self.run_cli(['set', self.yaml_path, 'new.nested.value', '42'])
        assert exit_code == 0
        
        # Verify the new value
        exit_code, stdout, stderr = self.run_cli(['get', self.yaml_path, 'new.nested.value'])
        assert stdout.strip() == '42'
        
        # Set a boolean value
        exit_code, stdout, stderr = self.run_cli(['set', self.yaml_path, 'app.debug', 'false'])
        assert exit_code == 0
        
        # Verify the boolean value
        exit_code, stdout, stderr = self.run_cli(['get', self.yaml_path, 'app.debug'])
        assert stdout.strip() == 'False'
    
    def test_create_command(self):
        """Test the 'create' command"""
        # Create a new file
        new_path = os.path.join(self.temp_dir, 'new_config.yaml')
        exit_code, stdout, stderr = self.run_cli(['create', new_path, '--vars', '{"app.name":"NewApp","server.port":9000}'])
        assert exit_code == 0
        
        # Verify the file was created
        assert os.path.exists(new_path)
        
        # Check the content
        exit_code, stdout, stderr = self.run_cli(['get', new_path, 'app.name'])
        assert stdout.strip() == 'NewApp'
        
        exit_code, stdout, stderr = self.run_cli(['get', new_path, 'server.port'])
        assert stdout.strip() == '9000'
    
    def test_validate_command(self):
        """Test the 'validate' command"""
        # Validate with all required keys present
        exit_code, stdout, stderr = self.run_cli(['validate', self.yaml_path, '--required', 'app.name,server.port'])
        assert exit_code == 0
        
        # Validate with missing required key
        exit_code, stdout, stderr = self.run_cli(['validate', self.yaml_path, '--required', 'app.name,missing.key'])
        assert exit_code == 1
        assert "Validation error" in stderr
