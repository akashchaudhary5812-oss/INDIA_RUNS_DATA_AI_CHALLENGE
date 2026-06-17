"""
FastAPI Backend for TalentMind AI
"""

import sys
from pathlib import Path
from typing import List, Optional
import logging

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import uvicorn

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.pipeline import TalentMindPipeline
from backend.models import Candidate, CandidateScore, JobDescription

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="TalentMind AI API",
    description="AI Recruitment Intelligence System API",
    version="1.0.0"
)

# Global pipeline instance
pipeline: Optional[TalentMindPipeline] = None


class ScoringRequest(BaseModel):
    """Request model for candidate scoring"""
    limit: Optional[int] = None
    use_sample_data: bool = False


class JobDescriptionRequest(BaseModel):
    """Request model for job description"""
    job_description: str


class CandidateComparisonRequest(BaseModel):
    """Request model for candidate comparison"""
    candidate_a_id: str
    candidate_b_id: str


@app.on_event("startup")
async def startup_event():
    """Initialize pipeline on startup"""
    global pipeline
    logger.info("Initializing TalentMind AI Pipeline...")
    pipeline = TalentMindPipeline()
    # Pre-load job description
    try:
        pipeline.load_job_description()
        logger.info("Job description loaded successfully")
    except Exception as e:
        logger.warning(f"Could not load job description: {e}")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "TalentMind AI API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.post("/score-candidates")
async def score_candidates(request: ScoringRequest, background_tasks: BackgroundTasks):
    """Score candidates and return ranked results"""
    try:
        if pipeline is None:
            raise HTTPException(status_code=500, detail="Pipeline not initialized")
        
        # Load candidates
        if request.use_sample_data:
            candidates = pipeline.data_loader.load_candidates_from_json(
                pipeline.data_loader.job_description_path.parent / 'sample_candidates.json',
                limit=request.limit
            )
        else:
            candidates = pipeline.data_loader.load_candidates_from_jsonl(limit=request.limit)
        
        if not candidates:
            raise HTTPException(status_code=404, detail="No candidates found")
        
        # Ensure job description is loaded
        if pipeline.job_description is None:
            pipeline.load_job_description()
        
        # Initialize scoring engine
        pipeline.initialize_scoring_engine()
        
        # Score candidates
        scored_candidates = pipeline.scoring_engine.score_candidates(candidates)
        
        # Convert to response format
        results = [
            {
                "candidate_id": score.candidate_id,
                "candidate_name": score.candidate_name,
                "final_score": score.final_score,
                "rank": score.rank,
                "recommendation_reason": score.recommendation_reason,
                "strengths": score.strengths,
                "risks": score.risks,
                "missing_skills": score.missing_skills
            }
            for score in scored_candidates
        ]
        
        return {
            "status": "success",
            "total_candidates": len(results),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error scoring candidates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/load-job-description")
async def load_job_description(request: JobDescriptionRequest):
    """Load and parse a new job description"""
    try:
        if pipeline is None:
            raise HTTPException(status_code=500, detail="Pipeline not initialized")
        
        job_description = pipeline.job_agent.parse_job_description(request.job_description)
        pipeline.job_description = job_description
        
        return {
            "status": "success",
            "job_title": job_description.title,
            "company": job_description.company,
            "required_skills": job_description.requirements.required_skills,
            "preferred_skills": job_description.requirements.preferred_skills
        }
        
    except Exception as e:
        logger.error(f"Error loading job description: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/candidates/{candidate_id}")
async def get_candidate_details(candidate_id: str):
    """Get detailed information about a specific candidate"""
    try:
        # This would require loading all candidates and finding the specific one
        # For now, return a placeholder
        return {
            "candidate_id": candidate_id,
            "message": "Detailed candidate retrieval not yet implemented"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def start_server(host: str = "0.0.0.0", port: int = 8000):
    """Start the FastAPI server"""
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    start_server()