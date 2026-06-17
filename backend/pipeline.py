"""
Main Pipeline - Orchestrates the complete TalentMind AI scoring workflow
"""

import logging
import json
import sys
from pathlib import Path
from typing import List, Optional
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.data_loader import DataLoader
from backend.models import Candidate, CandidateScore, JobDescription
from backend.agents import JobUnderstandingAgent
from backend.scoring_engine import ScoringEngine
from backend.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TalentMindPipeline:
    """Main pipeline for TalentMind AI scoring system"""
    
    def __init__(self, data_path: Optional[Path] = None):
        self.data_loader = DataLoader(data_path)
        self.job_agent = JobUnderstandingAgent()
        self.scoring_engine: Optional[ScoringEngine] = None
        self.job_description: Optional[JobDescription] = None
        
    def load_job_description(self, jd_text: Optional[str] = None) -> JobDescription:
        """Load and parse job description"""
        if jd_text is None:
            jd_text = self.data_loader.load_job_description()
        
        if not jd_text:
            raise ValueError("Job description text is required")
        
        self.job_description = self.job_agent.parse_job_description(jd_text)
        logger.info(f"Job description loaded: {self.job_description.title}")
        
        return self.job_description
    
    def load_candidates(self, limit: Optional[int] = None) -> List[Candidate]:
        """Load candidate data"""
        candidates = self.data_loader.load_candidates_from_jsonl(limit=limit)
        
        if not candidates:
            # Try loading from sample file
            logger.warning("No candidates loaded from JSONL, trying sample file...")
            candidates = self.data_loader.load_candidates_from_json(
                Config.SAMPLE_CANDIDATES, limit=limit
            )
        
        logger.info(f"Loaded {len(candidates)} candidates")
        return candidates
    
    def initialize_scoring_engine(self):
        """Initialize the scoring engine with job description"""
        if self.job_description is None:
            raise ValueError("Job description must be loaded first")
        
        self.scoring_engine = ScoringEngine(self.job_description)
        logger.info("Scoring engine initialized")
    
    def run_pipeline(self, limit: Optional[int] = None) -> List[CandidateScore]:
        """Run the complete pipeline"""
        logger.info("="*50)
        logger.info("Starting TalentMind AI Pipeline")
        logger.info("="*50)
        
        # Step 1: Load job description
        logger.info("Step 1: Loading job description...")
        self.load_job_description()
        
        # Step 2: Load candidates
        logger.info("Step 2: Loading candidates...")
        candidates = self.load_candidates(limit)
        
        if not candidates:
            raise ValueError("No candidates loaded. Check data source.")
        
        # Step 3: Initialize scoring engine
        logger.info("Step 3: Initializing scoring engine...")
        self.initialize_scoring_engine()
        
        # Step 4: Score candidates
        logger.info("Step 4: Scoring candidates...")
        scored_candidates = self.scoring_engine.score_candidates(candidates)
        
        logger.info("="*50)
        logger.info("Pipeline completed successfully")
        logger.info(f"Top candidate: {scored_candidates[0].candidate_name} (Score: {scored_candidates[0].final_score:.1f})")
        logger.info("="*50)
        
        return scored_candidates
    
    def save_results(self, scored_candidates: List[CandidateScore], 
                    output_path: Optional[Path] = None) -> Path:
        """Save scoring results to CSV"""
        if output_path is None:
            output_path = Config.OUTPUTS_DIR / "ranked_candidates.csv"
        
        # Prepare data for CSV
        results_data = []
        for score in scored_candidates:
            results_data.append({
                'candidate_id': score.candidate_id,
                'candidate_name': score.candidate_name,
                'final_score': score.final_score,
                'semantic_score': score.components.semantic_score,
                'skill_score': score.components.skill_score,
                'behavioral_score': score.components.behavioral_score,
                'career_score': score.components.career_growth_score,
                'achievement_score': score.components.achievement_score,
                'rank': score.rank,
                'recommendation_reason': score.recommendation_reason
            })
        
        # Create DataFrame and save
        df = pd.DataFrame(results_data)
        df.to_csv(output_path, index=False)
        
        logger.info(f"Results saved to {output_path}")
        return output_path
    
    def save_detailed_results(self, scored_candidates: List[CandidateScore],
                            output_path: Optional[Path] = None) -> Path:
        """Save detailed results with all scores and explanations"""
        if output_path is None:
            output_path = Config.OUTPUTS_DIR / "detailed_ranked_candidates.json"
        
        # Convert to dict
        results = [score.dict() for score in scored_candidates]
        
        # Save to JSON
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Detailed results saved to {output_path}")
        return output_path
    
    def generate_summary_report(self, scored_candidates: List[CandidateScore]) -> str:
        """Generate a summary report of the scoring results"""
        
        total_candidates = len(scored_candidates)
        avg_score = sum(score.final_score for score in scored_candidates) / total_candidates
        top_score = scored_candidates[0].final_score
        bottom_score = scored_candidates[-1].final_score
        
        # Score distribution
        high_score = sum(1 for score in scored_candidates if score.final_score >= 70)
        medium_score = sum(1 for score in scored_candidates if 50 <= score.final_score < 70)
        low_score = sum(1 for score in scored_candidates if score.final_score < 50)
        
        report = f"""
TalentMind AI Scoring Summary Report
{'='*50}

Total Candidates Scored: {total_candidates}
Average Score: {avg_score:.2f}
Top Score: {top_score:.2f}
Bottom Score: {bottom_score:.2f}

Score Distribution:
- High Score (70+): {high_score} ({high_score/total_candidates*100:.1f}%)
- Medium Score (50-70): {medium_score} ({medium_score/total_candidates*100:.1f}%)
- Low Score (<50): {low_score} ({low_score/total_candidates*100:.1f}%)

Top 5 Candidates:
"""
        
        for i, score in enumerate(scored_candidates[:5], 1):
            report += f"\n{i}. {score.candidate_name} - Score: {score.final_score:.1f}\n"
            report += f"   {score.recommendation_reason}\n"
        
        return report