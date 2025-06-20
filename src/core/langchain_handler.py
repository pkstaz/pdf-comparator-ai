from typing import Dict, List, Optional, Any
from langchain.llms.base import LLM
from langchain.llms import VLLMOpenAI
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import LLMChain, RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.vectorstores import FAISS
from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema import Document
import os
import logging
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class MetricsCallbackHandler(BaseCallbackHandler):
    """Callback handler para métricas de LangChain"""
    
    def __init__(self):
        self.metrics = {
            "llm_calls": 0,
            "llm_tokens": 0,
            "llm_errors": 0,
            "chain_runs": 0
        }
    
    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs) -> None:
        self.metrics["llm_calls"] += 1
        logger.debug(f"LLM call started with {len(prompts)} prompts")
    
    def on_llm_error(self, error: Exception, **kwargs) -> None:
        self.metrics["llm_errors"] += 1
        logger.error(f"LLM error: {error}")
    
    def on_chain_start(self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs) -> None:
        self.metrics["chain_runs"] += 1

class LangChainHandler:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.llm = self._initialize_llm()
        self.embeddings = self._initialize_embeddings()
        self.text_splitter = self._initialize_text_splitter()
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        self.callback_handler = MetricsCallbackHandler()
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    def _initialize_llm(self) -> LLM:
        """Inicializa el LLM con vLLM"""
        try:
            llm = VLLMOpenAI(
                openai_api_base=os.getenv("VLLM_ENDPOINT", "http://vllm-service:8000"),
                model_name=os.getenv("VLLM_MODEL_NAME", "granite-3.1-8b-instruct"),
                openai_api_key=os.getenv("VLLM_API_KEY", "EMPTY"),
                temperature=float(os.getenv("VLLM_TEMPERATURE", "0.3")),
                max_tokens=int(os.getenv("VLLM_MAX_TOKENS", "2048")),
                top_p=float(os.getenv("VLLM_TOP_P", "0.95")),
                frequency_penalty=float(os.getenv("VLLM_FREQUENCY_PENALTY", "0.0")),
                presence_penalty=float(os.getenv("VLLM_PRESENCE_PENALTY", "0.0")),
                streaming=True,
                callbacks=[self.callback_handler]
            )
            logger.info(f"LLM initialized with model: {os.getenv('VLLM_MODEL_NAME')}")
            return llm
        except Exception as e:
            logger.error(f"Error initializing LLM: {e}")
            raise
    
    def _initialize_embeddings(self) -> HuggingFaceEmbeddings:
        """Inicializa el modelo de embeddings"""
        return HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
    
    def _initialize_text_splitter(self) -> RecursiveCharacterTextSplitter:
        """Inicializa el text splitter"""
        return RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    async def compare_documents_intelligent(
        self,
        doc1_content: str,
        doc2_content: str,
        analysis_type: str = "general",
        language: str = "es"
    ) -> Dict[str, Any]:
        """Comparación inteligente de documentos usando LangChain"""
        
        # Crear documentos
        docs1 = self.text_splitter.create_documents([doc1_content], metadatas=[{"source": "doc1"}])
        docs2 = self.text_splitter.create_documents([doc2_content], metadatas=[{"source": "doc2"}])
        
        # Crear vectorstore
        all_docs = docs1 + docs2
        vectorstore = await self._create_vectorstore(all_docs)
        
        # Definir prompts según el tipo de análisis
        prompts = self._get_analysis_prompts(analysis_type, language)
        
        # Ejecutar análisis
        results = {}
        
        # Análisis general con chain
        general_chain = LLMChain(
            llm=self.llm,
            prompt=prompts["comparison"],
            callbacks=[self.callback_handler]
        )
        
        results["comparison"] = await self._run_chain_async(
            general_chain,
            {
                "doc1": doc1_content[:3000],
                "doc2": doc2_content[:3000],
                "language": language
            }
        )
        
        # Análisis de diferencias clave
        diff_chain = LLMChain(
            llm=self.llm,
            prompt=prompts["differences"],
            callbacks=[self.callback_handler]
        )
        
        results["key_differences"] = await self._run_chain_async(
            diff_chain,
            {
                "doc1": doc1_content[:3000],
                "doc2": doc2_content[:3000],
                "language": language
            }
        )
        
        # Búsqueda semántica de secciones únicas
        results["unique_sections"] = await self._find_unique_sections(vectorstore, docs1, docs2)
        
        # Generar recomendaciones
        recommendations_chain = LLMChain(
            llm=self.llm,
            prompt=prompts["recommendations"],
            callbacks=[self.callback_handler]
        )
        
        results["recommendations"] = await self._run_chain_async(
            recommendations_chain,
            {
                "analysis": results["comparison"],
                "differences": results["key_differences"],
                "language": language
            }
        )
        
        # Agregar métricas
        results["metrics"] = self.callback_handler.metrics
        
        return results
    
    def _get_analysis_prompts(self, analysis_type: str, language: str) -> Dict[str, PromptTemplate]:
        """Obtiene los prompts según el tipo de análisis"""
        
        base_prompts = {
            "comparison": PromptTemplate(
                input_variables=["doc1", "doc2", "language"],
                template="""Eres un experto en análisis de documentos. Compara estos dos documentos en {language}.

Documento 1:
{doc1}

Documento 2:
{doc2}

Proporciona un análisis detallado que incluya:
1. Resumen de cada documento
2. Principales similitudes
3. Principales diferencias
4. Cambios en la estructura y organización
5. Cambios en el tono y estilo

Responde en {language} de forma clara y estructurada."""
            ),
            
            "differences": PromptTemplate(
                input_variables=["doc1", "doc2", "language"],
                template="""Identifica las diferencias más importantes entre estos documentos en {language}:

Documento 1:
{doc1}

Documento 2:
{doc2}

Lista las 5 diferencias más significativas, explicando:
- Qué cambió
- Por qué es importante
- Impacto potencial del cambio

Responde en {language}."""
            ),
            
            "recommendations": PromptTemplate(
                input_variables=["analysis", "differences", "language"],
                template="""Basándote en este análisis comparativo:

{analysis}

Diferencias clave:
{differences}

Proporciona 5 recomendaciones específicas y accionables en {language} para:
1. Mejorar la coherencia entre documentos
2. Resolver inconsistencias identificadas
3. Aprovechar las mejores prácticas de cada documento
4. Siguientes pasos sugeridos

Responde en {language} de forma práctica y concreta."""
            )
        }
        
        # Prompts específicos por tipo de análisis
        if analysis_type == "legal":
            base_prompts["comparison"].template = """Eres un experto legal. Analiza estos documentos legales en {language} enfocándote en:
1. Cambios en términos y condiciones
2. Modificaciones en cláusulas legales
3. Implicaciones legales de los cambios
4. Riesgos y oportunidades
5. Cumplimiento normativo

Documento 1:
{doc1}

Documento 2:
{doc2}"""
        
        elif analysis_type == "technical":
            base_prompts["comparison"].template = """Eres un experto técnico. Analiza estos documentos técnicos en {language} enfocándote en:
1. Cambios en especificaciones técnicas
2. Modificaciones en arquitectura o diseño
3. Actualizaciones de versiones o dependencias
4. Impacto en la implementación
5. Mejoras o degradaciones de rendimiento

Documento 1:
{doc1}

Documento 2:
{doc2}"""
        
        return base_prompts
    
    async def _create_vectorstore(self, documents: List[Document]) -> FAISS:
        """Crea un vectorstore para búsqueda semántica"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            lambda: FAISS.from_documents(documents, self.embeddings)
        )
    
    async def _run_chain_async(self, chain: LLMChain, inputs: Dict[str, Any]) -> str:
        """Ejecuta una chain de forma asíncrona"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            chain.run,
            inputs
        )
    
    async def _find_unique_sections(
        self,
        vectorstore: FAISS,
        docs1: List[Document],
        docs2: List[Document]
    ) -> Dict[str, List[str]]:
        """Encuentra secciones únicas en cada documento"""
        unique_sections = {"doc1": [], "doc2": []}
        
        # Buscar chunks de doc1 que no tienen similar en doc2
        for doc in docs1[:10]:  # Limitar a los primeros 10 chunks
            similar = vectorstore.similarity_search_with_score(
                doc.page_content,
                k=3,
                filter={"source": "doc2"}
            )
            
            if not similar or similar[0][1] > 0.5:  # Si no hay similares o son muy diferentes
                unique_sections["doc1"].append(doc.page_content[:200] + "...")
        
        # Buscar chunks de doc2 que no tienen similar en doc1
        for doc in docs2[:10]:
            similar = vectorstore.similarity_search_with_score(
                doc.page_content,
                k=3,
                filter={"source": "doc1"}
            )
            
            if not similar or similar[0][1] > 0.5:
                unique_sections["doc2"].append(doc.page_content[:200] + "...")
        
        return unique_sections
    
    async def answer_question(self, question: str, context: str) -> str:
        """Responde preguntas sobre los documentos"""
        qa_prompt = PromptTemplate(
            input_variables=["question", "context"],
            template="""Basándote en el siguiente contexto, responde la pregunta de forma clara y concisa.

Contexto:
{context}

Pregunta: {question}

Respuesta:"""
        )
        
        qa_chain = LLMChain(
            llm=self.llm,
            prompt=qa_prompt,
            callbacks=[self.callback_handler]
        )
        
        return await self._run_chain_async(
            qa_chain,
            {"question": question, "context": context}
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas del handler"""
        return {
            "langchain_metrics": self.callback_handler.metrics,
            "model_name": os.getenv("VLLM_MODEL_NAME"),
            "endpoint": os.getenv("VLLM_ENDPOINT"),
            "timestamp": datetime.now().isoformat()
        }