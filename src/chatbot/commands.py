from typing import Dict, Callable, List, Tuple

class CommandHandler:
    def __init__(self):
        self.commands = {
            '/help': self.help_command,
            '/status': self.status_command,
            '/reset': self.reset_command,
            '/analyze': self.analyze_command,
            '/export': self.export_command,
            '/compare': self.compare_command,
            '/settings': self.settings_command
        }
        
    def process_command(self, command: str, args: List[str], context: Dict) -> str:
        """Procesa un comando del chatbot"""
        if command in self.commands:
            return self.commands[command](args, context)
        return f"Comando desconocido: {command}. Usa /help para ver comandos disponibles."
    
    def help_command(self, args: List[str], context: Dict) -> str:
        """Muestra ayuda sobre comandos disponibles"""
        return """
📋 **Comandos Disponibles:**

🔹 `/help` - Muestra esta ayuda
🔹 `/status` - Estado actual del análisis
🔹 `/reset` - Reinicia la sesión
🔹 `/analyze [tipo]` - Inicia análisis (tipos: basic, semantic, tfidf, ai)
🔹 `/compare` - Compara documentos cargados
🔹 `/export [formato]` - Exporta resultados (pdf, json, html)
🔹 `/settings` - Configuración del análisis

💡 **Ejemplos:**
- `/analyze semantic` - Análisis semántico
- `/export pdf` - Exportar como PDF
        """
    
    def status_command(self, args: List[str], context: Dict) -> str:
        """Muestra el estado actual"""
        state = context.get('state', 'idle')
        docs = context.get('documents_loaded', 0)
        
        status_messages = {
            'idle': '😴 En espera de documentos',
            'awaiting_documents': f'📄 {docs}/2 documentos cargados',
            'document_loaded': '✅ Documentos listos para análisis',
            'analyzing': '⚙️ Analizando documentos...',
            'results_ready': '📊 Resultados disponibles'
        }
        
        return f"""
**Estado Actual:** {status_messages.get(state, 'Desconocido')}
**Documentos cargados:** {docs}
**Sesión iniciada:** {context.get('session_info', {}).get('start_time', 'N/A')}
        """
    
    def reset_command(self, args: List[str], context: Dict) -> str:
        """Reinicia la sesión"""
        return "🔄 Sesión reiniciada. Puedes cargar nuevos documentos."
    
    def analyze_command(self, args: List[str], context: Dict) -> str:
        """Inicia el análisis"""
        if context.get('documents_loaded', 0) < 2:
            return "❌ Necesitas cargar 2 documentos antes de analizar."
        
        analysis_type = args[0] if args else 'all'
        valid_types = ['basic', 'semantic', 'tfidf', 'ai', 'all']
        
        if analysis_type not in valid_types:
            return f"❌ Tipo de análisis inválido. Opciones: {', '.join(valid_types)}"
        
        return f"🔍 Iniciando análisis {analysis_type}..."
    
    def export_command(self, args: List[str], context: Dict) -> str:
        """Exporta los resultados"""
        if not context.get('has_results', False):
            return "❌ No hay resultados para exportar. Ejecuta un análisis primero."
        
        export_format = args[0] if args else 'pdf'
        valid_formats = ['pdf', 'json', 'html', 'docx']
        
        if export_format not in valid_formats:
            return f"❌ Formato inválido. Opciones: {', '.join(valid_formats)}"
        
        return f"📥 Exportando resultados en formato {export_format.upper()}..."
    
    def compare_command(self, args: List[str], context: Dict) -> str:
        """Compara documentos rápidamente"""
        if context.get('documents_loaded', 0) < 2:
            return "❌ Necesitas cargar 2 documentos para comparar."
        
        return "⚡ Iniciando comparación rápida..."
    
    def settings_command(self, args: List[str], context: Dict) -> str:
        """Muestra o modifica configuración"""
        return """
⚙️ **Configuración Actual:**

• **Modelo LLM:** GPT-4
• **Idioma:** Español
• **Umbral similitud:** 0.7
• **Análisis profundo:** Activado
• **Auto-exportar:** Desactivado

Usa `/settings [opción] [valor]` para modificar.
        """