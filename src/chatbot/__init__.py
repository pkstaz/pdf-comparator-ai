"""
Chatbot components for conversational interface
"""

from .conversation_manager import ConversationManager, ConversationState
from .commands import CommandHandler

__all__ = [
    "ConversationManager",
    "ConversationState",
    "CommandHandler",
]

# Module constants
DEFAULT_SESSION_TIMEOUT = 3600  # 1 hour
MAX_CONVERSATION_HISTORY = 100