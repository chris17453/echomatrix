import yaml
import os
import uuid
import logging
from openai import OpenAI
from types import SimpleNamespace

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='/var/log/echomatrix/echomatrix_agi.log'
)
logger = logging.getLogger('echomatrix_agi')

_config_path = "/web/echomatrix/config.yaml"

_default_config = {
    'ari':{
        'uri':None,
        'app':None,
        'secret':None
    },
    'openai': {
        'api_key': '',
        'organization_id': None,
        'whisper_model': 'whisper-1',
        'gpt_model': 'gpt-3.5-turbo',
        'tts_voice': 'echo',
    },
    'temp_dir': '/tmp',
    'max_audio_file_size_mb' : 50,
    'sample_rate' : 8000,
    'min_sample_rate' : 8000,
    'max_sample_rate' : 48000,
    'max_recording_days': 30,
    'folders':{
        'prompts':'/web/echomatrix/prompts/',
        'recordings':'/var/lib/asterisk/recordings/'
    }
}


def dict_to_namespace(d):
    """
    Convert a dictionary to a SimpleNamespace recursively
    allowing for dot notation access
    """
    if not isinstance(d, dict):
        return d
    
    # Create a new SimpleNamespace
    namespace = SimpleNamespace()
    
    # Convert each key-value pair and set as attribute
    for key, value in d.items():
        if isinstance(value, dict):
            # Recursively convert nested dictionaries
            setattr(namespace, key, dict_to_namespace(value))
        else:
            setattr(namespace, key, value)
            
    return namespace


class Config:
    def __init__(self, config_path=_config_path):
        self._config_path = config_path

        with open(config_path) as f:
            user_config = yaml.safe_load(f) or {}

        merged_config = _default_config.copy()
        
        # Deep merge the dictionaries
        for section, values in user_config.items():
            if section not in merged_config:
                merged_config[section] = values
            elif isinstance(values, dict) and isinstance(merged_config[section], dict):
                # Deep merge for dictionaries
                self._deep_merge(merged_config[section], values)
            else:
                merged_config[section] = values

        # Set regular attributes directly
        for key, value in merged_config.items():
            if isinstance(value, dict):
                # Convert dictionaries to namespaces for dot notation
                setattr(self, key, dict_to_namespace(value))
            else:
                setattr(self, key, value)
    
    def _deep_merge(self, target, source):
        """
        Recursively merge source dict into target dict
        """
        for key, value in source.items():
            if key in target and isinstance(value, dict) and isinstance(target[key], dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value

    def generate_temp_audio_path(self):
        temp_dir = getattr(self, 'temp_dir', '/tmp')
        return os.path.join(temp_dir, f"ivr_input_{uuid.uuid4().hex}.wav")

    def generate_temp_mp3_path(self):
        temp_dir = getattr(self, 'temp_dir', '/tmp')
        return os.path.join(temp_dir, f"ivr_response_{uuid.uuid4().hex}.mp3")

    def save(self):
        data = {}
        for key in _default_config:
            attr = getattr(self, key, None)
            if isinstance(attr, SimpleNamespace):
                # Convert namespace back to dict for saving
                data[key] = self._namespace_to_dict(attr)
            else:
                data[key] = attr
                
        with open(self._config_path, 'w') as f:
            yaml.safe_dump(data, f, default_flow_style=False)
    
    def _namespace_to_dict(self, namespace):
        """
        Convert a SimpleNamespace back to a dictionary recursively
        """
        result = {}
        for key, value in namespace.__dict__.items():
            if isinstance(value, SimpleNamespace):
                result[key] = self._namespace_to_dict(value)
            else:
                result[key] = value
        return result


# Create the config instance
config = Config()

# Now you can use dot notation for nested attributes
client = OpenAI(
    api_key=config.openai.api_key,
    organization=config.openai.organization_id
)