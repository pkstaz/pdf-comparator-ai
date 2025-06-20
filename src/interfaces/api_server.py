from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
import time
from datetime import datetime
import logging
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi.responses import PlainTextResponse

# Local imports
from src.core.pdf_processor import PDFProcessor
from src.core.text_analyzer import TextAnalyzer
from src.core.embeddings import EmbeddingAnalyzer
from src.core.langchain_handler import LangChainHandler
from src.utils.config import get_settings, setup_logging

# Initialize settings and logging
settings = get_settings()
setup_logging(settings)
logger = logging.getLogger(__name__)

# Prometheus metrics
request_count = Counter('pdf_comparator_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
request_duration = Histogram('pdf_comparator_request_duration_seconds', 'Request duration', ['method', 'endpoint'])
active_requests = Gauge('pdf_comparator_active_requests', 'Active requests')
pdf_processing_duration = Histogram('pdf_processing_duration_seconds', 'PDF processing duration')
analysis_duration = Histogram('pdf_analysis_duration_seconds', 'Analysis duration', ['analysis_type'])

# Initialize FastAPI app
app = FastAPI(
    title="PDF Comparator AI API",
    description="Sistema inteligente para comparar documentos PDF usando vLLM y LangChain",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
pdf_processor = PDFProcessor()
text_analyzer = TextAnalyzer()
embedding_analyzer = EmbeddingAnalyzer()
langchain_handler = None

# Models
class ComparisonRequest(BaseModel):
    analysis_types: List[str] = Field(
        ["basic", "semantic", "ai"],
        description="Types of analysis to perform"
    )
    domain: str = Field("general", description="Domain for specialized analysis")
    language: str = Field("es", description="Language for analysis")
    use_cache: bool = Field(True, description="Use cached results if available")

class ComparisonResponse(BaseModel):
    request_id: str
    status: str
    results: Dict[str, Any]
    execution_time: float
    metadata: Dict[str, Any]

class ChatMessage(BaseModel):
    message: str
    context: Optional[Dict] = None
    session_id: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    vllm_status: str
    redis_status: str

# Middleware
@app.middleware("http")
async def metrics_middleware(request, call_next):
    """Middleware para métricas"""
    start_time = time.time()
    active_requests.inc()
    
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        
        # Record metrics
        request_count.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        
        request_duration.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)
        
        return response
    finally:
        active_requests.dec()

# Dependencies
async def get_langchain_handler():
    """Dependency para obtener LangChain handler"""
    global langchain_handler
    if langchain_handler is None:
        langchain_handler = LangChainHandler(settings.get_langchain_config())
    return langchain_handler

# Endpoints
@app.get("/", tags=["General"])
async def root():
    """Root endpoint"""
    return {
        "service": "PDF Comparator AI",
        "version": "2.0.0",
        "model": settings.vllm_model_name,
        "endpoints": {
            "/api/docs": "API documentation",
            "/health": "Health check",
            "/ready": "Readiness check",
            "/metrics": "Prometheus metrics",
            "/api/v1/compare": "Compare two PDFs",
            "/api/v1/chat": "Chat interface",
            "/api/v1/analyze": "Analyze single PDF"
        }
    }

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "vllm_status": "unknown",
        "redis_status": "unknown"
    }
    
    # Check vLLM
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.vllm_endpoint}/health", timeout=5.0)
            health_status["vllm_status"] = "healthy" if response.status_code == 200 else "unhealthy"
    except Exception as e:
        health_status["vllm_status"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Redis
    try:
        import redis.asyncio as redis
        r = redis.from_url(settings.redis_url)
        await r.ping()
        health_status["redis_status"] = "healthy"
        await r.close()
    except Exception as e:
        health_status["redis_status"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status

@app.get("/ready", tags=["Health"])
async def readiness_check():
    """Readiness check endpoint"""
    # Check if all services are ready
    health = await health_check()
    if health["status"] != "healthy":
        raise HTTPException(status_code=503, detail="Service not ready")
    return {"status": "ready"}

@app.get("/metrics", response_class=PlainTextResponse, tags=["Monitoring"])
async def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest()

@app.post("/api/v1/compare", response_model=ComparisonResponse, tags=["Analysis"])
async def compare_pdfs(
    background_tasks: BackgroundTasks,
    pdf1: UploadFile = File(...),
    pdf2: UploadFile = File(...),
    request: ComparisonRequest = ComparisonRequest(),
    handler: LangChainHandler = Depends(get_langchain_handler)
):
    """Compare two PDF documents"""
    start_time = time.time()
    request_id = f"req_{int(time.time() * 1000)}"
    
    logger.info(f"Starting comparison request {request_id}")
    
    try:
        # Validate PDFs
        if pdf1.content_type != "application/pdf" or pdf2.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="Both files must be PDFs")
        
        # Check file size
        pdf1_size = len(await pdf1.read())
        pdf2_size = len(await pdf2.read())
        await pdf1.seek(0)
        await pdf2.seek(0)
        
        max_size_bytes = settings.max_pdf_size_mb * 1024 * 1024
        if pdf1_size > max_size_bytes or pdf2_size > max_size_bytes:
            raise HTTPException(
                status_code=400,
                detail=f"PDF size exceeds maximum of {settings.max_pdf_size_mb}MB"
            )
        
        # Process PDFs
        with pdf_processing_duration.time():
            content1 = pdf_processor.extract_text(pdf1.file)
            content2 = pdf_processor.extract_text(pdf2.file)
        
        results = {}
        
        # Basic analysis
        if "basic" in request.analysis_types:
            with analysis_duration.labels(analysis_type="basic").time():
                results["basic"] = text_analyzer.basic_comparison(content1.text, content2.text)
        
        # Semantic analysis
        if "semantic" in request.analysis_types and settings.enable_semantic_analysis:
            with analysis_duration.labels(analysis_type="semantic").time():
                results["semantic"] = embedding_analyzer.semantic_comparison(content1.text, content2.text)
        
        # AI analysis with LangChain
        if "ai" in request.analysis_types:
            with analysis_duration.labels(analysis_type="ai").time():
                results["ai"] = await handler.compare_documents_intelligent(
                    content1.text,
                    content2.text,
                    request.domain,
                    request.language
                )
        
        # Structural analysis
        if "structural" in request.analysis_types and settings.enable_structural_analysis:
            with analysis_duration.labels(analysis_type="structural").time():
                results["structural"] = text_analyzer.structural_similarity(
                    content1.structure,
                    content2.structure
                )
        
        execution_time = time.time() - start_time
        
        # Background task to cache results
        if request.use_cache and settings.enable_caching:
            background_tasks.add_task(cache_results, request_id, results)
        
        return ComparisonResponse(
            request_id=request_id,
            status="success",
            results=results,
            execution_time=execution_time,
            metadata={
                "pdf1_pages": len(content1.pages),
                "pdf2_pages": len(content2.pages),
                "analysis_types": request.analysis_types,
                "language": request.language,
                "model": settings.vllm_model_name
            }
        )
        
    except Exception as e:
        logger.error(f"Error in comparison request {request_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/chat", tags=["Chat"])
async def chat(
    message: ChatMessage,
    handler: LangChainHandler = Depends(get_langchain_handler)
):
    """Chat interface for document questions"""
    try:
        # Get context from session or message
        context = message.context or {}
        
        # Generate response using LangChain
        response = await handler.answer_question(
            message.message,
            context.get("document_content", "No document loaded")
        )
        
        return {
            "response": response,
            "session_id": message.session_id or f"session_{int(time.time())}",
            "suggestions": [
                "¿Cuáles son las principales diferencias?",
                "¿Qué recomiendas hacer?",
                "Explica los cambios más importantes"
            ]
        }
    except Exception as e:
        logger.error(f"Error in chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/analyze", tags=["Analysis"])
async def analyze_pdf(
    pdf: UploadFile = File(...),
    analysis_type: str = "summary"
):
    """Analyze a single PDF document"""
    try:
        if pdf.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="File must be a PDF")
        
        content = pdf_processor.extract_text(pdf.file)
        
        # TODO: Implement single PDF analysis
        return {
            "status": "success",
            "pages": len(content.pages),
            "structure": content.structure,
            "message": "Single PDF analysis coming soon"
        }
        
    except Exception as e:
        logger.error(f"Error analyzing PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Helper functions
async def cache_results(request_id: str, results: Dict[str, Any]):
    """Cache analysis results in Redis"""
    try:
        import redis.asyncio as redis
        import json
        
        r = redis.from_url(settings.redis_url)
        await r.setex(
            f"results:{request_id}",
            3600,  # 1 hour TTL
            json.dumps(results)
        )
        await r.close()
        logger.info(f"Cached results for {request_id}")
    except Exception as e:
        logger.error(f"Error caching results: {str(e)}")

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting PDF Comparator AI API")
    
    # Validate configuration
    if not settings.validate_config():
        logger.error("Invalid configuration, exiting")
        raise RuntimeError("Invalid configuration")
    
    # Initialize LangChain handler
    global langchain_handler
    langchain_handler = LangChainHandler(settings.get_langchain_config())
    
    logger.info(f"API started successfully on {settings.host}:{settings.port}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down PDF Comparator AI API")