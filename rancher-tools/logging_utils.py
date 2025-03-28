import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logger(name, log_file='rancher_tools.log', level=logging.INFO):
    """Configure centralized logging"""
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    
    # File handler with rotation
    fh = RotatingFileHandler(
        log_file,
        maxBytes=1024*1024*5,  # 5MB
        backupCount=3
    )
    fh.setFormatter(formatter)
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(ch)
    logger.addHandler(fh)
    
    return logger

# Singleton logger instance
logger = setup_logger('RancherTools')
