"""
Unit tests for TalentMind AI scoring engine
"""

import sys
from pathlib import Path
import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.models import Candidate, CandidateProfile, CareerHistory, Education, Skill, RedrobSignals
from backend.config import Config


class TestCandidateModel:
    """Test candidate data model"""
    
    def test_candidate_creation(self):
        """Test creating a candidate object"""
        profile = CandidateProfile(
            anonymized_name="Test Candidate",
            headline="Software Engineer",
            summary="Experienced developer",
            location="San Francisco",
            country="USA",
            years_of_experience=5.0,
            current_title="Senior Engineer",
            current_company="Tech Corp",
            current_company_size="1001-5000",
            current_industry="Technology"
        )
        
        career_history = [
            CareerHistory(
                company="Tech Corp",
                title="Senior Engineer",
                start_date="2020-01-01",
                end_date=None,
                duration_months=48,
                is_current=True,
                industry="Technology",
                company_size="1001-5000",
                description="Leading development team"
            )
        ]
        
        skills = [
            Skill(name="Python", proficiency="expert", endorsements=10, duration_months=60)
        ]
        
        redrob_signals = RedrobSignals(
            profile_completeness_score=85.0,
            signup_date="2023-01-01",
            last_active_date="2024-01-01",
            open_to_work_flag=True,
            profile_views_received_30d=25,
            applications_submitted_30d=5,
            recruiter_response_rate=0.8,
            avg_response_time_hours=24.0,
            skill_assessment_scores={},
            connection_count=100,
            endorsements_received=20,
            notice_period_days=30,
            expected_salary_range_inr_lpa={"min": 20, "max": 30},
            preferred_work_mode="remote",
            willing_to_relocate=True,
            github_activity_score=75.0,
            search_appearance_30d=50,
            saved_by_recruiters_30d=10,
            interview_completion_rate=0.9,
            offer_acceptance_rate=0.8,
            verified_email=True,
            verified_phone=True,
            linkedin_connected=True
        )
        
        candidate = Candidate(
            candidate_id="TEST_0000001",
            profile=profile,
            career_history=career_history,
            education=[],
            skills=skills,
            certifications=[],
            redrob_signals=redrob_signals
        )
        
        assert candidate.candidate_id == "TEST_0000001"
        assert candidate.profile.years_of_experience == 5.0
        assert len(candidate.career_history) == 1
        assert len(candidate.skills) == 1
    
    def test_get_full_text(self):
        """Test full text extraction for embeddings"""
        profile = CandidateProfile(
            anonymized_name="Test",
            headline="Engineer",
            summary="Developer with experience",
            location="NYC",
            country="USA",
            years_of_experience=3.0,
            current_title="Developer",
            current_company="Company",
            current_company_size="51-200",
            current_industry="Tech"
        )
        
        candidate = Candidate(
            candidate_id="TEST_0000002",
            profile=profile,
            career_history=[
                CareerHistory(
                    company="Company",
                    title="Developer",
                    start_date="2021-01-01",
                    end_date=None,
                    duration_months=36,
                    is_current=True,
                    industry="Tech",
                    company_size="51-200",
                    description="Development work"
                )
            ],
            education=[],
            skills=[Skill(name="Python", proficiency="expert", endorsements=5, duration_months=24)],
            certifications=[],
            redrob_signals=RedrobSignals(
                profile_completeness_score=80.0,
                signup_date="2023-01-01",
                last_active_date="2024-01-01",
                open_to_work_flag=True,
                profile_views_received_30d=10,
                applications_submitted_30d=2,
                recruiter_response_rate=0.5,
                avg_response_time_hours=48.0,
                skill_assessment_scores={},
                connection_count=50,
                endorsements_received=10,
                notice_period_days=30,
                expected_salary_range_inr_lpa={"min": 15, "max": 25},
                preferred_work_mode="hybrid",
                willing_to_relocate=False,
                github_activity_score=50.0,
                search_appearance_30d=25,
                saved_by_recruiters_30d=5,
                interview_completion_rate=0.8,
                offer_acceptance_rate=0.7,
                verified_email=True,
                verified_phone=False,
                linkedin_connected=False
            )
        )
        
        full_text = candidate.get_full_text()
        assert "Engineer" in full_text
        assert "Python" in full_text
    
    def test_red_flag_detection(self):
        """Test red flag detection methods"""
        profile = CandidateProfile(
            anonymized_name="Test",
            headline="Engineer",
            summary="Developer",
            location="NYC",
            country="USA",
            years_of_experience=2.0,
            current_title="Junior Engineer",
            current_company="Consulting Firm",
            current_company_size="10001+",
            current_industry="Consulting"
        )
        
        # Create candidate with consulting background
        career_history = [
            CareerHistory(
                company="TCS",
                title="Consultant",
                start_date="2022-01-01",
                end_date="2023-01-01",
                duration_months=12,
                is_current=False,
                industry="Consulting",
                company_size="10001+",
                description="Consulting work"
            )
        ]
        
        candidate = Candidate(
            candidate_id="TEST_0000003",
            profile=profile,
            career_history=career_history,
            education=[],
            skills=[],
            certifications=[],
            redrob_signals=RedrobSignals(
                profile_completeness_score=70.0,
                signup_date="2023-01-01",
                last_active_date="2023-01-01",  # Very old
                open_to_work_flag=False,
                profile_views_received_30d=0,
                applications_submitted_30d=0,
                recruiter_response_rate=0.1,  # Low response rate
                avg_response_time_hours=120.0,
                skill_assessment_scores={},
                connection_count=10,
                endorsements_received=2,
                notice_period_days=90,
                expected_salary_range_inr_lpa={"min": 10, "max": 20},
                preferred_work_mode="onsite",
                willing_to_relocate=False,
                github_activity_score=-1,
                search_appearance_30d=5,
                saved_by_recruiters_30d=0,
                interview_completion_rate=0.5,
                offer_acceptance_rate=-1,
                verified_email=False,
                verified_phone=False,
                linkedin_connected=False
            )
        )
        
        # Test consulting detection
        assert candidate.is_consulting_background()
        
        # Test inactivity
        days_inactive = candidate.calculate_days_since_active()
        assert days_inactive > 365  # Should be very high


class TestConfig:
    """Test configuration settings"""
    
    def test_scoring_weights(self):
        """Test that scoring weights sum to 1.0"""
        weights = Config.get_scoring_weights()
        total_weight = sum(weights.values())
        
        assert abs(total_weight - 1.0) < 0.01, f"Scoring weights sum to {total_weight}, expected 1.0"
    
    def test_required_skills_not_empty(self):
        """Test that required skills are defined"""
        assert len(Config.REQUIRED_SKILLS) > 0
        assert "python" in str(Config.REQUIRED_SKILLS).lower()
    
    def test_experience_range_valid(self):
        """Test that experience range is valid"""
        min_exp, max_exp = Config.EXPERIENCE_RANGE
        assert min_exp > 0
        assert max_exp > min_exp


if __name__ == "__main__":
    pytest.main([__file__, "-v"])