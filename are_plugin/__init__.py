import importlib.metadata
import sys

if not sys.modules.get('netskope'):
    __version__ = importlib.metadata.version(__package__ or __name__)
