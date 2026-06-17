#!/usr/bin/env python3
"""
Test script for TalentMind AI pipeline
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.pipeline import TalentMindPipeline
from backend.config import Config

def test_pipeline():
    """Test the pipeline with sample data"""
    print("Testing TalentMind AI Pipeline...")
    print("="*50)
    
    # Create pipeline
    pipeline = TalentMindPipeline()
    
    # Load and parse job description
    print("Loading job description...")
    jd_text = pipeline.data_loader.load_job_description()
    if not jd_text:
        print("Error: Could not load job description")
        print("Trying manual extraction...")
        # Use the job description we extracted earlier
        jd_text = """
        Job Description: Senior AI Engineer — Founding Team
        Company: Redrob AI (Series A AI-native talent intelligence platform)
        Location: Pune/Noida, India (Hybrid — flexible cadence)
        Experience Required: 5–9 years
        
        We need someone who is simultaneously comfortable with:
        - Deep technical depth in modern ML systems — embeddings, retrieval, ranking, LLMs, fine-tuning
        - Scrappy product-engineering attitude — willing to ship a working ranker in a week
        
        Required Skills:
        - Production experience with embeddings-based retrieval systems
        - Production experience with vector databases or hybrid search infrastructure
        - Strong Python
        - Hands-on experience designing evaluation frameworks for ranking systems
        
        Preferred Skills:
        - LLM fine-tuning experience (LoRA, QLoRA, PEFT)
        - Experience with learning-to-rank models
        - Prior exposure to HR-tech, recruiting tech, or marketplace products
        """
    
    job_description = pipeline.job_agent.parse_job_description(jd_text)
    print(f"Job: {job_description.title}")
    print(f"Company: {job_description.company}")
    print(f"Required Skills: {len(job_description.requirements.required_skills)}")
    print(f"Preferred Skills: {len(job_description.requirements.preferred_skills)}")
    print()
    
    # Load sample candidates
    print("Loading sample candidates...")
    candidates = pipeline.data_loader.load_candidates_from_json(
        Config.SAMPLE_CANDIDATES, limit=10
    )
    print(f"Loaded {len(candidates)} candidates")
    print()
    
    # Initialize scoring engine
    print("Initializing scoring engine...")
    pipeline.job_description = job_description
    pipeline.initialize_scoring_engine()
    print()
    
    # Score candidates
    print("Scoring candidates...")
    scored_candidates = pipeline.scoring_engine.score_candidates(candidates)
    print()
    
    # Display results
    print("Top 5 Candidates:")
    print("="*50)
    for i, score in enumerate(scored_candidates[:5], 1):
        print(f"{i}. {score.candidate_name} - Score: {score.final_score:.1f}")
        print(f"   Rank: {score.rank}")
        print(f"   Reason: {score.recommendation_reason}")
        print()
    
    print("Test completed successfully!")
    return scored_candidates

if __name__ == "__main__":
    test_pipeline()
