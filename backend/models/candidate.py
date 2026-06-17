"""
Candidate data models
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class Skill(BaseModel):
    """Skill information"""
    name: str
    proficiency: str = Field(..., description="beginner, intermediate, advanced, expert")
    endorsements: int = Field(default=0, ge=0)
    duration_months: int = Field(default=0, ge=0)


class Education(BaseModel):
    """Education information"""
    institution: str
    degree: str
    field_of_study: str
    start_year: int = Field(..., ge=1970, le=2030)
    end_year: int = Field(..., ge=1970, le=2035)
    grade: Optional[str] = None
    tier: Optional[str] = Field(None, description="tier_1, tier_2, tier_3, tier_4, unknown")


class CareerHistory(BaseModel):
    """Career history entry"""
    company: str
    title: str
    start_date: str
    end_date: Optional[str] = None
    duration_months: int = Field(..., ge=0)
    is_current: bool = False
    industry: str
    company_size: str
    description: str


class RedrobSignals(BaseModel):
    """Platform activity and engagement signals"""
    profile_completeness_score: float = Field(..., ge=0, le=100)
    signup_date: str
    last_active_date: str
    open_to_work_flag: bool = False
    profile_views_received_30d: int = Field(default=0, ge=0)
    applications_submitted_30d: int = Field(default=0, ge=0)
    recruiter_response_rate: float = Field(..., ge=0, le=1)
    avg_response_time_hours: float = Field(..., ge=0)
    skill_assessment_scores: Dict[str, float] = Field(default_factory=dict)
    connection_count: int = Field(default=0, ge=0)
    endorsements_received: int = Field(default=0, ge=0)
    notice_period_days: int = Field(..., ge=0, le=180)
    expected_salary_range_inr_lpa: Dict[str, float] = Field(default_factory=dict)
    preferred_work_mode: str = Field(default="flexible")
    willing_to_relocate: bool = False
    github_activity_score: float = Field(..., ge=-1, le=100)
    search_appearance_30d: int = Field(default=0, ge=0)
    saved_by_recruiters_30d: int = Field(default=0, ge=0)
    interview_completion_rate: float = Field(..., ge=0, le=1)
    offer_acceptance_rate: float = Field(..., ge=-1, le=1)
    verified_email: bool = False
    verified_phone: bool = False
    linkedin_connected: bool = False


class CandidateProfile(BaseModel):
    """Candidate profile information"""
    anonymized_name: str
    headline: str
    summary: str
    location: str
    country: str
    years_of_experience: float = Field(..., ge=0, le=50)
    current_title: str
    current_company: str
    current_company_size: str
    current_industry: str


class Certification(BaseModel):
    """Certification information"""
    name: str
    issuer: str
    year: int


class Candidate(BaseModel):
    """Complete candidate profile"""
    candidate_id: str
    profile: CandidateProfile
    career_history: List[CareerHistory] = Field(..., min_items=1, max_items=10)
    education: List[Education] = Field(default_factory=list, max_items=5)
    skills: List[Skill] = Field(default_factory=list)
    certifications: List[Certification] = Field(default_factory=list)
    redrob_signals: RedrobSignals
    languages: Optional[List[Dict[str, str]]] = Field(default_factory=list)
    
    def get_full_text(self) -> str:
        """Get concatenated text for embedding"""
        parts = [
            self.profile.headline,
            self.profile.summary,
            self.profile.current_title,
            " ".join([skill.name for skill in self.skills]),
            " ".join([job.description for job in self.career_history]),
            " ".join([edu.institution + " " + edu.field_of_study for edu in self.education])
        ]
        return " ".join(filter(None, parts))
    
    def get_skills_list(self) -> List[str]:
        """Get list of skill names"""
        return [skill.name.lower() for skill in self.skills]
    
    def get_total_experience_months(self) -> int:
        """Get total career experience in months"""
        return sum(job.duration_months for job in self.career_history)
    
    def get_companies(self) -> List[str]:
        """Get list of companies worked at"""
        return [job.company for job in self.career_history]
    
    def get_job_titles(self) -> List[str]:
        """Get list of job titles"""
        return [job.title for job in self.career_history]
    
    def is_consulting_background(self) -> bool:
        """Check if candidate has only consulting background"""
        consulting_firms = {"tcs", "infosys", "wipro", "accenture", "cognizant", "capgemini"}
        companies = [company.lower() for company in self.get_companies()]
        return all(any(firm in company for firm in consulting_firms) for company in companies)
    
    def has_title_chasing_pattern(self) -> bool:
        """Check for title-chasing pattern (frequent job switches)"""
        if len(self.career_history) < 3:
            return False
        
        # Calculate average tenure
        tenures = [job.duration_months for job in self.career_history]
        avg_tenure_months = sum(tenures) / len(tenures)
        
        # Title chasing if average tenure < 24 months and multiple switches
        return avg_tenure_months < 24 and len(self.career_history) >= 4
    
    def calculate_days_since_active(self) -> int:
        """Calculate days since last active"""
        try:
            last_active = datetime.strptime(self.redrob_signals.last_active_date, "%Y-%m-%d")
            current_date = datetime.now()
            return (current_date - last_active).days
        except:
            return 999  # Return high value if date parsing fails