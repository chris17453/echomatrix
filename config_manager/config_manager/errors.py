class ConfigError(Exception):
    """Base exception for configuration errors"""
    
    def __init__(self, message="A configuration error occurred", details=None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self):
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} - {details_str}"
        return self.message
    
    def get_details(self):
        """Return a dictionary with error details"""
        return self.details


class ConfigFileError(ConfigError):
    """Exception for errors related to config files"""
    
    def __init__(self, message="Error accessing configuration file", file_path=None, details=None):
        self.file_path = file_path
        _details = details or {}
        if file_path:
            _details["file_path"] = file_path
        super().__init__(message, _details)


class ConfigFormatError(ConfigError):
    """Exception for errors related to config format"""
    
    def __init__(self, message="Invalid configuration format", format_type=None, details=None):
        self.format_type = format_type
        _details = details or {}
        if format_type:
            _details["format_type"] = format_type
        super().__init__(message, _details)


class ConfigValidationError(ConfigError):
    """Exception for errors related to config validation"""
    
    def __init__(self, message="Configuration validation failed", missing_keys=None, invalid_values=None, details=None):
        self.missing_keys = missing_keys or []
        self.invalid_values = invalid_values or {}
        _details = details or {}
        
        if missing_keys:
            _details["missing_keys"] = missing_keys
        if invalid_values:
            _details["invalid_values"] = invalid_values
            
        super().__init__(message, _details)
    
    def get_missing_keys(self):
        """Return a list of missing required keys"""
        return self.missing_keys
    
    def get_invalid_values(self):
        """Return a dictionary of keys with invalid values"""
        return self.invalid_values