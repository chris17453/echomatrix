import logging

logger = logging.getLogger(__name__)


def set_logging(level):
    """
    Set the verbosity level of the module.
    
    Args:
        level: Logging level as integer (0-5) or string:
           - 0, "off": No logging
           - 1, "critical": Critical errors only
           - 2, "error": Errors and above
           - 3, "warning": Warnings and above
           - 4, "info": Info and above (normal operation)
           - 5, "debug": Debug (maximum verbosity)
    """
    sip_logger = logging.getLogger(__name__)
    
    # Map values to standard logging levels
    level_map = {
        0: 100,               # Off (above CRITICAL)
        "off": 100,
        1: logging.CRITICAL,  # 50
        "critical": logging.CRITICAL,
        2: logging.ERROR,     # 40
        "error": logging.ERROR,
        3: logging.WARNING,   # 30
        "warning": logging.WARNING,
        4: logging.INFO,      # 20
        "info": logging.INFO,
        5: logging.DEBUG,     # 10
        "debug": logging.DEBUG
    }
    
    # Handle string input (convert to lowercase)
    if isinstance(level, str):
        level = level.lower()
        if level.isdigit():
            level = int(level)
    
    # Get logging level
    logging_level = level_map.get(level, logging.INFO)
    
    # For level 0/off, disable all logging
    if logging_level == 100:
        # Remove all handlers
        for handler in sip_logger.handlers[:]:
            sip_logger.removeHandler(handler)
        
        # Add a null handler to suppress all output
        sip_logger.addHandler(logging.NullHandler())
    
    # Set the level
    sip_logger.setLevel(logging_level)
    
    # Log message about the change
    if logging_level == 100:
        logger.info("SIP module logging has been disabled")
    else:
        level_name = logging.getLevelName(logging_level)
        logger.info(f"Set SIP module verbosity to {level} ({level_name})")
    
    return logging_level