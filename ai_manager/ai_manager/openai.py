from openai import OpenAI
import logging

logger = logging.getLogger(__name__)



def init_openai_client(config):
    """
    Initialize the OpenAI client using configuration.
    
    Args:
        config: Configuration object with openai settings
        
    Returns:
        OpenAI: Initialized OpenAI client or None on failure
    """
    try:
        # Access configuration using dot notation
        client = OpenAI(
            api_key=config.openai.api_key,
            organization=config.openai.organization_id
        )
        return client
    except Exception as e:
        logger.error(f"Error initializing OpenAI client: {e}")
        return None