import importlib

from .config import Config
from .note import Note, Notes

version = importlib.metadata.version("py-obsidianmd")

_ = Config
_ = Note
_ = Notes
