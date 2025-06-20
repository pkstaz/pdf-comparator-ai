# Procesar comando o pregunta
            response = process_chat_input(user_input)
            
            # Agregar respuesta del bot
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            # Rerun para actualizar el chat
            st.rerun()
    
    with tab3:
        st.header("📊 Resultados del Análisis")
        
        if st.session_state.analysis_results:
            # Métricas principales
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                similarity = st.session_state.analysis_results.get('basic', {}).get('similarity_ratio', 0)
                st.metric("Similitud General", f"{similarity:.1%}")
            
            with col2:
                semantic_sim = st.session_state.analysis_results.get('semantic', {}).get('overall_similarity', 0)
                st.metric("Similitud Semántica", f"{semantic_sim:.1%}")
            
            with col3:
                structural_sim = st.session_state.analysis_results.get('structural_similarity', 0)
                st.metric("Similitud Estructural", f"{structural_sim:.1%}")
            
            with col4:
                tfidf_sim = st.session_state.analysis_results.get('tfidf', {}).get('cosine_similarity', 0)
                st.metric("Similitud TF-IDF", f"{tfidf_sim:.1%}")
            
            st.divider()
            
            # Visualizaciones
            col1, col2 = st.columns(2)
            
            with col1:
                # Gráfico de radar
                fig_radar = create_radar_chart(st.session_state.analysis_results)
                st.plotly_chart(fig_radar, use_container_width=True)
            
            with col2:
                # Gráfico de barras
                fig_bars = create_comparison_bars(st.session_state.analysis_results)
                st.plotly_chart(fig_bars, use_container_width=True)
            
            # Detalles del análisis
            with st.expander("🔍 Detalles del Análisis Básico"):
                basic_results = st.session_state.analysis_results.get('basic', {})
                st.write(f"**Líneas añadidas:** {basic_results.get('added_lines', 0)}")
                st.write(f"**Líneas eliminadas:** {basic_results.get('removed_lines', 0)}")
            
            with st.expander("🧠 Detalles del Análisis Semántico"):
                semantic_results = st.session_state.analysis_results.get('semantic', {})
                st.write("**Pares similares encontrados:**")
                for pair in semantic_results.get('similar_pairs', [])[:5]:
                    st.write(f"- Similitud: {pair['similarity']:.2f}")
            
            with st.expander("📊 Detalles del Análisis TF-IDF"):
                tfidf_results = st.session_state.analysis_results.get('tfidf', {})
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Términos únicos Doc1:**")
                    for term in tfidf_results.get('unique_terms_doc1', [])[:10]:
                        st.write(f"- {term}")
                with col2:
                    st.write("**Términos únicos Doc2:**")
                    for term in tfidf_results.get('unique_terms_doc2', [])[:10]:
                        st.write(f"- {term}")
        else:
            st.info("No hay resultados disponibles. Carga dos documentos y ejecuta el análisis.")
    
    with tab4:
        st.header("📄 Generar Reporte")
        
        if st.session_state.analysis_results:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                report_type = st.selectbox(
                    "Tipo de reporte",
                    ["Ejecutivo", "Detallado", "Técnico", "Comparativo"]
                )
                
                include_options = {
                    "summary": st.checkbox("Incluir resumen ejecutivo", value=True),
                    "visualizations": st.checkbox("Incluir visualizaciones", value=True),
                    "recommendations": st.checkbox("Incluir recomendaciones", value=True),
                    "technical": st.checkbox("Incluir detalles técnicos", value=False)
                }
            
            with col2:
                export_format = st.radio(
                    "Formato de exportación",
                    ["PDF", "HTML", "DOCX", "JSON"]
                )
            
            if st.button("📥 Generar Reporte", type="primary", use_container_width=True):
                with st.spinner("Generando reporte..."):
                    report_generator = ReportGenerator()
                    report = report_generator.generate(
                        st.session_state.analysis_results,
                        report_type,
                        include_options,
                        export_format
                    )
                    st.success(f"✅ Reporte generado en formato {export_format}")
                    st.download_button(
                        label=f"Descargar {export_format}",
                        data=report,
                        file_name=f"comparacion_pdf_{report_type.lower()}.{export_format.lower()}",
                        mime=f"application/{export_format.lower()}"
                    )
        else:
            st.info("Ejecuta un análisis primero para generar reportes.")

def run_analysis(analysis_options, domain):
    """Ejecuta el análisis completo"""
    with st.spinner("Ejecutando análisis completo..."):
        # Inicializar analizadores
        text_analyzer = TextAnalyzer()
        embedding_analyzer = EmbeddingAnalyzer()
        
        # Obtener documentos
        doc1 = st.session_state.conversation_manager.documents.get("doc1")
        doc2 = st.session_state.conversation_manager.documents.get("doc2")
        
        results = {}
        
        # Análisis básico
        if analysis_options["basic"]:
            results["basic"] = text_analyzer.basic_comparison(doc1.text, doc2.text)
        
        # Análisis semántico
        if analysis_options["semantic"]:
            results["semantic"] = embedding_analyzer.semantic_comparison(doc1.text, doc2.text)
        
        # Análisis TF-IDF
        if analysis_options["tfidf"]:
            results["tfidf"] = text_analyzer.tfidf_analysis(doc1.text, doc2.text)
        
        # Análisis estructural
        if analysis_options["structural"]:
            results["structural_similarity"] = text_analyzer.structural_similarity(
                doc1.structure, doc2.structure
            )
        
        st.session_state.analysis_results = results
        st.success("✅ Análisis completado")

def process_chat_input(user_input):
    """Procesa la entrada del chat"""
    # Aquí iría la lógica del chatbot
    return f"Procesando: {user_input}"

def create_radar_chart(results):
    """Crea gráfico de radar con los resultados"""
    categories = ['Similitud\nGeneral', 'Similitud\nSemántica', 'Similitud\nEstructural', 'Similitud\nTF-IDF']
    values = [
        results.get('basic', {}).get('similarity_ratio', 0),
        results.get('semantic', {}).get('overall_similarity', 0),
        results.get('structural_similarity', 0),
        results.get('tfidf', {}).get('cosine_similarity', 0)
    ]
    
    fig = go.Figure(data=go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='Similitud'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1]
            )),
        showlegend=False,
        title="Análisis de Similitud Multidimensional"
    )
    
    return fig

def create_comparison_bars(results):
    """Crea gráfico de barras comparativo"""
    data = {
        'Métrica': ['Líneas Añadidas', 'Líneas Eliminadas', 'Chunks Únicos Doc1', 'Chunks Únicos Doc2'],
        'Valor': [
            results.get('basic', {}).get('added_lines', 0),
            results.get('basic', {}).get('removed_lines', 0),
            len(results.get('semantic', {}).get('unique_chunks_doc1', [])),
            len(results.get('semantic', {}).get('unique_chunks_doc2', []))
        ]
    }
    
    fig = px.bar(data, x='Métrica', y='Valor', title='Diferencias Encontradas')
    return fig

if __name__ == "__main__":
    main()