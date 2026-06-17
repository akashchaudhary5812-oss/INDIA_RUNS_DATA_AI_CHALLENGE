"""
Semantic Matching Module - Uses embeddings for similarity computation
"""

import logging
import pickle
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    import faiss
except ImportError:
    SentenceTransformer = None
    faiss = None

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.models import Candidate, JobDescription
from backend.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SemanticMatcher:
    """Handles semantic matching using embeddings and FAISS"""
    
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or Config.EMBEDDING_MODEL
        self.model = None
        self.faiss_index = None
        self.candidate_ids = []
        self.dimension = Config.EMBEDDING_DIMENSION
        
        # Try to load the model
        self._load_model()
    
    def _load_model(self):
        """Load the sentence transformer model"""
        if SentenceTransformer is None:
            logger.error("sentence-transformers not installed. Install with: pip install sentence-transformers")
            return
        
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            self.dimension = self.model.get_sentence_embedding_dimension()
            logger.info(f"Model loaded successfully. Embedding dimension: {self.dimension}")
        except Exception as e:
            logger.error(f"Failed to load primary model {self.model_name}: {e}")
            
            # Try fallback model
            try:
                logger.info(f"Trying fallback model: {Config.FALLBACK_EMBEDDING_MODEL}")
                self.model = SentenceTransformer(Config.FALLBACK_EMBEDDING_MODEL)
                self.dimension = self.model.get_sentence_embedding_dimension()
                self.model_name = Config.FALLBACK_EMBEDDING_MODEL
                logger.info(f"Fallback model loaded successfully")
            except Exception as e2:
                logger.error(f"Failed to load fallback model: {e2}")
                self.model = None
    
    def encode_text(self, text: str) -> Optional[np.ndarray]:
        """Encode a single text string"""
        if self.model is None:
            logger.error("Model not loaded")
            return None
        
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding
        except Exception as e:
            logger.error(f"Error encoding text: {e}")
            return None
    
    def encode_texts(self, texts: List[str], batch_size: int = 32) -> Optional[np.ndarray]:
        """Encode multiple text strings"""
        if self.model is None:
            logger.error("Model not loaded")
            return None
        
        try:
            embeddings = self.model.encode(texts, batch_size=batch_size, convert_to_numpy=True)
            return embeddings
        except Exception as e:
            logger.error(f"Error encoding texts: {e}")
            return None
    
    def build_faiss_index(self, candidate_embeddings: np.ndarray, candidate_ids: List[str]):
        """Build FAISS index for candidate embeddings"""
        if faiss is None:
            logger.error("FAISS not installed")
            return
        
        try:
            dimension = candidate_embeddings.shape[1]
            
            # Normalize embeddings for cosine similarity
            faiss.normalize_L2(candidate_embeddings)
            
            # Create index
            self.faiss_index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
            self.faiss_index.add(candidate_embeddings.astype(np.float32))
            
            self.candidate_ids = candidate_ids
            logger.info(f"FAISS index built with {len(candidate_ids)} candidates")
            
        except Exception as e:
            logger.error(f"Error building FAISS index: {e}")
    
    def search_similar(self, query_embedding: np.ndarray, k: int = 10) -> Tuple[List[str], np.ndarray]:
        """Search for similar candidates using FAISS"""
        if self.faiss_index is None:
            logger.error("FAISS index not built")
            return [], np.array([])
        
        try:
            # Normalize query embedding
            query_embedding = query_embedding.reshape(1, -1).astype(np.float32)
            faiss.normalize_L2(query_embedding)
            
            # Search
            similarities, indices = self.faiss_index.search(query_embedding, k)
            
            # Get candidate IDs
            result_ids = [self.candidate_ids[i] for i in indices[0] if i < len(self.candidate_ids)]
            result_scores = similarities[0][:len(result_ids)]
            
            return result_ids, result_scores
            
        except Exception as e:
            logger.error(f"Error searching FAISS index: {e}")
            return [], np.array([])
    
    def compute_similarity(self, text1: str, text2: str) -> float:
        """Compute cosine similarity between two texts"""
        if self.model is None:
            return 0.0
        
        try:
            emb1 = self.encode_text(text1)
            emb2 = self.encode_text(text2)
            
            if emb1 is None or emb2 is None:
                return 0.0
            
            # Compute cosine similarity
            similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error computing similarity: {e}")
            return 0.0
    
    def compute_candidate_job_similarity(self, candidate: Candidate, job_description: JobDescription) -> Dict[str, float]:
        """Compute various similarity scores between candidate and job"""
        candidate_text = candidate.get_full_text()
        job_text = job_description.get_full_text()
        
        # Overall similarity
        overall_similarity = self.compute_similarity(candidate_text, job_text)
        
        # Component similarities
        similarities = {
            'overall': overall_similarity,
            'summary': self.compute_similarity(candidate.profile.summary, job_description.raw_text),
            'headline': self.compute_similarity(candidate.profile.headline, job_description.title),
            'skills': self.compute_similarity(
                " ".join(candidate.get_skills_list()),
                " ".join(job_description.get_all_skills())
            )
        }
        
        return similarities
    
    def save_index(self, save_path: Path):
        """Save FAISS index and metadata"""
        if self.faiss_index is None:
            logger.error("No index to save")
            return
        
        try:
            save_path = Path(save_path)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save FAISS index
            faiss.write_index(self.faiss_index, str(save_path))
            
            # Save metadata
            metadata = {
                'candidate_ids': self.candidate_ids,
                'model_name': self.model_name,
                'dimension': self.dimension
            }
            
            metadata_path = save_path.parent / f"{save_path.stem}_metadata.pkl"
            with open(metadata_path, 'wb') as f:
                pickle.dump(metadata, f)
            
            logger.info(f"Index saved to {save_path}")
            
        except Exception as e:
            logger.error(f"Error saving index: {e}")
    
    def load_index(self, load_path: Path):
        """Load FAISS index and metadata"""
        try:
            load_path = Path(load_path)
            
            # Load FAISS index
            self.faiss_index = faiss.read_index(str(load_path))
            
            # Load metadata
            metadata_path = load_path.parent / f"{load_path.stem}_metadata.pkl"
            with open(metadata_path, 'rb') as f:
                metadata = pickle.load(f)
            
            self.candidate_ids = metadata['candidate_ids']
            self.model_name = metadata.get('model_name', self.model_name)
            self.dimension = metadata.get('dimension', self.dimension)
            
            # Reload model if needed
            if self.model is None or self.model_name != metadata.get('model_name'):
                self.model_name = metadata.get('model_name', self.model_name)
                self._load_model()
            
            logger.info(f"Index loaded from {load_path}")
            
        except Exception as e:
            logger.error(f"Error loading index: {e}")
    
    def batch_encode_candidates(self, candidates: List[Candidate], batch_size: int = 32) -> Optional[np.ndarray]:
        """Batch encode candidate profiles"""
        texts = [candidate.get_full_text() for candidate in candidates]
        return self.encode_texts(texts, batch_size)
    
    def compute_skill_similarity(self, candidate_skills: List[str], job_skills: List[str]) -> float:
        """Compute skill overlap similarity"""
        if not job_skills:
            return 0.0
        
        candidate_skills_lower = [skill.lower() for skill in candidate_skills]
        job_skills_lower = [skill.lower() for skill in job_skills]
        
        # Exact matches
        exact_matches = sum(1 for skill in job_skills_lower if skill in candidate_skills_lower)
        
        # Partial matches (substring)
        partial_matches = 0
        for job_skill in job_skills_lower:
            for candidate_skill in candidate_skills_lower:
                if job_skill in candidate_skill or candidate_skill in job_skill:
                    partial_matches += 1
                    break
        
        # Combine scores
        exact_score = exact_matches / len(job_skills_lower) if job_skills_lower else 0
        partial_score = partial_matches / len(job_skills_lower) if job_skills_lower else 0
        
        return (exact_score * 0.7 + partial_score * 0.3)
    
    def compute_experience_similarity(self, candidate_exp: float, job_exp_range: Tuple[int, int]) -> float:
        """Compute experience compatibility score"""
        min_exp, max_exp = job_exp_range
        
        if min_exp <= candidate_exp <= max_exp:
            # Perfect match within range
            return 1.0
        elif candidate_exp < min_exp:
            # Under-experienced - penalize based on gap
            gap = min_exp - candidate_exp
            return max(0, 1.0 - (gap / min_exp))
        else:
            # Over-experienced - slightly penalize but not heavily
            gap = candidate_exp - max_exp
            return max(0.5, 1.0 - (gap / (max_exp * 2)))