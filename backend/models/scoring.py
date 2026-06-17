"""
Scoring result models
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class ScoreComponents(BaseModel):
    """Individual score components"""
    semantic_score: float = Field(..., ge=0, le=1, description="Semantic similarity score")
    skill_score: float = Field(..., ge=0, le=1, description="Skill match score")
    career_growth_score: float = Field(..., ge=0, le=1, description="Career trajectory score")
    behavioral_score: float = Field(..., ge=0, le=1, description="Platform engagement score")
    experience_relevance_score: float = Field(..., ge=0, le=1, description="Experience relevance score")
    achievement_score: float = Field(..., ge=0, le=1, description="Achievement impact score")
    
    # Detailed sub-scores
    growth_score: float = Field(0, ge=0, le=1, description="Career growth/promotions")
    stability_score: float = Field(0, ge=0, le=1, description="Job stability/tenure")
    relevance_score: float = Field(0, ge=0, le=1, description="Domain relevance")
    
    # Penalty scores
    red_flag_penalty: float = Field(0, ge=0, le=1, description="Penalty for red flags")


class CandidateScore(BaseModel):
    """Complete candidate scoring result"""
    candidate_id: str
    candidate_name: str
    
    # Component scores
    components: ScoreComponents
    
    # Final scores
    final_score: float = Field(..., ge=0, le=100, description="Final weighted score 0-100")
    rank: int = Field(0, ge=0, description="Rank position")
    
    # Explanation
    recommendation_reason: str = Field(..., description="Why this candidate is recommended")
    strengths: list[str] = Field(default_factory=list, description="Key strengths")
    risks: list[str] = Field(default_factory=list, description="Potential risks")
    missing_skills: list[str] = Field(default_factory=list, description="Missing required skills")
    
    # Additional metrics
    semantic_similarity: float = Field(0, ge=0, le=1, description="Raw semantic similarity")
    skill_match_count: int = Field(0, ge=0, description="Number of matching skills")
    total_years_experience: float = Field(0, ge=0, description="Total years of experience")
    relevant_years_experience: float = Field(0, ge=0, description="Relevant domain years")
    
    # Behavioral signals
    recruiter_response_rate: float = Field(0, ge=0, le=1, description="Response rate to recruiters")
    days_since_active: int = Field(0, ge=0, description="Days since last platform activity")
    github_activity_score: float = Field(0, ge=-1, le=100, description="GitHub activity score")
    
    # Red flags detected
    red_flags_detected: list[str] = Field(default_factory=list, description="Red flags from JD")
    
    class Config:
        arbitrary_types_allowed = True