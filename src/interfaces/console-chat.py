        print(Fore.CYAN + "   🤖 PDF Comparator AI - Chat Inteligente")
        print(Fore.CYAN + "=" * 60)
        print(Fore.YELLOW + "\nEscribe '/help' para ver comandos disponibles")
        print(Fore.YELLOW + "Escribe 'exit' para salir\n")
    
    def print_message(self, role: str, message: str):
        """Imprime un mensaje con formato"""
        if role == "user":
            print(Fore.GREEN + f"👤 Tú: {message}")
        elif role == "assistant":
            print(Fore.BLUE + f"🤖 Bot: {message}")
        elif role == "system":
            print(Fore.YELLOW + f"📢 Sistema: {message}")
        print()
    
    def get_user_input(self) -> str:
        """Obtiene entrada del usuario"""
        return input(Fore.WHITE + ">>> ")
    
    def process_input(self, user_input: str) -> str:
        """Procesa la entrada del usuario"""
        # Verificar si es un comando
        if user_input.startswith('/'):
            parts = user_input.split()
            command = parts[0]
            args = parts[1:] if len(parts) > 1 else []
            context = self.conversation_manager.get_context()
            return self.command_handler.process_command(command, args, context)
        
        # Procesar como mensaje normal
        return self.handle_message(user_input)
    
    def handle_message(self, message: str) -> str:
        """Maneja mensajes normales del chat"""
        # Aquí iría la lógica del procesamiento de lenguaje natural
        
        if "cargar" in message.lower() or "subir" in message.lower():
            return "Para cargar PDFs, usa el comando '/load <ruta_archivo1> <ruta_archivo2>'"
        
        if "comparar" in message.lower() or "analizar" in message.lower():
            if len(self.conversation_manager.documents) < 2:
                return "Primero necesitas cargar 2 documentos PDF. Usa '/load' para cargarlos."
            else:
                return "Los documentos están listos. Usa '/analyze' para iniciar el análisis."
        
        if "ayuda" in message.lower() or "help" in message.lower():
            return "Usa el comando '/help' para ver todos los comandos disponibles."
        
        return f"Entiendo que dijiste: '{message}'. ¿En qué puedo ayudarte con la comparación de PDFs?"
    
    def load_pdfs(self, path1: str, path2: str) -> str:
        """Carga dos PDFs"""
        try:
            # Procesar primer PDF
            if not os.path.exists(path1):
                return f"❌ No se encontró el archivo: {path1}"
            
            content1 = self.pdf_processor.extract_text(path1)
            self.conversation_manager.add_document("doc1", content1)
            
            # Procesar segundo PDF
            if not os.path.exists(path2):
                return f"❌ No se encontró el archivo: {path2}"
            
            content2 = self.pdf_processor.extract_text(path2)
            self.conversation_manager.add_document("doc2", content2)
            
            return "✅ Ambos PDFs cargados exitosamente. Usa '/analyze' para comparar."
            
        except Exception as e:
            import os
import sys
from colorama import init, Fore, Back, Style
from typing import Optional
from src.core.pdf_processor import PDFProcessor
from src.core.text_analyzer import TextAnalyzer
from src.core.embeddings import EmbeddingAnalyzer
from src.chatbot.conversation_manager import ConversationManager
from src.chatbot.commands import CommandHandler

# Inicializar colorama
init(autoreset=True)

class ConsoleChat:
    def __init__(self):
        self.conversation_manager = ConversationManager()
        self.command_handler = CommandHandler()
        self.pdf_processor = PDFProcessor()
        self.text_analyzer = TextAnalyzer()
        self.embedding_analyzer = EmbeddingAnalyzer()
        
    def clear_screen(self):
        """Limpia la pantalla"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self):
        """Imprime el header del chat"""
        self.clear_screen()
        print(Fore.CYAN + "=" * 60)
        print(Fore.CYAN + "   🤖 PDF Comparator AI