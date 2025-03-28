import logging
import sys
from logging.handlers import RotatingFileHandler
import colorlog

def setup_logger(name='RancherTools'):
    """Configure color-coded logging with file rotation"""
    formatter = colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s - %(levelname)-8s%(reset)s %(blue)s%(name)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        },
        secondary_log_colors={},
        style='%'
    )

    # Console handler with colors
    console = colorlog.StreamHandler(sys.stdout)
    console.setFormatter(formatter)

    # File handler (no colors)
    file_handler = RotatingFileHandler(
        'rancher_tools.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=3
    )
    file_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)-8s - %(name)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_formatter)

    logger = colorlog.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.addHandler(console)
    logger.addHandler(file_handler)
    
    return logger

logger = setup_logger()
