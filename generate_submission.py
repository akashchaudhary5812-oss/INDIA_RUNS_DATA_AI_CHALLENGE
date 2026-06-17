#!/usr/bin/env python3
"""
Generate final submission file for hackathon
"""

import sys
from pathlib import Path
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.pipeline import TalentMindPipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Generate the final submission file"""
    logger.info("Generating final submission file...")
    
    # Create pipeline
    pipeline = TalentMindPipeline()
    
    # Load job description (manual extraction from the DOCX)
    jd_text = """
    Job Description: Senior AI Engineer — Founding Team
    Company: Redrob AI (Series A AI-native talent intelligence platform)
    Location: Pune/Noida, India (Hybrid — flexible cadence)
    Employment Type: Full-time
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
    
    # Parse job description
    logger.info("Parsing job description...")
    job_description = pipeline.job_agent.parse_job_description(jd_text)
    pipeline.job_description = job_description
    logger.info(f"Job: {job_description.title}")
    logger.info(f"Required Skills: {len(job_description.requirements.required_skills)}")
    
    # Load sample candidates (we'll use the sample file as the full dataset)
    logger.info("Loading candidates...")
    candidates = pipeline.data_loader.load_candidates_from_json(
        pipeline.data_loader.job_description_path.parent / 'sample_candidates.json'
    )
    logger.info(f"Loaded {len(candidates)} candidates")
    
    # Initialize scoring engine
    logger.info("Initializing scoring engine...")
    pipeline.initialize_scoring_engine()
    
    # Score all candidates
    logger.info("Scoring candidates...")
    scored_candidates = pipeline.scoring_engine.score_candidates(candidates)
    logger.info(f"Completed scoring. Top candidate: {scored_candidates[0].candidate_name} (Score: {scored_candidates[0].final_score:.1f})")
    
    # Save results in the required format
    logger.info("Saving submission file...")
    output_path = Path(__file__).parent / "outputs" / "ranked_candidates.csv"
    pipeline.save_results(scored_candidates, output_path)
    
    # Also save detailed results
    detailed_output_path = Path(__file__).parent / "outputs" / "detailed_results.json"
    pipeline.save_detailed_results(scored_candidates, detailed_output_path)
    
    # Generate summary report
    summary = pipeline.generate_summary_report(scored_candidates)
    
    # Save summary to file
    summary_path = Path(__file__).parent / "outputs" / "scoring_summary.txt"
    with open(summary_path, 'w') as f:
        f.write(summary)
    
    logger.info(f"Submission file saved to {output_path}")
    logger.info(f"Detailed results saved to {detailed_output_path}")
    logger.info(f"Summary report saved to {summary_path}")
    
    print("\n" + "="*70)
    print("FINAL SUBMISSION GENERATED SUCCESSFULLY")
    print("="*70)
    print("\nFiles created:")
    print(f"1. ranked_candidates.csv - Main submission file")
    print(f"2. detailed_results.json - Detailed scoring results")
    print(f"3. scoring_summary.txt - Summary report")
    print("\n" + summary)
    
    return output_path


if __name__ == "__main__":
    main()