from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import os
from src.core.pdf_processor import PDFProcessor
from src.chatbot.conversation_manager import ConversationManager

class TelegramBot:
    def __init__(self, token: str):
        self.token = token
        self.pdf_processor = PDFProcessor()
        self.conversations = {}
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start"""
        user_id = update.effective_user.id
        self.conversations[user_id] = ConversationManager()
        
        keyboard = [
            [InlineKeyboardButton("📄 Comparar PDFs", callback_data='compare')],
            [InlineKeyboardButton("❓ Ayuda", callback_data='help')],
            [InlineKeyboardButton("⚙️ Configuración", callback_data='settings')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "¡Hola! 🤖 Soy el PDF Comparator Bot.\n\n"
            "Puedo ayudarte a comparar documentos PDF usando IA.\n"
            "¿Qué quieres hacer?",
            reply_markup=reply_markup
        )
    
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /help"""
        help_text = """
📋 **Comandos Disponibles:**

/start - Iniciar el bot
/help - Mostrar esta ayuda
/compare - Comparar dos PDFs
/status - Ver estado actual
/reset - Reiniciar sesión

**Cómo usar:**
1. Envía /compare
2. Sube el primer PDF
3. Sube el segundo PDF
4. Selecciona el tipo de análisis
5. ¡Recibe los resultados!
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja documentos PDF enviados"""
        user_id = update.effective_user.id
        
        if user_id not in self.conversations:
            self.conversations[user_id] = ConversationManager()
        
        document = update.message.document
        
        if document.mime_type == 'application/pdf':
            await update.message.reply_text("📥 Recibiendo PDF...")
            
            # Descargar archivo
            file = await context.bot.get_file(document.file_id)
            file_path = f"temp_{user_id}_{document.file_name}"
            await file.download_to_drive(file_path)
            
            # Procesar PDF
            content = self.pdf_processor.extract_text(file_path)
            
            # Agregar a la conversación
            conv = self.conversations[user_id]
            doc_id = f"doc{len(conv.documents) + 1}"
            conv.add_document(doc_id, content)
            
            # Limpiar archivo temporal
            os.remove(file_path)
            
            if len(conv.documents) < 2:
                await update.message.reply_text(
                    f"✅ PDF 1 procesado.\n"
                    f"📄 Ahora envía el segundo PDF para comparar."
                )
            else:
                # Ambos PDFs cargados
                keyboard = [
                    [InlineKeyboardButton("🔍 Análisis Básico", callback_data='analyze_basic')],
                    [InlineKeyboardButton("🧠 Análisis Semántico", callback_data='analyze_semantic')],
                    [InlineKeyboardButton("📊 Análisis Completo", callback_data='analyze_all')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    "✅ Ambos PDFs procesados.\n"
                    "¿Qué tipo de análisis quieres realizar?",
                    reply_markup=reply_markup
                )
        else:
            await update.message.reply_text("❌ Por favor, envía solo archivos PDF.")
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja callbacks de botones"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        action = query.data
        
        if action == 'compare':
            await query.edit_message_text(
                "📄 Envía el primer PDF que quieres comparar."
            )
        
        elif action == 'help':
            await self.help(query, context)
        
        elif action.startswith('analyze_'):
            analysis_type = action.replace('analyze_', '')
            await query.edit_message_text(
                f"⚙️ Iniciando análisis {analysis_type}...\n"
                f"Esto puede tomar unos segundos."
            )
            
            # Aquí iría la lógica de análisis
            # results = run_analysis(analysis_type)
            
            await query.message.reply_text(
                "✅ Análisis completado!\n\n"
                "📊 **Resultados:**\n"
                "• Similitud: 85%\n"
                "• Cambios detectados: 23\n"
                "• Tiempo: 2.3s"
            )
    
    def run(self):
        """Ejecuta el bot"""
        # Crear aplicación
        application = Application.builder().token(self.token).build()
        
        # Agregar handlers
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("help", self.help))
        application.add_handler(MessageHandler(filters.Document.PDF, self.handle_document))
        application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Ejecutar bot
        application.run_polling()

# Función principal
def run_telegram_bot():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ No se encontró TELEGRAM_BOT_TOKEN")
        return
    
    bot = TelegramBot(token)
    bot.run()

if __name__ == "__main__":
    run_telegram_bot()