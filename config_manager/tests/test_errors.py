import os
import sys
import pytest

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config_manager.errors import ConfigError, ConfigFileError, ConfigFormatError, ConfigValidationError


class TestErrors:
    """Test the custom error classes"""
    
    def test_config_error_base(self):
        """Test the base ConfigError class"""
        # Simple error
        error = ConfigError("Test error message")
        assert str(error) == "Test error message"
        assert error.message == "Test error message"
        assert error.details == {}
        
        # Error with details
        details = {"key": "value", "code": 42}
        error = ConfigError("Error with details", details)
        assert "Error with details" in str(error)
        assert "key=value" in str(error)
        assert "code=42" in str(error)
        assert error.get_details() == details
    
    def test_config_file_error(self):
        """Test the ConfigFileError class"""
        # Simple file error
        error = ConfigFileError("File error")
        assert str(error) == "File error"
        
        # Error with file path
        error = ConfigFileError("Cannot read file", "/path/to/file")
        assert "Cannot read file" in str(error)
        assert "file_path=/path/to/file" in str(error)
        assert error.file_path == "/path/to/file"
        
        # Error with file path and additional details
        details = {"permission": "denied"}
        error = ConfigFileError("Access error", "/path/to/file", details)
        assert "Access error" in str(error)
        assert "file_path=/path/to/file" in str(error)
        assert "permission=denied" in str(error)
    
    def test_config_format_error(self):
        """Test the ConfigFormatError class"""
        # Simple format error
        error = ConfigFormatError("Invalid format")
        assert str(error) == "Invalid format"
        
        # Error with format type
        error = ConfigFormatError("Invalid YAML syntax", "yaml")
        assert "Invalid YAML syntax" in str(error)
        assert "format_type=yaml" in str(error)
        assert error.format_type == "yaml"
        
        # Error with format type and additional details
        details = {"line": 42}
        error = ConfigFormatError("Parsing error", "json", details)
        assert "Parsing error" in str(error)
        assert "format_type=json" in str(error)
        assert "line=42" in str(error)
    
    def test_config_validation_error(self):
        """Test the ConfigValidationError class"""
        # Simple validation error
        error = ConfigValidationError("Validation failed")
        assert str(error) == "Validation failed"
        assert error.missing_keys == []
        assert error.invalid_values == {}
        
        # Error with missing keys
        missing = ["app.name", "server.host"]
        error = ConfigValidationError("Missing required keys", missing)
        assert "Missing required keys" in str(error)
        assert "missing_keys=['app.name', 'server.host']" in str(error)
        assert error.get_missing_keys() == missing
        
        # Error with invalid values
        invalid = {"server.port": "not_a_number", "timeout": "invalid"}
        error = ConfigValidationError("Invalid values", None, invalid)
        assert "Invalid values" in str(error)
        assert "invalid_values=" in str(error)
        assert error.get_invalid_values() == invalid
        
        # Error with both missing keys and invalid values
        missing = ["required_key"]
        invalid = {"port": "invalid"}
        error = ConfigValidationError("Multiple errors", missing, invalid)
        assert "Multiple errors" in str(error)
        assert "missing_keys=['required_key']" in str(error)
        assert "invalid_values=" in str(error)
        assert error.get_missing_keys() == missing
        assert error.get_invalid_values() == invalid
