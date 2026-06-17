"""
Explainable Ranking Agent - Generates human-readable explanations for rankings
"""

import logging
from typing import Dict, List, Optional, Any

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.models import Candidate, CandidateScore, ScoreComponents
from backend.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExplainableRankingAgent:
    """Generates human-readable explanations for candidate rankings"""
    
    def __init__(self):
        self.strength_templates = [
            "Strong {skill} expertise",
            "Excellent {skill} background",
            "Deep knowledge of {skill}",
            "Extensive {skill} experience"
        ]
        
        self.risk_templates = [
            "Limited experience in {area}",
            "May need to develop {skill}",
            "Less exposure to {technology}",
            "Could strengthen {area}"
        ]
    
    def generate_explanation(self, candidate: Candidate, score_components: ScoreComponents, 
                           job_requirements: Dict) -> str:
        """Generate a comprehensive explanation for the candidate recommendation"""
        
        # Extract key information
        profile = candidate.profile
        skills = candidate.get_skills_list()
        experience = profile.years_of_experience
        title = profile.current_title
        
        # Build explanation components
        introduction = self._generate_introduction(candidate, score_components)
        strengths_section = self._generate_strengths(candidate, score_components, job_requirements)
        experience_section = self._generate_experience_summary(candidate)
        behavioral_section = self._generate_behavioral_summary(candidate)
        risks_section = self._generate_risks(candidate, job_requirements)
        conclusion = self._generate_conclusion(candidate, score_components)
        
        # Combine into full explanation
        explanation = f"{introduction}\n\n{strengths_section}\n\n{experience_section}\n\n{behavioral_section}\n\n{risks_section}\n\n{conclusion}"
        
        return explanation
    
    def _generate_introduction(self, candidate: Candidate, score_components: ScoreComponents) -> str:
        """Generate introduction for the explanation"""
        profile = candidate.profile
        overall_score = (score_components.semantic_score + 
                         score_components.skill_score + 
                         score_components.career_growth_score) / 3
        
        introduction = f"{profile.anonymized_name} is a {profile.current_title} with {profile.years_of_experience} years of experience"
        
        if overall_score >= 0.8:
            introduction += " and demonstrates exceptional fit for this role."
        elif overall_score >= 0.6:
            introduction += " and shows strong potential for this position."
        else:
            introduction += " and may be a viable candidate with some considerations."
        
        return introduction
    
    def _generate_strengths(self, candidate: Candidate, score_components: ScoreComponents,
                           job_requirements: Dict) -> str:
        """Generate strengths section"""
        strengths = []
        
        # Skill-based strengths
        if score_components.skill_score >= 0.7:
            top_skills = candidate.get_skills_list()[:5]
            if top_skills:
                strengths.append(f"Strong technical background with expertise in {', '.join(top_skills[:3])}")
        
        # Experience-based strengths
        if score_components.semantic_score >= 0.7:
            strengths.append(f"Relevant experience as {candidate.profile.current_title} at {candidate.profile.current_company}")
        
        # Career growth
        if score_components.growth_score >= 0.6:
            strengths.append("Demonstrates clear career progression and growth")
        
        # Behavioral strengths
        if score_components.behavioral_score >= 0.7:
            strengths.append("High platform engagement and quick response rates")
        
        # Achievement-based strengths
        if score_components.achievement_score >= 0.6:
            strengths.append("Track record of impactful contributions and achievements")
        
        if not strengths:
            strengths.append("Shows potential with further development")
        
        return "Key Strengths:\n" + "\n".join(f"• {strength}" for strength in strengths)
    
    def _generate_experience_summary(self, candidate: Candidate) -> str:
        """Generate experience summary section"""
        career_history = candidate.career_history
        total_exp = candidate.get_total_experience_months() / 12
        
        summary_parts = [
            f"Total professional experience: {total_exp:.1f} years",
            f"Current role: {candidate.profile.current_title} at {candidate.profile.current_company}",
            f"Career spans {len(career_history)} role(s) at {len(set(job.company for job in career_history))} different company/companies"
        ]
        
        # Add recent experience highlight
        if career_history:
            most_recent = career_history[0]
            summary_parts.append(f"Most recently: {most_recent.title} at {most_recent.company} ({most_recent.duration_months} months)")
        
        return "Experience Summary:\n" + "\n".join(f"• {part}" for part in summary_parts)
    
    def _generate_behavioral_summary(self, candidate: Candidate) -> str:
        """Generate behavioral signals summary"""
        signals = candidate.redrob_signals
        behaviors = []
        
        # Activity status
        days_active = candidate.calculate_days_since_active()
        if days_active <= 7:
            behaviors.append("Very recently active on platform")
        elif days_active <= 30:
            behaviors.append("Active within last month")
        else:
            behaviors.append(f"Last active {days_active} days ago")
        
        # Response behavior
        if signals.recruiter_response_rate >= 0.7:
            behaviors.append(f"High recruiter response rate ({signals.recruiter_response_rate:.0%})")
        elif signals.recruiter_response_rate >= 0.3:
            behaviors.append(f"Moderate recruiter response rate ({signals.recruiter_response_rate:.0%})")
        
        # Availability
        if signals.open_to_work_flag:
            behaviors.append("Marked as open to work opportunities")
        
        # Platform engagement
        if signals.saved_by_recruiters_30d >= 5:
            behaviors.append(f"High recruiter interest ({signals.saved_by_recruiters_30d} saves in 30 days)")
        
        return "Behavioral Indicators:\n" + "\n".join(f"• {behavior}" for behavior in behaviors)
    
    def _generate_risks(self, candidate: Candidate, job_requirements: Dict) -> str:
        """Generate risks and considerations section"""
        risks = []
        
        # Experience gap
        experience = candidate.profile.years_of_experience
        required_range = job_requirements.get('experience_range', Config.EXPERIENCE_RANGE)
        
        if experience < required_range[0]:
            risks.append(f"Experience ({experience} years) is below the preferred range ({required_range[0]}-{required_range[1]} years)")
        elif experience > required_range[1]:
            risks.append(f"Experience ({experience} years) exceeds the preferred range ({required_range[0]}-{required_range[1]} years)")
        
        # Skill gaps
        required_skills = job_requirements.get('required_skills', Config.REQUIRED_SKILLS)
        candidate_skills = [skill.lower() for skill in candidate.get_skills_list()]
        
        missing_skills = [skill for skill in required_skills if not any(
            req_skill in cand_skill for cand_skill in candidate_skills for req_skill in skill.lower().split()
        )]
        
        if missing_skills:
            risks.append(f"May need to develop experience with: {', '.join(missing_skills[:3])}")
        
        # Activity concerns
        days_active = candidate.calculate_days_since_active()
        if days_active > 90:
            risks.append(f"Extended period of platform inactivity ({days_active} days)")
        
        # Response rate concerns
        if candidate.redrob_signals.recruiter_response_rate < 0.3:
            risks.append("Low historical response rate to recruiters")
        
        # Job hopping concerns
        if candidate.has_title_chasing_pattern():
            risks.append("Pattern of frequent job changes may indicate stability concerns")
        
        # Consulting-only background
        if candidate.is_consulting_background():
            risks.append("Career entirely in consulting firms (may lack product company experience)")
        
        if not risks:
            risks.append("No significant risks identified")
        
        return "Considerations:\n" + "\n".join(f"• {risk}" for risk in risks)
    
    def _generate_conclusion(self, candidate: Candidate, score_components: ScoreComponents) -> str:
        """Generate conclusion/recommendation"""
        final_score = (score_components.semantic_score + 
                      score_components.skill_score + 
                      score_components.career_growth_score +
                      score_components.behavioral_score +
                      score_components.achievement_score) / 5
        
        if final_score >= 0.8:
            return f"Overall Assessment: Strong fit. Final score: {final_score:.2f}. Candidate demonstrates excellent alignment with role requirements and should be prioritized for outreach."
        elif final_score >= 0.6:
            return f"Overall Assessment: Good fit. Final score: {final_score:.2f}. Candidate shows strong potential and should be considered for outreach."
        else:
            return f"Overall Assessment: Moderate fit. Final score: {final_score:.2f}. Candidate may warrant consideration depending on talent pool and specific requirements."
    
    def generate_recommendation_reason(self, candidate: Candidate, score_components: ScoreComponents,
                                      missing_skills: List[str]) -> str:
        """Generate a concise recommendation reason (for CSV output)"""
        
        parts = []
        
        # Experience
        exp = candidate.profile.years_of_experience
        parts.append(f"{candidate.profile.current_title} with {exp:.1f} yrs")
        
        # Skills
        skill_count = len([s for s in candidate.get_skills_list() if any(
            kw in s.lower() for kw in ['python', 'machine learning', 'ai', 'ml', 'data']
        )])
        parts.append(f"{skill_count} AI/ML-related skills")
        
        # Response rate
        response_rate = candidate.redrob_signals.recruiter_response_rate
        parts.append(f"response rate {response_rate:.2f}")
        
        # Add missing skills if any
        if missing_skills:
            parts.append(f"missing: {', '.join(missing_skills[:2])}")
        
        return "; ".join(parts)
    
    def generate_strengths_list(self, candidate: Candidate, score_components: ScoreComponents,
                                job_requirements: Dict) -> List[str]:
        """Generate a list of key strengths"""
        strengths = []
        
        if score_components.skill_score >= 0.7:
            skills = candidate.get_skills_list()
            if skills:
                strengths.append(f"Strong technical skills: {', '.join(skills[:3])}")
        
        if score_components.career_growth_score >= 0.6:
            strengths.append("Demonstrates career growth and progression")
        
        if score_components.semantic_score >= 0.7:
            strengths.append("High semantic similarity to job requirements")
        
        if score_components.behavioral_score >= 0.7:
            strengths.append("High platform engagement and availability")
        
        if score_components.achievement_score >= 0.6:
            strengths.append("Track record of achievements and impact")
        
        if not strengths:
            strengths.append("Shows potential for the role")
        
        return strengths
    
    def generate_risks_list(self, candidate: Candidate, job_requirements: Dict) -> List[str]:
        """Generate a list of potential risks"""
        risks = []
        
        experience = candidate.profile.years_of_experience
        required_range = job_requirements.get('experience_range', Config.EXPERIENCE_RANGE)
        
        if experience < required_range[0]:
            risks.append(f"Below preferred experience range")
        
        if candidate.calculate_days_since_active() > 90:
            risks.append("Extended platform inactivity")
        
        if candidate.redrob_signals.recruiter_response_rate < 0.3:
            risks.append("Low recruiter response rate")
        
        if candidate.has_title_chasing_pattern():
            risks.append("Pattern of frequent job changes")
        
        if candidate.is_consulting_background():
            risks.append("Limited product company experience")
        
        return risks
    
    def compare_candidates(self, candidate_a: Candidate, score_a: CandidateScore,
                          candidate_b: Candidate, score_b: CandidateScore) -> str:
        """Generate a comparison explanation between two candidates"""
        
        comparison_parts = [
            f"Comparing {candidate_a.profile.anonymized_name} (Score: {score_a.final_score:.1f}) vs {candidate_b.profile.anonymized_name} (Score: {score_b.final_score:.1f}):"
        ]
        
        # Compare experience
        exp_diff = candidate_a.profile.years_of_experience - candidate_b.profile.years_of_experience
        if abs(exp_diff) > 1:
            better = candidate_a if exp_diff > 0 else candidate_b
            comparison_parts.append(f"• Experience: {better.profile.anonymized_name} has {abs(exp_diff):.1f} more years of experience")
        
        # Compare skills
        skill_diff = len(candidate_a.get_skills_list()) - len(candidate_b.get_skills_list())
        if abs(skill_diff) > 2:
            better = candidate_a if skill_diff > 0 else candidate_b
            comparison_parts.append(f"• Skills: {better.profile.anonymized_name} lists {abs(skill_diff)} more skills")
        
        # Compare behavioral scores
        behavior_diff = score_a.components.behavioral_score - score_b.components.behavioral_score
        if abs(behavior_diff) > 0.1:
            better = candidate_a if behavior_diff > 0 else candidate_b
            comparison_parts.append(f"• Engagement: {better.profile.anonymized_name} shows higher platform activity")
        
        # Compare career growth
        growth_diff = score_a.components.career_growth_score - score_b.components.career_growth_score
        if abs(growth_diff) > 0.1:
            better = candidate_a if growth_diff > 0 else candidate_b
            comparison_parts.append(f"• Career Growth: {better.profile.anonymized_name} demonstrates stronger progression")
        
        return "\n".join(comparison_parts)