#!/usr/bin/env python3
"""
Main entry point for TalentMind AI
"""

import sys
import argparse
import logging
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.pipeline import TalentMindPipeline
from backend.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='TalentMind AI - AI Recruitment Intelligence System')
    parser.add_argument('--limit', type=int, default=None, 
                       help='Limit number of candidates to process (for testing)')
    parser.add_argument('--output', type=str, default=None,
                       help='Output file path for results')
    parser.add_argument('--detailed', action='store_true',
                       help='Save detailed JSON results in addition to CSV')
    
    args = parser.parse_args()
    
    try:
        # Create pipeline
        pipeline = TalentMindPipeline()
        
        # Run pipeline
        logger.info("Starting TalentMind AI scoring pipeline...")
        scored_candidates = pipeline.run_pipeline(limit=args.limit)
        
        # Save results
        output_path = Path(args.output) if args.output else None
        pipeline.save_results(scored_candidates, output_path)
        
        if args.detailed:
            pipeline.save_detailed_results(scored_candidates)
        
        # Generate summary
        summary = pipeline.generate_summary_report(scored_candidates)
        print(summary)
        
        logger.info("Pipeline completed successfully!")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()