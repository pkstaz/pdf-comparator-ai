        if not pdf1 or not pdf2:
            return "Por favor, carga ambos PDFs para comparar."
        
        # Procesar PDFs
        content1 = self.pdf_processor.extract_text(pdf1.name)
        content2 = self.pdf_processor.extract_text(pdf2.name)
        
        results = {}
        
        # Ejecutar análisis seleccionados
        if "Análisis Básico" in analysis_types:
            results["basic"] = self.text_analyzer.basic_comparison(
                content1.text, content2.text
            )
        
        if "Análisis Semántico" in analysis_types:
            results["semantic"] = self.embedding_analyzer.semantic_comparison(
                content1.text, content2.text
            )
        
        if "Análisis TF-IDF" in analysis_types:
            results["tfidf"] = self.text_analyzer.tfidf_analysis(
                content1.text, content2.text
            )
        
        if "Análisis Estructural" in analysis_types:
            results["structural"] = self.text_analyzer.structural_similarity(
                content1.structure, content2.structure
            )
        
        return self.format_results(results)
    
    def format_results(self, results):
        """Formatea los resultados para mostrar"""
        output = "# 📊 Resultados del Análisis\n\n"
        
        if "basic" in results:
            basic = results["basic"]
            output += f"""## 🔍 Análisis Básico
- **Similitud General:** {basic['similarity_ratio']:.1%}
- **Líneas Añadidas:** {basic['added_lines']}
- **Líneas Eliminadas:** {basic['removed_lines']}

"""
        
        if "semantic" in results:
            semantic = results["semantic"]
            output += f"""## 🧠 Análisis Semántico
- **Similitud Semántica:** {semantic['overall_similarity']:.1%}
- **Chunks Doc1:** {semantic['num_chunks_doc1']}
- **Chunks Doc2:** {semantic['num_chunks_doc2']}
- **Pares Similares:** {len(semantic['similar_pairs'])}

"""
        
        if "tfidf" in results:
            tfidf = results["tfidf"]
            output += f"""## 📊 Análisis TF-IDF
- **Similitud Coseno:** {tfidf['cosine_similarity']:.1%}
- **Términos Únicos Doc1:** {len(tfidf.get('unique_terms_doc1', []))}
- **Términos Únicos Doc2:** {len(tfidf.get('unique_terms_doc2', []))}

"""
        
        if "structural" in results:
            output += f"""## 🏗️ Análisis Estructural
- **Similitud Estructural:** {results['structural']:.1%}

"""
        
        return output
    
    def chat_interface(self, message, history):
        """Interfaz de chat"""
        # Aquí iría la lógica del chatbot
        response = f"Echo: {message}"
        return response
    
    def create_interface(self):
        """Crea la interfaz Gradio"""
        with gr.Blocks(title="PDF Comparator AI", theme=gr.themes.Soft()) as demo:
            gr.Markdown("""
            # 🤖 PDF Comparator con IA
            ### Sistema inteligente para comparar documentos PDF
            """)
            
            with gr.Tab("📄 Comparar PDFs"):
                with gr.Row():
                    pdf1_input = gr.File(label="PDF 1", file_types=[".pdf"])
                    pdf2_input = gr.File(label="PDF 2", file_types=[".pdf"])
                
                analysis_types = gr.CheckboxGroup(
                    ["Análisis Básico", "Análisis Semántico", "Análisis TF-IDF", "Análisis Estructural"],
                    label="Tipos de Análisis",
                    value=["Análisis Básico", "Análisis Semántico"]
                )
                
                compare_btn = gr.Button("🚀 Comparar PDFs", variant="primary")
                
                output = gr.Markdown()
                
                compare_btn.click(
                    fn=self.compare_pdfs,
                    inputs=[pdf1_input, pdf2_input, analysis_types],
                    outputs=output
                )
            
            with gr.Tab("💬 Chat"):
                chatbot = gr.Chatbot()
                msg = gr.Textbox(label="Mensaje", placeholder="Escribe tu pregunta...")
                clear = gr.Button("Limpiar")
                
                msg.submit(self.chat_interface, [msg, chatbot], [chatbot])
                clear.click(lambda: None, None, chatbot, queue=False)
            
            with gr.Tab("📊 Estadísticas"):
                gr.Markdown("""
                ### Estadísticas de Uso
                - Documentos procesados: 0
                - Análisis realizados: 0
                - Tiempo promedio: 0s
                """)
        
        return demo

# Función principal para lanzar la app
def launch_gradio():
    interface = GradioInterface()
    demo = interface.create_interface()
    demo.launch(share=True)

if __name__ == "__main__":
    launch_gradio()import gradio as gr
from src.core.pdf_processor import PDFProcessor
from src.core.text_analyzer import TextAnalyzer
from src.core.embeddings import EmbeddingAnalyzer
import json

class GradioInterface:
    def __init__(self):
        self.pdf_processor = PDFProcessor()
        self.text_analyzer = TextAnalyzer()
        self.embedding_analyzer = EmbeddingAnalyzer()
        
    def compare_pdfs(self, pdf1, pdf2, analysis_types):
        """Función principal de comparación"""
        if not pdf1 or not pdf2