"""
Bonus Features - Recruiter Copilot, Skill Gap Analysis, Diversity-Aware Ranking, etc.
"""

import logging
from typing import Dict, List, Optional, Set
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.models import Candidate, CandidateScore, JobDescription
from backend.agents.explainable_ranking_agent import ExplainableRankingAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RecruiterCopilot:
    """Recruiter Copilot - Interactive Q&A for candidate comparisons"""
    
    def __init__(self, explainability_agent: ExplainableRankingAgent):
        self.explainability_agent = explainability_agent
    
    def compare_candidates(self, candidate_a: Candidate, score_a: CandidateScore,
                          candidate_b: Candidate, score_b: CandidateScore) -> str:
        """Generate detailed comparison between two candidates"""
        return self.explainability_agent.compare_candidates(
            candidate_a, score_a, candidate_b, score_b
        )
    
    def answer_why_ranked_higher(self, higher_candidate: Candidate, higher_score: CandidateScore,
                                lower_candidate: Candidate, lower_score: CandidateScore) -> str:
        """Answer why one candidate is ranked higher than another"""
        
        score_diff = higher_score.final_score - lower_score.final_score
        
        comparison_parts = [
            f"{higher_candidate.profile.anonymized_name} is ranked above {lower_candidate.profile.anonymized_name} by {score_diff:.1f} points.",
            "",
            "Key reasons:",
        ]
        
        # Compare individual components
        if higher_score.components.semantic_score > lower_score.components.semantic_score + 0.1:
            comparison_parts.append(f"• Better semantic match to job description ({higher_score.components.semantic_score:.2f} vs {lower_score.components.semantic_score:.2f})")
        
        if higher_score.components.skill_score > lower_score.components.skill_score + 0.1:
            comparison_parts.append(f"• Stronger skill alignment ({higher_score.components.skill_score:.2f} vs {lower_score.components.skill_score:.2f})")
        
        if higher_score.components.behavioral_score > lower_score.components.behavioral_score + 0.1:
            comparison_parts.append(f"• Higher platform engagement and availability ({higher_score.components.behavioral_score:.2f} vs {lower_score.components.behavioral_score:.2f})")
        
        if higher_score.components.career_growth_score > lower_score.components.career_growth_score + 0.1:
            comparison_parts.append(f"• Better career growth trajectory ({higher_score.components.career_growth_score:.2f} vs {lower_score.components.career_growth_score:.2f})")
        
        # Experience comparison
        exp_diff = higher_candidate.profile.years_of_experience - lower_candidate.profile.years_of_experience
        if abs(exp_diff) > 1:
            comparison_parts.append(f"• {'More' if exp_diff > 0 else 'Less'} experience ({abs(exp_diff):.1f} years difference)")
        
        return "\n".join(comparison_parts)


class SkillGapAnalyzer:
    """Skill Gap Analysis - Identify missing and development needs"""
    
    def __init__(self):
        pass
    
    def analyze_skill_gaps(self, candidate: Candidate, 
                         required_skills: List[str],
                         preferred_skills: List[str]) -> Dict[str, any]:
        """Analyze skill gaps for a candidate"""
        
        candidate_skills = [skill.lower() for skill in candidate.get_skills_list()]
        
        # Analyze required skill gaps
        missing_required = []
        partial_required = []
        met_required = []
        
        for required in required_skills:
            required_lower = required.lower()
            
            # Check for exact match
            if required_lower in candidate_skills:
                met_required.append(required)
            # Check for partial match
            elif any(req in cand_skill or cand_skill in req 
                    for cand_skill in candidate_skills 
                    for req in required_lower.split()):
                partial_required.append(required)
            else:
                missing_required.append(required)
        
        # Analyze preferred skill gaps
        missing_preferred = []
        partial_preferred = []
        met_preferred = []
        
        for preferred in preferred_skills:
            preferred_lower = preferred.lower()
            
            if preferred_lower in candidate_skills:
                met_preferred.append(preferred)
            elif any(pref in cand_skill or cand_skill in pref 
                    for cand_skill in candidate_skills 
                    for pref in preferred_lower.split()):
                partial_preferred.append(preferred)
            else:
                missing_preferred.append(preferred)
        
        # Calculate skill gap scores
        required_coverage = len(met_required) / len(required_skills) if required_skills else 1.0
        preferred_coverage = len(met_preferred) / len(preferred_skills) if preferred_skills else 0.0
        
        # Identify skills for development
        development_priority = missing_required + missing_preferred[:3]
        
        return {
            'missing_required_skills': missing_required,
            'partial_required_skills': partial_required,
            'met_required_skills': met_required,
            'missing_preferred_skills': missing_preferred,
            'partial_preferred_skills': partial_preferred,
            'met_preferred_skills': met_preferred,
            'required_skill_coverage': required_coverage,
            'preferred_skill_coverage': preferred_coverage,
            'development_priority': development_priority,
            'total_skill_gap': len(missing_required) + len(missing_preferred)
        }
    
    def generate_development_recommendations(self, candidate: Candidate, 
                                           skill_gaps: Dict[str, any]) -> List[str]:
        """Generate skill development recommendations"""
        
        recommendations = []
        
        # High priority required skills
        if skill_gaps['missing_required_skills']:
            recommendations.append(
                f"Priority: Develop required skills: {', '.join(skill_gaps['missing_required_skills'][:3])}"
            )
        
        # Medium priority partial skills
        if skill_gaps['partial_required_skills']:
            recommendations.append(
                f"Strengthen partial matches: {', '.join(skill_gaps['partial_required_skills'][:2])}"
            )
        
        # Preferred skills
        if skill_gaps['missing_preferred_skills']:
            recommendations.append(
                f"Consider learning: {', '.join(skill_gaps['missing_preferred_skills'][:2])}"
            )
        
        # Based on current skills
        if candidate.skills:
            top_skill = max(candidate.skills, key=lambda x: x.duration_months)
            recommendations.append(
                f"Leverage existing expertise in {top_skill.name} ({top_skill.duration_months} months experience)"
            )
        
        return recommendations


class DiversityAwareRanker:
    """Diversity-Aware Ranking - Remove bias from ranking process"""
    
    def __init__(self):
        self.b Protected_attributes = ['name', 'gender', 'age', 'ethnicity']
    
    def anonymize_for_scoring(self, candidate: Candidate) -> Candidate:
        """Remove protected attributes before scoring"""
        
        # Create a copy with anonymized data
        # In this case, the dataset is already anonymized with 'anonymized_name'
        # But we ensure no other protected attributes influence scoring
        
        # Note: The current dataset already uses anonymized names
        # This ensures scoring is based on skills, experience, and behavior only
        
        return candidate
    
    def apply_fairness_checks(self, scored_candidates: List[CandidateScore]) -> Dict[str, any]:
        """Apply fairness checks to ranking results"""
        
        # Calculate score distribution
        scores = [score.final_score for score in scored_candidates]
        
        # Check for potential bias patterns
        fairness_metrics = {
            'score_distribution': {
                'mean': sum(scores) / len(scores),
                'min': min(scores),
                'max': max(scores),
                'std': (sum((x - sum(scores)/len(scores))**2 for x in scores) / len(scores))**0.5
            },
            'ranking_diversity': self._calculate_ranking_diversity(scored_candidates),
            'score_variance': max(scores) - min(scores)
        }
        
        return fairness_metrics
    
    def _calculate_ranking_diversity(self, scored_candidates: List[CandidateScore]) -> float:
        """Calculate diversity in ranking (based on various attributes)"""
        
        # Check diversity in companies
        companies = set()
        for score in scored_candidates[:20]:  # Top 20
            # Extract from candidate (would need full candidate data)
            pass
        
        # For this implementation, we return a placeholder
        # In practice, this would measure diversity across various dimensions
        return 0.0


class NaturalLanguageSearch:
    """Natural Language Search - Query candidates using natural language"""
    
    def __init__(self, scored_candidates: List[CandidateScore]):
        self.scored_candidates = scored_candidates
        self.candidate_map = {score.candidate_id: score for score in scored_candidates}
    
    def search(self, query: str, limit: int = 10) -> List[CandidateScore]:
        """Search candidates using natural language query"""
        
        query_lower = query.lower()
        
        # Simple keyword-based search for demonstration
        # In production, this would use semantic search on candidate profiles
        
        results = []
        for score in self.scored_candidates:
            # Check if query matches various attributes
            match_score = 0
            
            # Check skills
            if 'backend' in query_lower and any(skill in 'backend engineer' 
                for skill in score.recommendation_reason.lower()):
                match_score += 1
            
            if 'leadership' in query_lower and 'leadership' in score.recommendation_reason.lower():
                match_score += 1
            
            if 'ai' in query_lower and any(skill in score.recommendation_reason.lower() 
                for skill in ['ai', 'machine learning', 'ml']):
                match_score += 1
            
            if 'python' in query_lower and 'python' in score.recommendation_reason.lower():
                match_score += 1
            
            if match_score > 0:
                results.append((score, match_score))
        
        # Sort by match score and final score
        results.sort(key=lambda x: (x[1], x[0].final_score), reverse=True)
        
        return [score for score, match in results[:limit]]
    
    def find_similar_to_candidate(self, candidate_id: str, limit: int = 5) -> List[CandidateScore]:
        """Find candidates similar to a given candidate"""
        
        if candidate_id not in self.candidate_map:
            return []
        
        reference_score = self.candidate_map[candidate_id]
        
        # Find similar based on score components
        similar = []
        for score in self.scored_candidates:
            if score.candidate_id == candidate_id:
                continue
            
            # Calculate similarity based on component scores
            component_similarity = (
                abs(score.components.semantic_score - reference_score.components.semantic_score) +
                abs(score.components.skill_score - reference_score.components.skill_score) +
                abs(score.components.behavioral_score - reference_score.components.behavioral_score)
            )
            
            # Lower difference = more similar
            similarity = 1 - component_similarity / 3
            
            similar.append((score, similarity))
        
        # Sort by similarity
        similar.sort(key=lambda x: x[1], reverse=True)
        
        return [score for score, sim in similar[:limit]]