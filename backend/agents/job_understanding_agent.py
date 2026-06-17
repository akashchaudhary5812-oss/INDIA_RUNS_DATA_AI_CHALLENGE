"""
Job Understanding Agent - Extracts structured requirements from job descriptions
"""

import re
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.models import JobDescription, JobRequirements
from backend.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JobUnderstandingAgent:
    """Extracts structured job requirements from job descriptions"""
    
    def __init__(self, job_description_path: Optional[Path] = None):
        self.job_description_path = job_description_path or Config.JOB_DESCRIPTION_DOCX
        self.requirements: Optional[JobRequirements] = None
        self.job_description: Optional[JobDescription] = None
    
    def parse_job_description(self, jd_text: str) -> JobDescription:
        """Parse job description text into structured format"""
        # Extract basic information
        title = self._extract_title(jd_text)
        company = self._extract_company(jd_text)
        location = self._extract_location(jd_text)
        employment_type = self._extract_employment_type(jd_text)
        
        # Extract requirements
        requirements = self._extract_requirements(jd_text)
        
        # Create job description object
        job_desc = JobDescription(
            raw_text=jd_text,
            title=title,
            company=company,
            location=location,
            employment_type=employment_type,
            requirements=requirements,
            summary=self._extract_summary(jd_text)
        )
        
        self.job_description = job_desc
        self.requirements = requirements
        
        logger.info(f"Job description parsed: {title} at {company}")
        return job_desc
    
    def _extract_title(self, text: str) -> str:
        """Extract job title"""
        # Look for common patterns
        patterns = [
            r'Job Description:\s*([^\n—]+)',
            r'Title:\s*([^\n]+)',
            r'Position:\s*([^\n]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Default extraction
        lines = text.split('\n')
        for line in lines[:5]:
            if 'engineer' in line.lower() or 'manager' in line.lower() or 'director' in line.lower():
                return line.strip()
        
        return "Senior AI Engineer"
    
    def _extract_company(self, text: str) -> str:
        """Extract company name"""
        patterns = [
            r'Company:\s*([^\n—]+)',
            r'at\s*([A-Z][^\n,]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                company = match.group(1).strip()
                if len(company) > 3 and len(company) < 50:
                    return company
        
        return "Redrob AI"
    
    def _extract_location(self, text: str) -> str:
        """Extract location"""
        patterns = [
            r'Location:\s*([^\n|]+)',
            r'([A-Z][a-z]+,\s*[A-Z][a-z]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                location = match.group(1).strip()
                if len(location) > 3 and len(location) < 50:
                    return location
        
        return "Pune/Noida, India"
    
    def _extract_employment_type(self, text: str) -> str:
        """Extract employment type"""
        if 'full-time' in text.lower() or 'full time' in text.lower():
            return "Full-time"
        elif 'contract' in text.lower():
            return "Contract"
        elif 'part-time' in text.lower() or 'part time' in text.lower():
            return "Part-time"
        
        return "Full-time"
    
    def _extract_requirements(self, text: str) -> JobRequirements:
        """Extract job requirements"""
        # Initialize with config defaults
        requirements = JobRequirements(
            required_skills=Config.REQUIRED_SKILLS.copy(),
            preferred_skills=Config.PREFERRED_SKILLS.copy(),
            experience_years_min=Config.EXPERIENCE_RANGE[0],
            experience_years_max=Config.EXPERIENCE_RANGE[1],
            preferred_locations=Config.PREFERRED_LOCATIONS.copy()
        )
        
        # Extract skills from text
        text_lower = text.lower()
        
        # Look for explicit skill requirements
        skill_patterns = [
            r'(?:required|must have|need|essential)[\s:]+([^.]+)',
            r'(?:preferred|nice to have|bonus)[\s:]+([^.]+)'
        ]
        
        extracted_skills = set()
        for pattern in skill_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                # Extract potential skill keywords
                words = match.split()
                for i, word in enumerate(words):
                    if len(word) > 3 and word.isalpha():
                        extracted_skills.add(word)
        
        # Add extracted skills if they're relevant
        relevant_skills = {'python', 'machine learning', 'deep learning', 'nlp', 
                          'tensorflow', 'pytorch', 'sql', 'aws', 'docker', 'kubernetes',
                          'llm', 'transformers', 'embeddings', 'vector', 'retrieval',
                          'ranking', 'evaluation', 'faiss', 'pinecone', 'weaviate'}
        
        for skill in extracted_skills:
            if any(keyword in skill for keyword in relevant_skills):
                if skill not in requirements.required_skills:
                    requirements.preferred_skills.append(skill)
        
        # Extract experience requirements
        exp_patterns = [
            r'(\d+)[-–](\d+)\s*(?:years?|yrs?)',
            r'(\d+)\+?\s*(?:years?|yrs?)'
        ]
        
        for pattern in exp_patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                if len(match) == 2:
                    requirements.experience_years_min = int(match[0])
                    requirements.experience_years_max = int(match[1])
                elif len(match) == 1:
                    requirements.experience_years_min = int(match[0])
        
        # Extract domain requirements
        domain_keywords = ['machine learning', 'artificial intelligence', 'data science',
                          'software engineering', 'distributed systems', 'product company']
        
        for keyword in domain_keywords:
            if keyword in text_lower:
                requirements.domain_requirements.append(keyword)
        
        # Infer hidden signals
        requirements.culture_type = self._infer_culture_type(text)
        requirements.role_type = self._infer_role_type(text)
        requirements.focus_area = self._infer_focus_area(text)
        requirements.innovation_orientation = self._infer_innovation_orientation(text)
        
        return requirements
    
    def _infer_culture_type(self, text: str) -> str:
        """Infer culture type (startup vs enterprise)"""
        text_lower = text.lower()
        
        startup_indicators = ['startup', 'found', 'build from scratch', 'early stage', 
                            'series a', 'venture', 'ship fast', 'move fast']
        enterprise_indicators = ['enterprise', 'large scale', 'established', 'corporate',
                                ' fortune ', 'big company']
        
        startup_score = sum(1 for indicator in startup_indicators if indicator in text_lower)
        enterprise_score = sum(1 for indicator in enterprise_indicators if indicator in text_lower)
        
        if startup_score > enterprise_score:
            return "startup"
        elif enterprise_score > startup_score:
            return "enterprise"
        else:
            return "hybrid"
    
    def _infer_role_type(self, text: str) -> str:
        """Infer role type (hands-on vs managerial)"""
        text_lower = text.lower()
        
        hands_on_indicators = ['code', 'implement', 'build', 'develop', 'ship',
                              'hands-on', 'write code', 'production']
        managerial_indicators = ['lead', 'manage', 'mentor', 'team', 'architect',
                                'strategy', 'oversee']
        
        hands_on_score = sum(1 for indicator in hands_on_indicators if indicator in text_lower)
        managerial_score = sum(1 for indicator in managerial_indicators if indicator in text_lower)
        
        if hands_on_score > managerial_score:
            return "hands-on"
        elif managerial_score > hands_on_score:
            return "managerial"
        else:
            return "balanced"
    
    def _infer_focus_area(self, text: str) -> str:
        """Infer focus area (research vs implementation)"""
        text_lower = text.lower()
        
        research_indicators = ['research', 'paper', 'publish', 'academic', 'novel',
                              'innovative', 'state of the art', 'sota']
        implementation_indicators = ['production', 'deploy', 'scale', 'implement',
                                   'ship', 'real-world', 'user-facing']
        
        research_score = sum(1 for indicator in research_indicators if indicator in text_lower)
        implementation_score = sum(1 for indicator in implementation_indicators if indicator in text_lower)
        
        if research_score > implementation_score:
            return "research"
        elif implementation_score > research_score:
            return "implementation"
        else:
            return "balanced"
    
    def _infer_innovation_orientation(self, text: str) -> str:
        """Infer innovation orientation"""
        text_lower = text.lower()
        
        high_innovation = ['cutting edge', 'state of the art', 'breakthrough', 'pioneer',
                         'novel', 'first-mover', 'innovative', 'disrupt']
        moderate_innovation = ['improve', 'enhance', 'optimize', 'better', 'upgrade']
        
        high_score = sum(1 for indicator in high_innovation if indicator in text_lower)
        moderate_score = sum(1 for indicator in moderate_innovation if indicator in text_lower)
        
        if high_score > moderate_score:
            return "high"
        elif moderate_score > high_score:
            return "moderate"
        else:
            return "moderate"
    
    def _extract_summary(self, text: str) -> str:
        """Extract job summary"""
        # Get first few sentences
        sentences = text.split('.')
        if sentences:
            return '. '.join(sentences[:3])
        return ""
    
    def get_requirements(self) -> JobRequirements:
        """Get extracted requirements"""
        if self.requirements is None:
            raise ValueError("Job description not parsed. Call parse_job_description first.")
        return self.requirements
    
    def get_job_description(self) -> JobDescription:
        """Get parsed job description"""
        if self.job_description is None:
            raise ValueError("Job description not parsed. Call parse_job_description first.")
        return self.job_description