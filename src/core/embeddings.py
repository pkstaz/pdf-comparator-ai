from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict, Tuple
import torch

class EmbeddingAnalyzer:
    def __init__(self, model_name: str = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'):
        self.model = SentenceTransformer(model_name)
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model.to(self.device)
    
    def semantic_comparison(self, text1: str, text2: str, chunk_size: int = 512) -> Dict:
        """Comparación semántica usando embeddings"""
        # Dividir textos en chunks
        chunks1 = self._create_chunks(text1, chunk_size)
        chunks2 = self._create_chunks(text2, chunk_size)
        
        # Generar embeddings
        embeddings1 = self.model.encode(chunks1, convert_to_tensor=True)
        embeddings2 = self.model.encode(chunks2, convert_to_tensor=True)
        
        # Calcular similitud general
        overall_similarity = self._calculate_overall_similarity(embeddings1, embeddings2)
        
        # Encontrar pares más similares
        similar_pairs = self._find_similar_pairs(chunks1, chunks2, embeddings1, embeddings2)
        
        # Encontrar chunks únicos
        unique_chunks = self._find_unique_chunks(chunks1, chunks2, embeddings1, embeddings2)
        
        return {
            'overall_similarity': overall_similarity,
            'num_chunks_doc1': len(chunks1),
            'num_chunks_doc2': len(chunks2),
            'similar_pairs': similar_pairs[:10],  # Top 10 pares
            'unique_chunks_doc1': unique_chunks['doc1'][:5],
            'unique_chunks_doc2': unique_chunks['doc2'][:5]
        }
    
    def _create_chunks(self, text: str, chunk_size: int) -> List[str]:
        """Divide el texto en chunks con overlap"""
        words = text.split()
        chunks = []
        overlap = chunk_size // 4
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if len(chunk.strip()) > 50:  # Mínimo 50 caracteres
                chunks.append(chunk)
        
        return chunks
    
    def _calculate_overall_similarity(self, embeddings1: torch.Tensor, embeddings2: torch.Tensor) -> float:
        """Calcula similitud general entre conjuntos de embeddings"""
        # Promedio de embeddings
        mean_emb1 = embeddings1.mean(dim=0)
        mean_emb2 = embeddings2.mean(dim=0)
        
        # Similitud coseno
        similarity = torch.nn.functional.cosine_similarity(
            mean_emb1.unsqueeze(0),
            mean_emb2.unsqueeze(0)
        ).item()
        
        return similarity
    
    def _find_similar_pairs(self, chunks1: List[str], chunks2: List[str], 
                          embeddings1: torch.Tensor, embeddings2: torch.Tensor) -> List[Dict]:
        """Encuentra los pares de chunks más similares"""
        # Calcular matriz de similitud
        similarity_matrix = torch.nn.functional.cosine_similarity(
            embeddings1.unsqueeze(1),
            embeddings2.unsqueeze(0),
            dim=2
        )
        
        # Encontrar pares más similares
        pairs = []
        for i in range(len(chunks1)):
            for j in range(len(chunks2)):
                similarity = similarity_matrix[i, j].item()
                if similarity > 0.7:  # Umbral de similitud
                    pairs.append({
                        'chunk1': chunks1[i][:100] + '...',
                        'chunk2': chunks2[j][:100] + '...',
                        'similarity': similarity,
                        'index1': i,
                        'index2': j
                    })
        
        # Ordenar por similitud
        pairs.sort(key=lambda x: x['similarity'], reverse=True)
        
        return pairs
    
    def _find_unique_chunks(self, chunks1: List[str], chunks2: List[str],
                          embeddings1: torch.Tensor, embeddings2: torch.Tensor) -> Dict:
        """Encuentra chunks únicos en cada documento"""
        # Calcular similitud máxima para cada chunk
        similarity_matrix = torch.nn.functional.cosine_similarity(
            embeddings1.unsqueeze(1),
            embeddings2.unsqueeze(0),
            dim=2
        )
        
        # Chunks únicos en doc1
        max_sim_doc1 = similarity_matrix.max(dim=1)[0]
        unique_indices_doc1 = torch.where(max_sim_doc1 < 0.5)[0]
        unique_doc1 = [chunks1[i] for i in unique_indices_doc1]
        
        # Chunks únicos en doc2
        max_sim_doc2 = similarity_matrix.max(dim=0)[0]
        unique_indices_doc2 = torch.where(max_sim_doc2 < 0.5)[0]
        unique_doc2 = [chunks2[i] for i in unique_indices_doc2]
        
        return {
            'doc1': unique_doc1,
            'doc2': unique_doc2
        }