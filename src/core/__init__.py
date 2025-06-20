"""
Core functionality for PDF processing and analysis
"""

from .pdf_processor import PDFProcessor, PDFContent
from .text_analyzer import TextAnalyzer
from .embeddings import EmbeddingAnalyzer
from .langchain_handler import LangChainHandler, DocumentComparator

__all__ = [
    "PDFProcessor",
    "PDFContent",
    "TextAnalyzer",
    "EmbeddingAnalyzer",
    "LangChainHandler",
    "DocumentComparator",
]

# Version of the core module
__version__ = "2.0.0"