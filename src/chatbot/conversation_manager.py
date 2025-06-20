from enum import Enum
from typing import Dict, List, Optional, Tuple
import json
import datetime

class ConversationState(Enum):
    IDLE = "idle"
    AWAITING_DOCUMENTS = "awaiting_documents"
    DOCUMENT_LOADED = "document_loaded"
    ANALYZING = "analyzing"
    RESULTS_READY = "results_ready"

class ConversationManager:
    def __init__(self):
        self.state = ConversationState.IDLE
        self.documents = {}
        self.analysis_results = {}
        self.conversation_history = []
        self.current_session = {
            'start_time': datetime.datetime.now(),
            'documents_compared': 0,
            'analysis_types': []
        }
    
    def add_message(self, role: str, content: str):
        """Agrega un mensaje al historial"""
        self.conversation_history.append({
            'timestamp': datetime.datetime.now().isoformat(),
            'role': role,
            'content': content
        })
    
    def set_state(self, new_state: ConversationState):
        """Cambia el estado de la conversación"""
        self.state = new_state
        self.add_message('system', f'Estado cambiado a: {new_state.value}')
    
    def add_document(self, doc_id: str, content: Dict):
        """Agrega un documento para análisis"""
        self.documents[doc_id] = content
        if len(self.documents) >= 2:
            self.set_state(ConversationState.DOCUMENT_LOADED)
    
    def get_context(self) -> Dict:
        """Obtiene el contexto actual de la conversación"""
        return {
            'state': self.state.value,
            'documents_loaded': len(self.documents),
            'has_results': bool(self.analysis_results),
            'session_info': self.current_session,
            'last_messages': self.conversation_history[-5:]
        }
    
    def clear_session(self):
        """Limpia la sesión actual"""
        self.documents.clear()
        self.analysis_results.clear()
        self.set_state(ConversationState.IDLE)
        self.current_session['documents_compared'] += len(self.documents)