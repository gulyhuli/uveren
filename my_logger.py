import logging
import logging.config
from os import path
import os


def get_logger():
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s')
    handler.setFormatter(formatter)
    logger = logging.getLogger('root')
    logger.addHandler(handler)
    return logger
