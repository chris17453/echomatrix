import os
import logging
import time
import sys
from .config import engine_instance
from  .engine import engine

# Create log directory if it doesn't exist
log_dir = "/var/log/echomatrix"
os.makedirs(log_dir, exist_ok=True)

# Set up logging to file
log_file = os.path.join(log_dir, "full.log")
logging.basicConfig(
    filename=log_file,
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
logger.info("Logging initialized")

if __name__ == "__main__":
    logger.info("Starting EchoMatrix")
    config_path = "config.yaml"
    engine_instance=engine(config_path)



      