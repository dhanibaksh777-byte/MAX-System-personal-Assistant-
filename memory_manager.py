"""
Max Assistant - Conversation Memory Manager
Handles persistent conversation storage and retrieval.
"""
import json
import os
from datetime import datetime
from config import MEMORY_FILE, MAX_MEMORY_MESSAGES


class MemoryManager:
    """Manages conversation memory with persistent JSON storage."""

    def __init__(self):
        self.memory_file = MEMORY_FILE
        self.messages = []
        self._load()

    def _load(self):
        """Load conversation history from disk."""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.messages = data.get('messages', [])
        except (json.JSONDecodeError, IOError):
            self.messages = []

    def _save(self):
        """Save conversation history to disk."""
        try:
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'messages': self.messages,
                    'last_updated': datetime.now().isoformat(),
                    'total_messages': len(self.messages)
                }, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"[Memory] Error saving: {e}")

    def add_message(self, role: str, content: str):
        """Add a message to memory."""
        entry = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        }
        self.messages.append(entry)

        # Trim if exceeding max
        if len(self.messages) > MAX_MEMORY_MESSAGES:
            self.messages = self.messages[-MAX_MEMORY_MESSAGES:]

        self._save()

    def get_recent_messages(self, limit: int = 20):
        """Get recent messages formatted for LLM context."""
        recent = self.messages[-limit:] if len(self.messages) > limit else self.messages
        return [{'role': m['role'], 'content': m['content']} for m in recent]

    def get_summary(self):
        """Get a brief summary of conversation history."""
        if not self.messages:
            return "No previous conversations."
        
        count = len(self.messages)
        first = self.messages[0].get('timestamp', 'unknown')
        last = self.messages[-1].get('timestamp', 'unknown')
        return f"{count} messages from {first} to {last}"

    def clear(self):
        """Clear all conversation history."""
        self.messages = []
        self._save()

    def search(self, query: str):
        """Search through conversation history."""
        query_lower = query.lower()
        results = []
        for msg in self.messages:
            if query_lower in msg['content'].lower():
                results.append(msg)
        return results
