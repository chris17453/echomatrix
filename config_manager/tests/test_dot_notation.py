import os
import sys
import pytest
from types import SimpleNamespace

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config_manager.dot_notation import dict_to_namespace, namespace_to_dict, deep_merge


class TestDotNotation:
    """Test the dot notation utilities"""
    
    def test_dict_to_namespace(self):
        """Test converting a dictionary to a namespace"""
        data = {
            'simple': 'value',
            'number': 42,
            'boolean': True,
            'nested': {
                'key': 'nested_value',
                'list': [1, 2, 3]
            },
            'list_of_dicts': [
                {'name': 'item1'},
                {'name': 'item2'}
            ]
        }
        
        # Convert to namespace
        ns = dict_to_namespace(data)
        
        # Simple values
        assert ns.simple == 'value'
        assert ns.number == 42
        assert ns.boolean is True
        
        # Nested namespace
        assert isinstance(ns.nested, SimpleNamespace)
        assert ns.nested.key == 'nested_value'
        assert ns.nested.list == [1, 2, 3]
        
        # List of dicts should be converted to list of namespaces
        assert isinstance(ns.list_of_dicts[0], SimpleNamespace)
        assert ns.list_of_dicts[0].name == 'item1'
        assert ns.list_of_dicts[1].name == 'item2'
    
    def test_namespace_to_dict(self):
        """Test converting a namespace back to a dictionary"""
        # Create a namespace
        ns = SimpleNamespace()
        ns.simple = 'value'
        ns.number = 42
        ns.boolean = True
        
        ns.nested = SimpleNamespace()
        ns.nested.key = 'nested_value'
        ns.nested.list = [1, 2, 3]
        
        ns.list_of_ns = [
            SimpleNamespace(name='item1'),
            SimpleNamespace(name='item2')
        ]
        
        # Convert to dict
        data = namespace_to_dict(ns)
        
        # Simple values
        assert data['simple'] == 'value'
        assert data['number'] == 42
        assert data['boolean'] is True
        
        # Nested dict
        assert isinstance(data['nested'], dict)
        assert data['nested']['key'] == 'nested_value'
        assert data['nested']['list'] == [1, 2, 3]
        
        # List of namespaces should be converted to list of dicts
        assert isinstance(data['list_of_ns'][0], dict)
        assert data['list_of_ns'][0]['name'] == 'item1'
        assert data['list_of_ns'][1]['name'] == 'item2'
    
    def test_roundtrip_conversion(self):
        """Test roundtrip conversion between dict and namespace"""
        original = {
            'app': {
                'name': 'TestApp',
                'version': '1.0.0',
                'features': ['feature1', 'feature2']
            },
            'server': {
                'host': '127.0.0.1',
                'port': 8000,
                'options': {
                    'timeout': 30,
                    'retries': 3
                }
            }
        }
        
        # Dict -> Namespace -> Dict
        ns = dict_to_namespace(original)
        result = namespace_to_dict(ns)
        
        # Should be identical to the original
        assert result == original
    
    def test_deep_merge(self):
        """Test deep merging of dictionaries"""
        dict1 = {
            'app': {
                'name': 'App1',
                'version': '1.0.0',
                'debug': True
            },
            'server': {
                'host': '127.0.0.1',
                'port': 8000
            },
            'simple': 'value1'
        }
        
        dict2 = {
            'app': {
                'name': 'App2',
                'features': ['feature1', 'feature2']
            },
            'database': {
                'url': 'sqlite:///test.db'
            },
            'simple': 'value2'
        }
        
        # Merge dict2 into dict1
        result = deep_merge(dict1.copy(), dict2)
        
        # Check merged values
        assert result['app']['name'] == 'App2'  # Overridden
        assert result['app']['version'] == '1.0.0'  # Preserved
        assert result['app']['debug'] is True  # Preserved
        assert result['app']['features'] == ['feature1', 'feature2']  # Added
        
        assert result['server']['host'] == '127.0.0.1'  # Preserved
        assert result['server']['port'] == 8000  # Preserved
        
        assert result['database']['url'] == 'sqlite:///test.db'  # Added
        
        assert result['simple'] == 'value2'  # Overridden
    
    def test_non_dict_values(self):
        """Test handling of non-dict values"""
        # dict_to_namespace with non-dict
        assert dict_to_namespace('string') == 'string'
        assert dict_to_namespace(42) == 42
        assert dict_to_namespace([1, 2, 3]) == [1, 2, 3]
        
        # namespace_to_dict with non-namespace
        assert namespace_to_dict('string') == 'string'
        assert namespace_to_dict(42) == 42
        assert namespace_to_dict([1, 2, 3]) == [1, 2, 3]
