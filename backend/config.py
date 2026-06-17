"""
Configuration module for TalentMind AI
"""

import os
from pathlib import Path
from typing import Dict, Any

class Config:
    """Application configuration"""
    
    # Base paths
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    MODELS_DIR = BASE_DIR / "models"
    OUTPUTS_DIR = BASE_DIR / "outputs"
    DOCS_DIR = BASE_DIR / "docs"
    
    # Dataset paths
    DATASET_PATH = BASE_DIR.parent / "[PUB] India_runs_data_and_ai_challenge" / "[PUB] India_runs_data_and_ai_challenge" / "India_runs_data_and_ai_challenge"
    CANDIDATES_JSONL = DATASET_PATH / "candidates.jsonl"
    JOB_DESCRIPTION_DOCX = DATASET_PATH / "job_description.docx"
    SAMPLE_CANDIDATES = DATASET_PATH / "sample_candidates.json"
    SAMPLE_SUBMISSION = DATASET_PATH / "sample_submission.csv"
    
    # Model configurations
    EMBEDDING_MODEL = "BAAI/bge-large-en-v1.5"
    FALLBACK_EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"
    EMBEDDING_DIMENSION = 1024
    
    # Scoring weights
    SEMANTIC_WEIGHT = 0.35
    SKILL_WEIGHT = 0.20
    CAREER_GROWTH_WEIGHT = 0.15
    BEHAVIORAL_FIT_WEIGHT = 0.10
    EXPERIENCE_RELEVANCE_WEIGHT = 0.10
    ACHIEVEMENT_IMPACT_WEIGHT = 0.10
    
    # FAISS configuration
    FAISS_INDEX_TYPE = "IndexFlatIP"  # Inner product for cosine similarity
    FAISS_NLIST = 100  # For IVF indexes
    
    # Job requirements (extracted from JD)
    REQUIRED_SKILLS = [
        "embeddings", "retrieval", "ranking", "LLM", "fine-tuning",
        "vector database", "evaluation frameworks", "Python"
    ]
    
    PREFERRED_SKILLS = [
        "LoRA", "QLoRA", "PEFT", "learning-to-rank", "XGBoost",
        "distributed systems", "inference optimization"
    ]
    
    EXPERIENCE_RANGE = (5, 9)  # years
    PREFERRED_LOCATIONS = ["Pune", "Noida", "Hyderabad", "Mumbai", "Delhi NCR"]
    
    # Red flags (explicitly mentioned in JD)
    RED_FLAGS = {
        "title_chasing": "Frequent job switching (<2 years per role)",
        "framework_enthusiast": "Only framework experience without deep systems knowledge",
        "consulting_only": "Career only at consulting firms (TCS, Infosys, Wipro, etc.)",
        "wrong_domain": "Primary expertise in CV/speech/robotics without NLP/IR",
        "closed_source_only": "5+ years only on closed-source without external validation"
    }
    
    # API Configuration
    API_HOST = "0.0.0.0"
    API_PORT = 8000
    API_TITLE = "TalentMind AI API"
    API_VERSION = "1.0.0"
    
    # LLM Configuration (optional)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    
    # Processing configuration
    BATCH_SIZE = 32
    MAX_CANDIDATES = 1000
    TOP_K_RESULTS = 100
    
    # Evaluation metrics
    EVALUATION_METRICS = ["precision_at_k", "recall_at_k", "mrr", "ndcg", "ranking_accuracy"]
    K_VALUES = [5, 10, 20, 50, 100]
    
    @classmethod
    def create_directories(cls) -> None:
        """Create necessary directories if they don't exist"""
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.MODELS_DIR.mkdir(parents=True, exist_ok=True)
        cls.OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        cls.DOCS_DIR.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_scoring_weights(cls) -> Dict[str, float]:
        """Get scoring weights as dictionary"""
        return {
            "semantic": cls.SEMANTIC_WEIGHT,
            "skill": cls.SKILL_WEIGHT,
            "career_growth": cls.CAREER_GROWTH_WEIGHT,
            "behavioral": cls.BEHAVIORAL_FIT_WEIGHT,
            "experience": cls.EXPERIENCE_RELEVANCE_WEIGHT,
            "achievement": cls.ACHIEVEMENT_IMPACT_WEIGHT
        }

# Create directories on import
Config.create_directories()