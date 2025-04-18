import os
import sys
import pytest
import tempfile
import shutil
import yaml
import json
import logging
from pathlib import Path

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config_manager import Config, config_manager, setup_file_logging
from config_manager.errors import ConfigError, ConfigFileError, ConfigValidationError


class TestIntegration:
    """Integration tests for the config_manager package"""
    
    def test_full_workflow(self, temp_dir, sample_config):
        """Test a complete workflow of loading, modifying, and saving config"""
        # Create test config files
        yaml_path = os.path.join(temp_dir, 'config.yaml')
        with open(yaml_path, 'w') as f:
            yaml.dump(sample_config, f)
            
        # Test environment variables
        os.environ['MYAPP_SERVER__HOST'] = '0.0.0.0'
        os.environ['MYAPP_NEW_SECTION__KEY'] = 'value'
        
        try:
            # 1. Load configuration with defaults and env vars
            default_config = {
                'app': {
                    'name': 'DefaultApp',
                    'debug': False
                },
                'logging': {
                    'level': 'INFO'
                }
            }
            
            config = config_manager(
                config_path=yaml_path,
                default_config=default_config,
                env_prefix='MYAPP_',
                required_keys=['app.name', 'server.host']
            )
            
            # 2. Verify merged configuration
            # From file
            assert config.app.version == '1.0.0'
            assert config.database.url == 'sqlite:///test.db'
            
            # From defaults
            assert config.logging.level == 'INFO'
            
            # From environment variables
            assert config.server.host == '0.0.0.0'  # Overridden by env
            assert config.new_section.key == 'value'  # Added by env
            
            # 3. Modify configuration
            config.set('app.version', '2.0.0')
            config.set('features.enabled', ['feature1', 'feature2'])
            
            # 4. Check modifications
            assert config.app.version == '2.0.0'
            assert config.features.enabled == ['feature1', 'feature2']
            
            # 5. Save to a new file
            json_path = os.path.join(temp_dir, 'modified_config.json')
            config._format = 'json'  # Force JSON format
            config.save(json_path)
            
            # 6. Load the saved file and verify
            new_config = Config(config_path=json_path)
            assert new_config.app.version == '2.0.0'
            assert new_config.features.enabled == ['feature1', 'feature2']
            assert new_config.app.name == 'TestApp'
            assert new_config.server.host == '0.0.0.0'
            
            # 7. Convert to another format
            ini_path = os.path.join(temp_dir, 'config.ini')
            new_config._format = 'ini'
            new_config.save(ini_path)
            
            # 8. Reload and verify
            # First save back to the original yaml file
            config._format = 'yaml'  # Set to yaml format
            config.save(yaml_path)  # Save back to the original file
            config.reload()  # Now reload the updated file
            assert config.app.version == '2.0.0'  # Should have updated value
            
        finally:
            # Clean up environment variables
            for key in ['MYAPP_SERVER__HOST', 'MYAPP_NEW_SECTION__KEY']:
                if key in os.environ:
                    del os.environ[key]
    
    def test_error_handling_workflow(self, temp_dir):
        """Test error handling in a realistic workflow"""
        # 1. Missing file
        nonexistent_path = os.path.join(temp_dir, 'nonexistent.yaml')
        
        with pytest.raises(ConfigFileError):
            Config(config_path=nonexistent_path)
        
        # 2. Create a file with invalid content
        invalid_path = os.path.join(temp_dir, 'invalid.yaml')
        with open(invalid_path, 'w') as f:
            f.write('invalid: yaml: :\n  - missing" quote\n')
        
        with pytest.raises(ConfigFileError):
            Config(config_path=invalid_path)
        
        # 3. Missing required keys
        valid_path = os.path.join(temp_dir, 'valid.yaml')
        with open(valid_path, 'w') as f:
            yaml.dump({'app': {'version': '1.0.0'}}, f)
        
        with pytest.raises(ConfigValidationError) as exc_info:
            Config(
                config_path=valid_path,
                required_keys=['app.name', 'server.host']
            )
        
        # 4. Verify the error contains useful information
        assert 'app.name' in str(exc_info.value)
        assert 'server.host' in str(exc_info.value)
        
        # 5. Test recovering with default values
        config = Config(
            config_path=valid_path,
            default_config={
                'app': {
                    'name': 'DefaultApp'
                },
                'server': {
                    'host': '127.0.0.1'
                }
            },
            required_keys=['app.name', 'server.host']
        )
        
        # Should not raise an error now
        assert config.app.name == 'DefaultApp'
        assert config.server.host == '127.0.0.1'
    
    def test_logging_integration(self, temp_dir):
        """Test integration with logging module"""
        log_file = os.path.join(temp_dir, 'config.log')
        
        # Configure file logging
        setup_file_logging(
            log_dir=temp_dir,
            app_name='test_app',
            log_level=logging.DEBUG
        )
        
        # Perform some operations that generate log messages
        config = Config(
            default_config={'app': {'name': 'LogTest'}},
            log_level=logging.DEBUG
        )
        
        config.set('new.key', 'value')
        
        # Use a temp file path that doesn't exist to trigger errors
        nonexistent = os.path.join(temp_dir, 'nonexistent', 'config.yaml')
        
        try:
            Config(config_path=nonexistent)
        except ConfigFileError:
            pass
        
        # Check that log files were created
        log_path = os.path.join(temp_dir, 'test_app', 'config_manager.log')
        assert os.path.exists(log_path)
        
        # Verify log content
        with open(log_path, 'r') as f:
            log_content = f.read()
            assert 'config_manager' in log_content
            assert 'DEBUG' in log_content or 'INFO' in log_content
