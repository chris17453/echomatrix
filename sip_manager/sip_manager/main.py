import os
import logging
import pjsua2 as pj
import time
import sys
import threading
from .config import default_config
from . import SipAgent

# Simplified path handling
parent_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)),"..", "config_manager"))
sys.path.append(parent_dir)

from config_manager import Config






# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)




def configure_audio(agent):
    """Configure audio settings for better compatibility"""
    # Set codec priorities
    ep = agent.ep
    
    # Proper way to get codecs in PJSUA2
    ep.codecSetPriority("PCMU/8000", 255)  # G.711 μ-law
    ep.codecSetPriority("PCMA/8000", 254)  # G.711 A-law
    
    # Make sure all other codecs have low priority
    ep.codecSetPriority("iLBC/8000", 1)
    ep.codecSetPriority("GSM/8000", 1)
    ep.codecSetPriority("speex/8000", 1)
    ep.codecSetPriority("speex/16000", 1)
    
    # Ensure null device is set correctly
    ep.audDevManager().setNullDev()
    
    logger.info("Audio configured successfully")

    

if __name__ == "__main__":


    logger.info(f"Starting EchoMatrix")
    config_path ="../audio_manager.yaml"
    config_manager = Config(config_path=config_path, default_config=default_config, env_prefix='AUDIO_MANAGER_')
    
    config = config_manager.sip

    # Replace with your Twilio SIP credentials and your server's IP address

    
    try:
        # Create and start SIP agent
        agent = SipAgent(config)
        agent.test_audio_routing()
        configure_audio(agent)
        agent.register_account()
        agent.start()
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

