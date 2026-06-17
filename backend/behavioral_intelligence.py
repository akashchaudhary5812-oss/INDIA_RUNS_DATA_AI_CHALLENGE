"""
Behavioral Intelligence - Analyzes platform activity and engagement signals
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.models import Candidate
from backend.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BehavioralAnalyzer:
    """Analyzes behavioral signals from platform activity"""
    
    def __init__(self):
        self.weights = {
            'activity_recency': 0.3,
            'response_rate': 0.25,
            'engagement': 0.2,
            'profile_quality': 0.15,
            'social_proof': 0.1
        }
    
    def analyze_behavioral_signals(self, candidate: Candidate) -> Dict[str, float]:
        """Perform comprehensive behavioral analysis"""
        
        activity_recency_score = self._calculate_activity_recency_score(candidate)
        response_rate_score = self._calculate_response_rate_score(candidate)
        engagement_score = self._calculate_engagement_score(candidate)
        profile_quality_score = self._calculate_profile_quality_score(candidate)
        social_proof_score = self._calculate_social_proof_score(candidate)
        
        # Calculate weighted behavioral score
        behavioral_score = (
            activity_recency_score * self.weights['activity_recency'] +
            response_rate_score * self.weights['response_rate'] +
            engagement_score * self.weights['engagement'] +
            profile_quality_score * self.weights['profile_quality'] +
            social_proof_score * self.weights['social_proof']
        )
        
        return {
            'behavioral_score': behavioral_score,
            'activity_recency_score': activity_recency_score,
            'response_rate_score': response_rate_score,
            'engagement_score': engagement_score,
            'profile_quality_score': profile_quality_score,
            'social_proof_score': social_proof_score,
            'days_since_active': candidate.calculate_days_since_active()
        }
    
    def _calculate_activity_recency_score(self, candidate: Candidate) -> float:
        """Calculate activity recency score (0-1)"""
        days_since_active = candidate.calculate_days_since_active()
        
        # High penalty for inactive candidates
        if days_since_active <= 7:
            return 1.0
        elif days_since_active <= 30:
            return 0.8
        elif days_since_active <= 90:
            return 0.6
        elif days_since_active <= 180:
            return 0.3
        else:
            return 0.1  # Very low score for inactive candidates
    
    def _calculate_response_rate_score(self, candidate: Candidate) -> float:
        """Calculate recruiter response rate score (0-1)"""
        response_rate = candidate.redrob_signals.recruiter_response_rate
        
        if response_rate >= 0.7:
            return 1.0
        elif response_rate >= 0.5:
            return 0.8
        elif response_rate >= 0.3:
            return 0.6
        elif response_rate >= 0.1:
            return 0.4
        else:
            return 0.2
    
    def _calculate_engagement_score(self, candidate: Candidate) -> float:
        """Calculate platform engagement score (0-1)"""
        signals = candidate.redrob_signals
        
        engagement_points = 0
        max_points = 10
        
        # Profile views (indicates market interest)
        if signals.profile_views_received_30d >= 50:
            engagement_points += 2
        elif signals.profile_views_received_30d >= 20:
            engagement_points += 1
        
        # Applications submitted (active job seeker)
        if signals.applications_submitted_30d >= 5:
            engagement_points += 2
        elif signals.applications_submitted_30d >= 2:
            engagement_points += 1
        
        # Search appearances (visibility in searches)
        if signals.search_appearance_30d >= 100:
            engagement_points += 2
        elif signals.search_appearance_30d >= 50:
            engagement_points += 1
        
        # Saved by recruiters (recruiter interest)
        if signals.saved_by_recruiters_30d >= 10:
            engagement_points += 2
        elif signals.saved_by_recruiters_30d >= 5:
            engagement_points += 1
        
        # Open to work flag
        if signals.open_to_work_flag:
            engagement_points += 2
        
        return min(1.0, engagement_points / max_points)
    
    def _calculate_profile_quality_score(self, candidate: Candidate) -> float:
        """Calculate profile quality score (0-1)"""
        signals = candidate.redrob_signals
        
        quality_points = 0
        max_points = 6
        
        # Profile completeness
        if signals.profile_completeness_score >= 90:
            quality_points += 2
        elif signals.profile_completeness_score >= 70:
            quality_points += 1
        
        # Verifications
        if signals.verified_email:
            quality_points += 1
        if signals.verified_phone:
            quality_points += 1
        if signals.linkedin_connected:
            quality_points += 1
        
        # GitHub activity (indicates active developer)
        if signals.github_activity_score > 50:
            quality_points += 1
        elif signals.github_activity_score > 0:
            quality_points += 0.5
        
        return min(1.0, quality_points / max_points)
    
    def _calculate_social_proof_score(self, candidate: Candidate) -> float:
        """Calculate social proof score (0-1)"""
        signals = candidate.redrob_signals
        
        social_points = 0
        max_points = 5
        
        # Connections
        if signals.connection_count >= 500:
            social_points += 2
        elif signals.connection_count >= 200:
            social_points += 1
        
        # Endorsements
        if signals.endorsements_received >= 50:
            social_points += 2
        elif signals.endorsements_received >= 20:
            social_points += 1
        
        # Interview completion rate (reliability)
        if signals.interview_completion_rate >= 0.8:
            social_points += 1
        elif signals.interview_completion_rate >= 0.6:
            social_points += 0.5
        
        return min(1.0, social_points / max_points)
    
    def assess_availability(self, candidate: Candidate) -> Dict[str, any]:
        """Assess candidate availability and readiness"""
        signals = candidate.redrob_signals
        days_since_active = candidate.calculate_days_since_active()
        
        availability_score = 0
        availability_factors = []
        
        # Active on platform
        if days_since_active <= 30:
            availability_score += 3
            availability_factors.append("Recently active on platform")
        elif days_since_active <= 90:
            availability_score += 2
            availability_factors.append("Somewhat active")
        else:
            availability_factors.append("Inactive for extended period")
        
        # Open to work
        if signals.open_to_work_flag:
            availability_score += 3
            availability_factors.append("Marked as open to work")
        
        # Notice period
        if signals.notice_period_days <= 30:
            availability_score += 2
            availability_factors.append("Short notice period")
        elif signals.notice_period_days <= 60:
            availability_score += 1
            availability_factors.append("Moderate notice period")
        
        # Application activity
        if signals.applications_submitted_30d >= 2:
            availability_score += 2
            availability_factors.append("Actively applying")
        
        return {
            'availability_score': availability_score,
            'max_score': 10,
            'availability_percentage': availability_score / 10.0,
            'availability_factors': availability_factors,
            'days_since_active': days_since_active,
            'open_to_work': signals.open_to_work_flag,
            'notice_period_days': signals.notice_period_days
        }
    
    def detect_learning_orientation(self, candidate: Candidate) -> Dict[str, any]:
        """Detect continuous learning and curiosity signals"""
        learning_signals = []
        learning_score = 0
        
        # Recent skill acquisitions (skills with short duration)
        recent_skills = [skill for skill in candidate.skills if skill.duration_months <= 12]
        if len(recent_skills) >= 3:
            learning_score += 3
            learning_signals.append(f"Recently learned {len(recent_skills)} new skills")
        
        # GitHub activity (continuous coding)
        if candidate.redrob_signals.github_activity_score > 50:
            learning_score += 3
            learning_signals.append("High GitHub activity")
        elif candidate.redrob_signals.github_activity_score > 0:
            learning_score += 1
            learning_signals.append("Some GitHub activity")
        
        # Certifications (formal learning)
        if candidate.certifications:
            learning_score += 2
            learning_signals.append(f"Has {len(candidate.certifications)} certifications")
        
        # Skill assessment completion (willingness to prove skills)
        if candidate.redrob_signals.skill_assessment_scores:
            learning_score += 2
            learning_signals.append(f"Completed {len(candidate.redrob_signals.skill_assessment_scores)} skill assessments")
        
        return {
            'learning_score': learning_score,
            'max_score': 10,
            'learning_percentage': learning_score / 10.0,
            'learning_signals': learning_signals
        }
    
    def assess_fit_for_culture(self, candidate: Candidate, job_requirements: Dict) -> Dict[str, any]:
        """Assess cultural fit based on behavioral signals"""
        fit_score = 0.5  # Start neutral
        fit_factors = []
        
        # Work mode preference
        preferred_work_mode = candidate.redrob_signals.preferred_work_mode.lower()
        if 'hybrid' in preferred_work_mode or 'flexible' in preferred_work_mode:
            fit_score += 0.2
            fit_factors.append("Flexible work mode preference")
        
        # Relocation willingness
        if candidate.redrob_signals.willing_to_relocate:
            fit_score += 0.1
            fit_factors.append("Willing to relocate")
        
        # Response time (quick responders are often more engaged)
        if candidate.redrob_signals.avg_response_time_hours <= 24:
            fit_score += 0.1
            fit_factors.append("Quick response time")
        
        # Interview reliability
        if candidate.redrob_signals.interview_completion_rate >= 0.8:
            fit_score += 0.1
            fit_factors.append("High interview completion rate")
        
        return {
            'culture_fit_score': min(1.0, fit_score),
            'fit_factors': fit_factors
        }