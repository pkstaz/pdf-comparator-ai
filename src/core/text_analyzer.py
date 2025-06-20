import difflib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from typing import List, Dict, Tuple

class TextAnalyzer:
    def __init__(self):
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 3),
            stop_words='spanish'
        )
    
    def basic_comparison(self, text1: str, text2: str) -> Dict:
        """Comparación básica línea por línea"""
        lines1 = text1.splitlines()
        lines2 = text2.splitlines()
        
        differ = difflib.unified_diff(lines1, lines2, lineterm='')
        diff_lines = list(differ)
        
        # Calcular ratio de similitud
        matcher = difflib.SequenceMatcher(None, text1, text2)
        similarity_ratio = matcher.ratio()
        
        # Encontrar bloques comunes
        matching_blocks = matcher.get_matching_blocks()
        
        return {
            'similarity_ratio': similarity_ratio,
            'diff_lines': diff_lines,
            'matching_blocks': matching_blocks,
            'added_lines': len([l for l in diff_lines if l.startswith('+')]),
            'removed_lines': len([l for l in diff_lines if l.startswith('-')])
        }
    
    def tfidf_analysis(self, text1: str, text2: str) -> Dict:
        """Análisis TF-IDF para encontrar términos importantes"""
        texts = [text1, text2]
        
        try:
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)
            
            # Similitud coseno
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            # Términos más importantes
            feature_names = self.tfidf_vectorizer.get_feature_names_out()
            
            # Top términos para cada documento
            doc1_tfidf = tfidf_matrix[0].toarray()[0]
            doc2_tfidf = tfidf_matrix[1].toarray()[0]
            
            top_terms_doc1 = self._get_top_terms(doc1_tfidf, feature_names)
            top_terms_doc2 = self._get_top_terms(doc2_tfidf, feature_names)
            
            # Términos únicos
            unique_doc1 = set(top_terms_doc1) - set(top_terms_doc2)
            unique_doc2 = set(top_terms_doc2) - set(top_terms_doc1)
            
            return {
                'cosine_similarity': similarity,
                'top_terms_doc1': top_terms_doc1,
                'top_terms_doc2': top_terms_doc2,
                'unique_terms_doc1': list(unique_doc1),
                'unique_terms_doc2': list(unique_doc2)
            }
        except Exception as e:
            return {
                'error': str(e),
                'cosine_similarity': 0.0
            }
    
    def _get_top_terms(self, tfidf_scores: np.ndarray, feature_names: np.ndarray, top_n: int = 20) -> List[str]:
        """Obtiene los términos más importantes"""
        top_indices = np.argsort(tfidf_scores)[-top_n:][::-1]
        return [feature_names[i] for i in top_indices if tfidf_scores[i] > 0]
    
    def structural_similarity(self, structure1: Dict, structure2: Dict) -> float:
        """Calcula similitud estructural entre documentos"""
        score = 0.0
        total_weight = 0.0
        
        # Comparar títulos
        if structure1['titles'] and structure2['titles']:
            titles1 = [t['text'] for t in structure1['titles']]
            titles2 = [t['text'] for t in structure2['titles']]
            title_sim = self._sequence_similarity(titles1, titles2)
            score += title_sim * 0.3
            total_weight += 0.3
        
        # Comparar secciones
        if structure1['sections'] and structure2['sections']:
            sections1 = [s['text'] for s in structure1['sections']]
            sections2 = [s['text'] for s in structure2['sections']]
            section_sim = self._sequence_similarity(sections1, sections2)
            score += section_sim * 0.5
            total_weight += 0.5
        
        # Comparar estructura de listas
        if structure1['lists'] and structure2['lists']:
            list_density1 = len(structure1['lists']) / max(len(structure1['titles']) + len(structure1['sections']), 1)
            list_density2 = len(structure2['lists']) / max(len(structure2['titles']) + len(structure2['sections']), 1)
            list_sim = 1 - abs(list_density1 - list_density2)
            score += list_sim * 0.2
            total_weight += 0.2
        
        return score / total_weight if total_weight > 0 else 0.0
    
    def _sequence_similarity(self, seq1: List[str], seq2: List[str]) -> float:
        """Calcula similitud entre secuencias de texto"""
        matcher = difflib.SequenceMatcher(None, seq1, seq2)
        return matcher.ratio()