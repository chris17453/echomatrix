import pytest
import os
import sys
import tempfile
import shutil
import yaml
import json

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    dir_path = tempfile.mkdtemp()
    yield dir_path
    shutil.rmtree(dir_path)


@pytest.fixture
def sample_config():
    """Provide a sample configuration dictionary"""
    return {
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


@pytest.fixture
def config_yaml_path(temp_dir, sample_config):
    """Create a YAML config file for testing"""
    yaml_path = os.path.join(temp_dir, 'config.yaml')
    with open(yaml_path, 'w') as f:
        yaml.dump(sample_config, f)
    return yaml_path


@pytest.fixture
def config_json_path(temp_dir, sample_config):
    """Create a JSON config file for testing"""
    json_path = os.path.join(temp_dir, 'config.json')
    with open(json_path, 'w') as f:
        json.dump(sample_config, f)
    return json_path


@pytest.fixture
def config_ini_path(temp_dir, sample_config):
    """Create an INI config file for testing"""
    ini_path = os.path.join(temp_dir, 'config.ini')
    with open(ini_path, 'w') as f:
        for section, values in sample_config.items():
            f.write(f"[{section}]\n")
            for key, value in values.items():
                f.write(f"{key} = {value}\n")
            f.write("\n")
    return ini_path


@pytest.fixture
def env_vars():
    """Set and clean up environment variables for testing"""
    # Store original environment
    original_env = os.environ.copy()
    
    # Set test environment variables
    os.environ['TEST_APP__NAME'] = 'EnvApp'
    os.environ['TEST_SERVER__PORT'] = '9000'
    os.environ['TEST_DATABASE__URL'] = 'sqlite:///env.db'
    
    yield
    
    # Restore original environment
    for key in ['TEST_APP__NAME', 'TEST_SERVER__PORT', 'TEST_DATABASE__URL']:
        if key in os.environ:
            del os.environ[key]

