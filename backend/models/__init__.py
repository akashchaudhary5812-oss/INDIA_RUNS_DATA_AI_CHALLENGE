"""
Data models for TalentMind AI
"""

from .candidate import Candidate, CandidateProfile, CareerHistory, Education, Skill, Certification, RedrobSignals
from .job import JobDescription, JobRequirements
from .scoring import CandidateScore, ScoreComponents

__all__ = [
    "Candidate",
    "CandidateProfile", 
    "CareerHistory",
    "Education",
    "Skill",
    "Certification",
    "RedrobSignals",
    "JobDescription",
    "JobRequirements",
    "CandidateScore",
    "ScoreComponents"
]
