import os

from logging.handlers import WatchedFileHandler as BaseWatchedFileHandler


class WatchedFileHandler(BaseWatchedFileHandler):
    def __init__(self, filename, **kwargs):
        path = os.path.dirname(filename)
        os.makedirs(path, exist_ok=True)
        super().__init__(filename, **kwargs)
