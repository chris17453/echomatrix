import logging

logger = logging.getLogger(__name__)


def set_logging(level):
    """
    Set the verbosity level for the current module and its children.
    
    Args:
        level: Logging level as integer (0-5) or string:
           - 0, "off": No logging
           - 1, "critical": Critical errors only
           - 2, "error": Errors and above
           - 3, "warning": Warnings and above
           - 4, "info": Info and above (normal operation)
           - 5, "debug": Debug (maximum verbosity)
    """
    # Get the base module name (first part of __name__)
    module_base = __name__.split('.')[0]
    module_logger = logging.getLogger(module_base)
    
    # Map values to standard logging levels
    level_map = {
        0: 100,  # Off (above CRITICAL)
        "off": 100,
        1: logging.CRITICAL,
        "critical": logging.CRITICAL,
        2: logging.ERROR,
        "error": logging.ERROR,
        3: logging.WARNING,
        "warning": logging.WARNING,
        4: logging.INFO,
        "info": logging.INFO,
        5: logging.DEBUG,
        "debug": logging.DEBUG
    }
    
    # Handle string input
    if isinstance(level, str):
        level = level.lower()
        if level.isdigit():
            level = int(level)
    
    # Get logging level
    logging_level = level_map.get(level, logging.INFO)
    
    # For level 0/off, disable all logging
    if logging_level == 100:
        # Remove all handlers
        for handler in module_logger.handlers[:]:
            module_logger.removeHandler(handler)
        
        # Add a null handler
        module_logger.addHandler(logging.NullHandler())
        module_logger.setLevel(logging.CRITICAL)
        
        # Critical: stop propagation to parent loggers
        module_logger.propagate = False
    else:
        # Set the level for normal operation
        module_logger.setLevel(logging_level)
        module_logger.propagate = True
    
    # Apply same settings to all child loggers in the module
    for name in logging.Logger.manager.loggerDict:
        if name == module_base or name.startswith(f"{module_base}."):
            logger = logging.getLogger(name)
            if logging_level == 100:
                for handler in logger.handlers[:]:
                    logger.removeHandler(handler)
                logger.addHandler(logging.NullHandler())
                logger.setLevel(logging.CRITICAL)
                logger.propagate = False
            else:
                logger.setLevel(logging_level)
                logger.propagate = True
    
    return logging_level