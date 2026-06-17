"""
Data loading and preprocessing module
"""

import json
import pandas as pd
from pathlib import Path
from typing import List, Iterator, Optional
from docx import Document
import logging

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.models import Candidate, CandidateProfile, CareerHistory, Education, Skill, Certification, RedrobSignals
from backend.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataLoader:
    """Load and preprocess candidate data"""
    
    def __init__(self, data_path: Optional[Path] = None):
        self.data_path = data_path or Config.CANDIDATES_JSONL
        self.job_description_path = Config.JOB_DESCRIPTION_DOCX
    
    def load_candidates_from_jsonl(self, limit: Optional[int] = None) -> List[Candidate]:
        """Load candidates from JSONL file"""
        candidates = []
        
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    if limit and i >= limit:
                        break
                    
                    try:
                        data = json.loads(line.strip())
                        candidate = self._parse_candidate(data)
                        candidates.append(candidate)
                    except Exception as e:
                        logger.warning(f"Failed to parse candidate at line {i}: {e}")
                        continue
        
        except FileNotFoundError:
            logger.error(f"Candidates file not found: {self.data_path}")
            # Try loading from sample candidates as fallback
            sample_path = Config.SAMPLE_CANDIDATES
            if sample_path.exists():
                logger.info(f"Loading from sample candidates: {sample_path}")
                with open(sample_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for item in data:
                            try:
                                candidate = self._parse_candidate(item)
                                candidates.append(candidate)
                            except Exception as e:
                                logger.warning(f"Failed to parse sample candidate: {e}")
                                continue
                        if limit:
                            candidates = candidates[:limit]
        
        logger.info(f"Loaded {len(candidates)} candidates")
        return candidates
    
    def load_candidates_from_json(self, file_path: Path, limit: Optional[int] = None) -> List[Candidate]:
        """Load candidates from JSON file"""
        candidates = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                if isinstance(data, list):
                    items = data[:limit] if limit else data
                    for item in items:
                        try:
                            candidate = self._parse_candidate(item)
                            candidates.append(candidate)
                        except Exception as e:
                            logger.warning(f"Failed to parse candidate: {e}")
                            continue
        
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
        except Exception as e:
            logger.error(f"Error loading candidates from JSON: {e}")
        
        return candidates
    
    def _parse_candidate(self, data: dict) -> Candidate:
        """Parse candidate data from dictionary"""
        # Parse profile
        profile_data = data.get('profile', {})
        profile = CandidateProfile(
            anonymized_name=profile_data.get('anonymized_name', ''),
            headline=profile_data.get('headline', ''),
            summary=profile_data.get('summary', ''),
            location=profile_data.get('location', ''),
            country=profile_data.get('country', ''),
            years_of_experience=profile_data.get('years_of_experience', 0),
            current_title=profile_data.get('current_title', ''),
            current_company=profile_data.get('current_company', ''),
            current_company_size=profile_data.get('current_company_size', ''),
            current_industry=profile_data.get('current_industry', '')
        )
        
        # Parse career history
        career_history = []
        for job_data in data.get('career_history', []):
            career_history.append(CareerHistory(
                company=job_data.get('company', ''),
                title=job_data.get('title', ''),
                start_date=job_data.get('start_date', ''),
                end_date=job_data.get('end_date'),
                duration_months=job_data.get('duration_months', 0),
                is_current=job_data.get('is_current', False),
                industry=job_data.get('industry', ''),
                company_size=job_data.get('company_size', ''),
                description=job_data.get('description', '')
            ))
        
        # Parse education
        education = []
        for edu_data in data.get('education', []):
            education.append(Education(
                institution=edu_data.get('institution', ''),
                degree=edu_data.get('degree', ''),
                field_of_study=edu_data.get('field_of_study', ''),
                start_year=edu_data.get('start_year', 0),
                end_year=edu_data.get('end_year', 0),
                grade=edu_data.get('grade'),
                tier=edu_data.get('tier')
            ))
        
        # Parse skills
        skills = []
        for skill_data in data.get('skills', []):
            skills.append(Skill(
                name=skill_data.get('name', ''),
                proficiency=skill_data.get('proficiency', 'beginner'),
                endorsements=skill_data.get('endorsements', 0),
                duration_months=skill_data.get('duration_months', 0)
            ))
        
        # Parse certifications
        certifications = []
        for cert_data in data.get('certifications', []):
            certifications.append(Certification(
                name=cert_data.get('name', ''),
                issuer=cert_data.get('issuer', ''),
                year=cert_data.get('year', 0)
            ))
        
        # Parse redrob signals
        signals_data = data.get('redrob_signals', {})
        redrob_signals = RedrobSignals(
            profile_completeness_score=signals_data.get('profile_completeness_score', 0),
            signup_date=signals_data.get('signup_date', ''),
            last_active_date=signals_data.get('last_active_date', ''),
            open_to_work_flag=signals_data.get('open_to_work_flag', False),
            profile_views_received_30d=signals_data.get('profile_views_received_30d', 0),
            applications_submitted_30d=signals_data.get('applications_submitted_30d', 0),
            recruiter_response_rate=signals_data.get('recruiter_response_rate', 0),
            avg_response_time_hours=signals_data.get('avg_response_time_hours', 0),
            skill_assessment_scores=signals_data.get('skill_assessment_scores', {}),
            connection_count=signals_data.get('connection_count', 0),
            endorsements_received=signals_data.get('endorsements_received', 0),
            notice_period_days=signals_data.get('notice_period_days', 0),
            expected_salary_range_inr_lpa=signals_data.get('expected_salary_range_inr_lpa', {}),
            preferred_work_mode=signals_data.get('preferred_work_mode', 'flexible'),
            willing_to_relocate=signals_data.get('willing_to_relocate', False),
            github_activity_score=signals_data.get('github_activity_score', -1),
            search_appearance_30d=signals_data.get('search_appearance_30d', 0),
            saved_by_recruiters_30d=signals_data.get('saved_by_recruiters_30d', 0),
            interview_completion_rate=signals_data.get('interview_completion_rate', 0),
            offer_acceptance_rate=signals_data.get('offer_acceptance_rate', -1),
            verified_email=signals_data.get('verified_email', False),
            verified_phone=signals_data.get('verified_phone', False),
            linkedin_connected=signals_data.get('linkedin_connected', False)
        )
        
        return Candidate(
            candidate_id=data.get('candidate_id', ''),
            profile=profile,
            career_history=career_history,
            education=education,
            skills=skills,
            certifications=certifications,
            redrob_signals=redrob_signals,
            languages=data.get('languages', [])
        )
    
    def load_job_description(self) -> str:
        """Load job description from DOCX file"""
        try:
            doc = Document(self.job_description_path)
            text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
            logger.info("Job description loaded successfully")
            return text
        except Exception as e:
            logger.error(f"Error loading job description: {e}")
            return ""
    
    def load_sample_submission(self) -> pd.DataFrame:
        """Load sample submission format"""
        try:
            df = pd.read_csv(self.job_description_path.parent / 'sample_submission.csv')
            logger.info(f"Sample submission loaded: {len(df)} rows")
            return df
        except Exception as e:
            logger.error(f"Error loading sample submission: {e}")
            return pd.DataFrame()
    
    def stream_candidates(self, batch_size: int = 100) -> Iterator[List[Candidate]]:
        """Stream candidates in batches for memory efficiency"""
        batch = []
        
        with open(self.data_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    candidate = self._parse_candidate(data)
                    batch.append(candidate)
                    
                    if len(batch) >= batch_size:
                        yield batch
                        batch = []
                except Exception as e:
                    logger.warning(f"Failed to parse candidate: {e}")
                    continue
        
        if batch:
            yield batch