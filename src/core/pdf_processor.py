import PyPDF2
import pdfplumber
from typing import List, Dict, Tuple
import re
from dataclasses import dataclass

@dataclass
class PDFContent:
    text: str
    pages: List[str]
    metadata: Dict
    structure: Dict

class PDFProcessor:
    def __init__(self):
        self.structure_patterns = {
            'main_titles': [
                r'^[A-Z\s]+$',  # TODO EN MAYÚSCULAS
                r'^CAPÍTULO\s+[IVX\d]+',
                r'^SECCIÓN\s+[IVX\d]+',
                r'^CHAPTER\s+[IVX\d]+',
            ],
            'numbered_sections': [
                r'^\d+\.\s+',
                r'^\d+\.\d+\s+',
                r'^\d+\.\d+\.\d+\s+',
                r'^[a-zA-Z]\)\s+',
                r'^\(\d+\)\s+',
            ],
            'list_items': [
                r'^[•\-\*→✓]\s+',
                r'^\s*[•\-\*→✓]\s+',
            ]
        }
    
    def extract_text(self, pdf_path: str) -> PDFContent:
        """Extrae texto y estructura de un PDF"""
        text = ""
        pages = []
        metadata = {}
        structure = {
            'titles': [],
            'sections': [],
            'lists': [],
            'toc': []
        }
        
        with pdfplumber.open(pdf_path) as pdf:
            metadata = pdf.metadata or {}
            
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text() or ""
                pages.append(page_text)
                text += page_text + "\n"
                
                # Analizar estructura
                self._analyze_page_structure(page_text, i, structure)
        
        return PDFContent(
            text=text,
            pages=pages,
            metadata=metadata,
            structure=structure
        )
    
    def _analyze_page_structure(self, text: str, page_num: int, structure: Dict):
        """Analiza la estructura de una página"""
        lines = text.split('\n')
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Detectar títulos principales
            for pattern in self.structure_patterns['main_titles']:
                if re.match(pattern, line):
                    structure['titles'].append({
                        'text': line,
                        'page': page_num,
                        'line': line_num,
                        'type': 'main_title'
                    })
                    break
            
            # Detectar secciones numeradas
            for pattern in self.structure_patterns['numbered_sections']:
                if re.match(pattern, line):
                    structure['sections'].append({
                        'text': line,
                        'page': page_num,
                        'line': line_num,
                        'level': line.count('.')
                    })
                    break
            
            # Detectar elementos de lista
            for pattern in self.structure_patterns['list_items']:
                if re.match(pattern, line):
                    structure['lists'].append({
                        'text': line,
                        'page': page_num,
                        'line': line_num
                    })
                    break
            
            # Detectar posible tabla de contenidos
            if '....' in line or '----' in line:
                structure['toc'].append({
                    'text': line,
                    'page': page_num
                })