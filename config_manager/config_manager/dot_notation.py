from types import SimpleNamespace
from typing import Dict, Any, List
from types import SimpleNamespace

class IterableNamespace(SimpleNamespace):
    """A SimpleNamespace that's also iterable"""
    
    def __iter__(self):
        """Make the namespace iterable, returning (key, value) pairs"""
        for key, value in vars(self).items():
            yield key, value

    def __str__(self):
        """Override the string representation to look cleaner"""
        # Get the attributes
        attrs = vars(self)
        if not attrs:
            return '{}'
        
        # Format them as key-value pairs
        attr_str = ', '.join(f'{key}={value!r}' for key, value in attrs.items())
        return f'{{{attr_str}}}'
    
    def __repr__(self):
        """Override the repr to look cleaner"""
        return self.__str__()            

def dict_to_namespace(d):
    """
    Convert a dictionary to an IterableNamespace recursively
    allowing for dot notation access and iteration
    
    Args:
        d: Dictionary to convert
        
    Returns:
        IterableNamespace object or original value if not a dict
    """
    if not isinstance(d, dict):
        return d
    
    # Create a new IterableNamespace instead of SimpleNamespace
    namespace = IterableNamespace()
    
    # Convert each key-value pair and set as attribute
    for key, value in d.items():
        if isinstance(value, dict):
            # Recursively convert nested dictionaries
            setattr(namespace, key, dict_to_namespace(value))
        elif isinstance(value, list):
            # Convert dictionaries within lists
            new_list = []
            for item in value:
                if isinstance(item, dict):
                    new_list.append(dict_to_namespace(item))
                else:
                    new_list.append(item)
            setattr(namespace, key, new_list)
        else:
            setattr(namespace, key, value)
            
    return namespace

def namespace_to_dict(namespace: SimpleNamespace) -> Dict:
    """
    Convert a SimpleNamespace back to a dictionary recursively
    
    Args:
        namespace: SimpleNamespace to convert
        
    Returns:
        Dictionary representation of the namespace
    """
    if not isinstance(namespace, SimpleNamespace):
        return namespace
        
    result = {}
    for key, value in namespace.__dict__.items():
        if isinstance(value, SimpleNamespace):
            result[key] = namespace_to_dict(value)
        elif isinstance(value, list):
            new_list = []
            for item in value:
                if isinstance(item, SimpleNamespace):
                    new_list.append(namespace_to_dict(item))
                else:
                    new_list.append(item)
            result[key] = new_list
        else:
            result[key] = value
    return result

def deep_merge(target: Dict, source: Dict) -> Dict:
    """
    Recursively merge source dict into target dict
    
    Args:
        target: Target dictionary to merge into
        source: Source dictionary to merge from
        
    Returns:
        The merged dictionary
    """
    for key, value in source.items():
        if key in target and isinstance(value, dict) and isinstance(target[key], dict):
            deep_merge(target[key], value)
        else:
            target[key] = value
    return target