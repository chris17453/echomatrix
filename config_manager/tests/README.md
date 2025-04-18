## Testing

Config Manager comes with comprehensive unit tests to ensure reliability. To run the tests:

```bash
# Install test dependencies
pip install pytest

# Run all tests
pytest

# Run specific test files
pytest tests/test_config.py
pytest tests/test_cli.py
pytest tests/test_integration.py::TestIntegration::test_full_workflow

# Run with coverage report
pip install pytest-cov
pytest --cov=config_manager
```


### Test Structure

- `test_config.py`: Tests for the main `Config` class functionality
- `test_dot_notation.py`: Tests for the dot notation utilities
- `test_errors.py`: Tests for custom exception classes
- `test_cli.py`: Tests for the command-line interface
- `conftest.py`: Shared pytest fixtures

### Writing New Tests

When adding new features, please add corresponding tests. For example, to test a new method in the `Config` class:

```python
def test_my_new_feature(self):
    """Test the my_new_feature method"""
    config = Config(config_path=self.yaml_path)
    result = config.my_new_feature('param')
    assert result == expected_value
```

The test suite uses pytest fixtures to set up test environments and sample data, making it easy to write focused tests without repetitive setup code.
