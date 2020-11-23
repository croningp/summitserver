import os
import logging
from logging.handlers import RotatingFileHandler


HERE = os.path.abspath('.')
LOG_PATH = os.path.join(HERE, 'logs')
MAX_BYTES_SIZE = 100*1000 # 100 kB is okay to look through
BACKUP_COUNT = 10 # will give 1 MB of log data at one time

def get_logger(
        logger_name='summit-server',
        stream_level=10,
        logger_filename='summit_server.log'
):
    """ Returns logger instance with preset stream and file handlers.

    Args:
        logger_name (str): logger name, defaults to "summit-server".
        stream_level (int): level of the stream output, defaults to 10
            (logging.DEBUG).
        logger_filename (str): filename to save debug logging.

    Returns:
        :obj:logging.Logger: logger object.
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    logger.handlers = [] # resetting

    ff = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # console handler
    ch = logging.StreamHandler()
    ch.setLevel(stream_level)
    ch.setFormatter(ff)
    logger.addHandler(ch)

    if logger_filename is not None:
        # file handler
        os.makedirs(LOG_PATH, exist_ok=True)
        file_path = os.path.join(LOG_PATH, logger_filename)
        fh = RotatingFileHandler(
            filename=file_path,
            mode='a',
            maxBytes=MAX_BYTES_SIZE,
            backupCount=BACKUP_COUNT
        )
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(ff)
        logger.addHandler(fh)

    return logger
