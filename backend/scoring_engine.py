"""
Scoring Engine - Main scoring pipeline that combines all analysis components
"""

import logging
from typing import Dict, List, Optional, Tuple
import numpy as np

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.models import Candidate, CandidateScore, ScoreComponents, JobDescription, JobRequirements
from backend.semantic_matching import SemanticMatcher
from backend.career_intelligence import CareerTrajectoryAnalyzer
from backend.behavioral_intelligence import BehavioralAnalyzer
from backend.agents.explainable_ranking_agent import ExplainableRankingAgent
from backend.agents.candidate_understanding_agent import CandidateUnderstandingAgent
from backend.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScoringEngine:
    """Main scoring engine that orchestrates all scoring components"""
    
    def __init__(self, job_description: JobDescription):
        self.job_description = job_description
        self.job_requirements = job_description.requirements
        
        # Initialize components
        self.semantic_matcher = SemanticMatcher()
        self.career_analyzer = CareerTrajectoryAnalyzer()
        self.behavioral_analyzer = BehavioralAnalyzer()
        self.explainability_agent = ExplainableRankingAgent()
        self.candidate_agent = CandidateUnderstandingAgent()
        
        # Get scoring weights
        self.weights = Config.get_scoring_weights()
        
        logger.info("Scoring Engine initialized")
    
    def score_candidate(self, candidate: Candidate) -> CandidateScore:
        """Perform comprehensive scoring of a single candidate"""
        
        # Calculate individual component scores
        semantic_score = self._calculate_semantic_score(candidate)
        skill_score = self._calculate_skill_score(candidate)
        career_scores = self.career_analyzer.analyze_career_trajectory(candidate)
        behavioral_scores = self.behavioral_analyzer.analyze_behavioral_signals(candidate)
        achievement_score = self.career_analyzer.calculate_achievement_score(candidate)
        
        # Calculate experience relevance
        experience_relevance = self.semantic_matcher.compute_experience_similarity(
            candidate.profile.years_of_experience,
            (self.job_requirements.experience_years_min, self.job_requirements.experience_years_max)
        )
        
        # Apply red flag penalties
        red_flag_penalty = self._calculate_red_flag_penalty(candidate)
        
        # Build score components
        components = ScoreComponents(
            semantic_score=semantic_score,
            skill_score=skill_score,
            career_growth_score=career_scores['growth_score'],
            behavioral_score=behavioral_scores['behavioral_score'],
            experience_relevance_score=experience_relevance,
            achievement_score=achievement_score,
            growth_score=career_scores['growth_score'],
            stability_score=career_scores['stability_score'],
            relevance_score=career_scores['relevance_score'],
            red_flag_penalty=red_flag_penalty
        )
        
        # Calculate final weighted score
        final_score = self._calculate_final_score(components)
        
        # Generate explanations
        job_req_dict = {
            'required_skills': self.job_requirements.required_skills,
            'preferred_skills': self.job_requirements.preferred_skills,
            'experience_range': (self.job_requirements.experience_years_min, 
                                self.job_requirements.experience_years_max),
            'preferred_locations': self.job_requirements.preferred_locations
        }
        
        missing_skills = self._identify_missing_skills(candidate)
        
        recommendation_reason = self.explainability_agent.generate_recommendation_reason(
            candidate, components, missing_skills
        )
        
        strengths = self.explainability_agent.generate_strengths_list(
            candidate, components, job_req_dict
        )
        
        risks = self.explainability_agent.generate_risks_list(candidate, job_req_dict)
        
        red_flags = self._detect_red_flags(candidate)
        
        # Create candidate score
        candidate_score = CandidateScore(
            candidate_id=candidate.candidate_id,
            candidate_name=candidate.profile.anonymized_name,
            components=components,
            final_score=final_score,
            rank=0,  # Will be set after ranking
            recommendation_reason=recommendation_reason,
            strengths=strengths,
            risks=risks,
            missing_skills=missing_skills,
            semantic_similarity=semantic_score,
            skill_match_count=len(self._get_matching_skills(candidate)),
            total_years_experience=candidate.profile.years_of_experience,
            relevant_years_experience=career_scores['relevance_score'] * candidate.profile.years_of_experience,
            recruiter_response_rate=candidate.redrob_signals.recruiter_response_rate,
            days_since_active=candidate.calculate_days_since_active(),
            github_activity_score=candidate.redrob_signals.github_activity_score,
            red_flags_detected=red_flags
        )
        
        return candidate_score
    
    def _calculate_semantic_score(self, candidate: Candidate) -> float:
        """Calculate semantic similarity score"""
        similarities = self.semantic_matcher.compute_candidate_job_similarity(
            candidate, self.job_description
        )
        
        # Weighted combination of similarity components
        semantic_score = (
            similarities['overall'] * 0.4 +
            similarities['summary'] * 0.3 +
            similarities['skills'] * 0.2 +
            similarities['headline'] * 0.1
        )
        
        return semantic_score
    
    def _calculate_skill_score(self, candidate: Candidate) -> float:
        """Calculate skill matching score"""
        candidate_skills = candidate.get_skills_list()
        required_skills = self.job_requirements.required_skills
        preferred_skills = self.job_requirements.preferred_skills
        
        # Calculate required skill match
        required_score = self.semantic_matcher.compute_skill_similarity(
            candidate_skills, required_skills
        )
        
        # Calculate preferred skill match (weighted lower)
        preferred_score = self.semantic_matcher.compute_skill_similarity(
            candidate_skills, preferred_skills
        )
        
        # Combine scores
        skill_score = required_score * 0.7 + preferred_score * 0.3
        
        # Bonus for skill depth (advanced/expert skills)
        advanced_skills = sum(1 for skill in candidate.skills 
                             if skill.proficiency in ['advanced', 'expert'])
        if advanced_skills >= 3:
            skill_score = min(1.0, skill_score + 0.1)
        
        return skill_score
    
    def _calculate_final_score(self, components: ScoreComponents) -> float:
        """Calculate final weighted score (0-100)"""
        
        # Apply red flag penalty
        adjusted_semantic = components.semantic_score * (1 - components.red_flag_penalty * 0.3)
        adjusted_skill = components.skill_score * (1 - components.red_flag_penalty * 0.2)
        
        # Weighted sum
        weighted_sum = (
            adjusted_semantic * self.weights['semantic'] +
            adjusted_skill * self.weights['skill'] +
            components.career_growth_score * self.weights['career_growth'] +
            components.behavioral_score * self.weights['behavioral'] +
            components.experience_relevance_score * self.weights['experience'] +
            components.achievement_score * self.weights['achievement']
        )
        
        # Scale to 0-100
        final_score = weighted_sum * 100
        
        return final_score
    
    def _calculate_red_flag_penalty(self, candidate: Candidate) -> float:
        """Calculate penalty for red flags (0-1)"""
        penalty = 0.0
        
        # Title chasing pattern
        if candidate.has_title_chasing_pattern():
            penalty += 0.3
        
        # Consulting-only background
        if candidate.is_consulting_background():
            penalty += 0.2
        
        # Extended inactivity
        days_inactive = candidate.calculate_days_since_active()
        if days_inactive > 180:
            penalty += 0.3
        elif days_inactive > 90:
            penalty += 0.1
        
        # Very low response rate
        if candidate.redrob_signals.recruiter_response_rate < 0.1:
            penalty += 0.2
        
        return min(1.0, penalty)
    
    def _identify_missing_skills(self, candidate: Candidate) -> List[str]:
        """Identify missing required skills"""
        candidate_skills = [skill.lower() for skill in candidate.get_skills_list()]
        required_skills = [skill.lower() for skill in self.job_requirements.required_skills]
        
        missing = []
        for required in required_skills:
            # Check if any candidate skill matches or contains the required skill
            found = any(required in cand_skill or cand_skill in required 
                       for cand_skill in candidate_skills)
            if not found:
                missing.append(required)
        
        return missing
    
    def _get_matching_skills(self, candidate: Candidate) -> List[str]:
        """Get skills that match job requirements"""
        candidate_skills = [skill.lower() for skill in candidate.get_skills_list()]
        all_required = [skill.lower() for skill in 
                       self.job_requirements.required_skills + self.job_requirements.preferred_skills]
        
        matching = []
        for cand_skill in candidate_skills:
            if any(req in cand_skill or cand_skill in req for req in all_required):
                matching.append(cand_skill)
        
        return matching
    
    def _detect_red_flags(self, candidate: Candidate) -> List[str]:
        """Detect red flags based on JD requirements"""
        red_flags = []
        
        if candidate.has_title_chasing_pattern():
            red_flags.append("Title-chasing pattern (frequent job switches)")
        
        if candidate.is_consulting_background():
            red_flags.append("Career limited to consulting firms")
        
        days_inactive = candidate.calculate_days_since_active()
        if days_inactive > 90:
            red_flags.append(f"Inactive for {days_inactive} days")
        
        if candidate.redrob_signals.recruiter_response_rate < 0.2:
            red_flags.append("Low recruiter response rate")
        
        return red_flags
    
    def score_candidates(self, candidates: List[Candidate]) -> List[CandidateScore]:
        """Score multiple candidates"""
        logger.info(f"Scoring {len(candidates)} candidates...")
        
        scored_candidates = []
        for i, candidate in enumerate(candidates):
            if (i + 1) % 100 == 0:
                logger.info(f"Scored {i + 1}/{len(candidates)} candidates...")
            
            try:
                score = self.score_candidate(candidate)
                scored_candidates.append(score)
            except Exception as e:
                logger.warning(f"Failed to score candidate {candidate.candidate_id}: {e}")
                continue
        
        # Rank candidates
        scored_candidates.sort(key=lambda x: x.final_score, reverse=True)
        
        # Assign ranks
        for rank, score in enumerate(scored_candidates, 1):
            score.rank = rank
        
        logger.info(f"Completed scoring. Top candidate: {scored_candidates[0].candidate_name} (Score: {scored_candidates[0].final_score:.1f})")
        
        return scored_candidates
    
    def get_top_candidates(self, candidates: List[Candidate], k: int = 100) -> List[CandidateScore]:
        """Get top K scored candidates"""
        scored = self.score_candidates(candidates)
        return scored[:k]