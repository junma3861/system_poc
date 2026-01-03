"""Chat Companion package exposing LLM, prompt, and memory utilities."""

from .chatbot import Chatbot
from .config import Settings, load_settings

__all__ = ["Chatbot", "Settings", "load_settings"]
__version__ = "0.1.0"
