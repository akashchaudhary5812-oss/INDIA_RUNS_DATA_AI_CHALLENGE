"""
Job description models
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class JobRequirements(BaseModel):
    """Structured job requirements"""
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    experience_years_min: int = 0
    experience_years_max: int = 0
    education_requirements: List[str] = Field(default_factory=list)
    domain_requirements: List[str] = Field(default_factory=list)
    preferred_locations: List[str] = Field(default_factory=list)
    
    # Hidden signals
    culture_type: Optional[str] = Field(None, description="startup vs enterprise")
    role_type: Optional[str] = Field(None, description="hands-on vs managerial")
    focus_area: Optional[str] = Field(None, description="research vs implementation")
    innovation_orientation: Optional[str] = Field(None, description="high vs moderate")


class JobDescription(BaseModel):
    """Complete job description"""
    raw_text: str
    title: str
    company: str
    location: str
    employment_type: str
    requirements: JobRequirements
    summary: str = ""
    
    def get_full_text(self) -> str:
        """Get concatenated text for embedding"""
        parts = [
            self.title,
            self.company,
            self.raw_text,
            " ".join(self.requirements.required_skills),
            " ".join(self.requirements.preferred_skills),
            " ".join(self.requirements.domain_requirements)
        ]
        return " ".join(filter(None, parts))
    
    def get_all_skills(self) -> List[str]:
        """Get all required and preferred skills"""
        return self.requirements.required_skills + self.requirements.preferred_skills