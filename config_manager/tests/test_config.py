import os
import sys
import pytest
import tempfile
import json
import yaml
import shutil
from pathlib import Path

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config_manager import Config, config_manager, ConfigError, ConfigFileError, ConfigValidationError


class TestConfig:
    """Test the Config class"""

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
            },
            'database': {
                'url': 'sqlite:///test.db',
                'pool_size': 5
            }
        }
        
        # Create temporary config files
        self.yaml_path = os.path.join(self.temp_dir, 'config.yaml')
        with open(self.yaml_path, 'w') as f:
            yaml.dump(self.sample_config, f)
            
        self.json_path = os.path.join(self.temp_dir, 'config.json')
        with open(self.json_path, 'w') as f:
            json.dump(self.sample_config, f)
            
        # Create INI file
        self.ini_path = os.path.join(self.temp_dir, 'config.ini')
        with open(self.ini_path, 'w') as f:
            f.write("[app]\n")
            f.write("name = TestApp\n")
            f.write("version = 1.0.0\n")
            f.write("debug = true\n")
            f.write("\n")
            f.write("[server]\n")
            f.write("host = 127.0.0.1\n")
            f.write("port = 8000\n")
            f.write("timeout = 30\n")
            f.write("\n")
            f.write("[database]\n")
            f.write("url = sqlite:///test.db\n")
            f.write("pool_size = 5\n")
    
    def teardown_method(self):
        """Tear down test fixtures"""
        shutil.rmtree(self.temp_dir)
    
    def test_load_yaml_config(self):
        """Test loading a YAML configuration file"""
        config = Config(config_path=self.yaml_path)
        assert config.app.name == 'TestApp'
        assert config.server.port == 8000
        assert config.database.url == 'sqlite:///test.db'
    
    def test_load_json_config(self):
        """Test loading a JSON configuration file"""
        config = Config(config_path=self.json_path)
        assert config.app.name == 'TestApp'
        assert config.server.port == 8000
        assert config.database.url == 'sqlite:///test.db'
    
    def test_load_ini_config(self):
        """Test loading an INI configuration file"""
        config = Config(config_path=self.ini_path)
        assert config.app.name == 'TestApp'
        assert config.server.port == '8000'  # INI values are strings
        assert config.database.url == 'sqlite:///test.db'
    
    def test_default_config(self):
        """Test using a default configuration"""
        default_config = {
            'app': {
                'name': 'DefaultApp',
                'version': '0.1.0',
                'debug': False
            },
            'logging': {
                'level': 'INFO'
            }
        }
        
        # Load with both default and file
        config = Config(config_path=self.yaml_path, default_config=default_config)
        
        # File values should override defaults
        assert config.app.name == 'TestApp'
        assert config.app.debug is True
        
        # Values only in default should be present
        assert config.logging.level == 'INFO'
        
        # Values only in file should be present
        assert config.server.port == 8000
    
    def test_config_manager_function(self):
        """Test the config_manager function"""
        config = config_manager(self.yaml_path)
        assert config.app.name == 'TestApp'
        assert config.server.port == 8000
    
    def test_get_config(self):
        """Test getting the entire configuration as a dict"""
        config = Config(config_path=self.yaml_path)
        config_dict = config.get_config()
        
        assert config_dict['app']['name'] == 'TestApp'
        assert config_dict['server']['port'] == 8000
        assert config_dict['database']['url'] == 'sqlite:///test.db'
    
    def test_get_method(self):
        """Test the get method for accessing values"""
        config = Config(config_path=self.yaml_path)
        
        # Get with dot notation
        assert config.get('app.name') == 'TestApp'
        assert config.get('server.port') == 8000
        
        # Get with default
        assert config.get('missing.key', 'default') == 'default'
        
        # Get entire config
        full_config = config.get()
        assert full_config['app']['name'] == 'TestApp'
    
    def test_set_method(self):
        """Test setting configuration values"""
        config = Config(config_path=self.yaml_path)
        
        # Set a simple value
        config.set('app.name', 'NewName')
        assert config.app.name == 'NewName'
        
        # Set a nested value that doesn't exist
        config.set('new.nested.value', 42)
        assert config.new.nested.value == 42
    
    def test_update_method(self):
        """Test updating multiple configuration values"""
        config = Config(config_path=self.yaml_path)
        
        updates = {
            'app': {
                'name': 'UpdatedApp',
                'debug': False
            },
            'new_section': {
                'key': 'value'
            }
        }
        
        config.update(updates)
        assert config.app.name == 'UpdatedApp'
        assert config.app.debug is False
        assert config.new_section.key == 'value'
        
        # Original values not in update should remain
        assert config.app.version == '1.0.0'
    
    def test_items_method(self):
        """Test the items method"""
        config = Config(config_path=self.yaml_path)
        
        # Top-level items
        top_items = dict(config.items())
        assert 'app' in top_items
        assert 'server' in top_items
        
        # Section items
        server_items = dict(config.items('server'))
        assert server_items['host'] == '127.0.0.1'
        assert server_items['port'] == 8000
    
    def test_save_method(self):
        """Test saving configuration to a file"""
        config = Config(config_path=self.yaml_path)
        
        # Modify the configuration
        config.set('app.name', 'SavedApp')
        config.set('new_section.key', 'value')
        
        # Save to a new file
        new_path = os.path.join(self.temp_dir, 'saved_config.yaml')
        config.save(new_path)
        
        # Load the saved file and check values
        new_config = Config(config_path=new_path)
        assert new_config.app.name == 'SavedApp'
        assert new_config.new_section.key == 'value'
    
    def test_from_dict_classmethod(self):
        """Test creating a Config from a dictionary"""
        config = Config.from_dict(self.sample_config)
        
        assert config.app.name == 'TestApp'
        assert config.server.port == 8000
        assert config.database.url == 'sqlite:///test.db'
    
    def test_from_env_classmethod(self):
        """Test creating a Config from environment variables"""
        # Set environment variables
        os.environ['TEST_APP__NAME'] = 'EnvApp'
        os.environ['TEST_SERVER__PORT'] = '9000'
        os.environ['TEST_DATABASE__URL'] = 'sqlite:///env.db'
        
        try:
            config = Config.from_env('TEST_')
            
            assert config.app.name == 'EnvApp'
            assert config.server.port == 9000  # Should be converted to int
            assert config.database.url == 'sqlite:///env.db'
        finally:
            # Clean up environment
            del os.environ['TEST_APP__NAME']
            del os.environ['TEST_SERVER__PORT']
            del os.environ['TEST_DATABASE__URL']
    
    def test_env_override(self):
        """Test environment variables overriding file values"""
        # Set environment variables
        os.environ['TEST_APP__NAME'] = 'EnvOverride'
        os.environ['TEST_SERVER__PORT'] = '9000'
        
        try:
            config = Config(
                config_path=self.yaml_path,
                env_prefix='TEST_'
            )
            
            # Environment should override file
            assert config.app.name == 'EnvOverride'
            assert config.server.port == 9000
            
            # File values not in env should remain
            assert config.app.version == '1.0.0'
            assert config.database.url == 'sqlite:///test.db'
        finally:
            # Clean up environment
            del os.environ['TEST_APP__NAME']
            del os.environ['TEST_SERVER__PORT']
    
    def test_required_keys(self):
        """Test validation of required keys"""
        # All required keys present
        config = Config(
            config_path=self.yaml_path,
            required_keys=['app.name', 'server.host', 'server.port']
        )
        
        # Should not raise an exception
        assert config.app.name == 'TestApp'
        
        # Missing required key
        with pytest.raises(ConfigValidationError):
            Config(
                config_path=self.yaml_path,
                required_keys=['app.name', 'missing.key']
            )
    
    def test_find_config_file(self):
        """Test finding a config file in search paths"""
        search_paths = [
            os.path.join(self.temp_dir, 'nonexistent'),
            self.temp_dir
        ]
        
        config = Config(search_paths=search_paths)
        
        # Should find and load one of the config files
        assert hasattr(config, 'app')
        assert hasattr(config, 'server')
    
    def test_reload_method(self):
        """Test reloading configuration from file"""
        config = Config(config_path=self.yaml_path)
        
        # Modify the config file
        modified_config = self.sample_config.copy()
        modified_config['app']['name'] = 'ReloadedApp'
        
        with open(self.yaml_path, 'w') as f:
            yaml.dump(modified_config, f)
        
        # Reload the configuration
        config.reload()
        
        # Should have the updated value
        assert config.app.name == 'ReloadedApp'
    
    def test_file_not_found(self):
        """Test handling of file not found errors"""
        nonexistent_path = os.path.join(self.temp_dir, 'nonexistent.yaml')
        
        with pytest.raises(ConfigFileError):
            Config(config_path=nonexistent_path)
    
    def test_invalid_format(self):
        """Test handling of invalid format errors"""
        # Create an invalid YAML file
        invalid_path = os.path.join(self.temp_dir, 'invalid.yaml')
        with open(invalid_path, 'w') as f:
            f.write('invalid: yaml: content:\n  - missing" quote\n')
        
        with pytest.raises(ConfigFileError):
            Config(config_path=invalid_path)
