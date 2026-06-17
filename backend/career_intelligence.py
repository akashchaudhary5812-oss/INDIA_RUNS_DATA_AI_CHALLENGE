"""
Career Trajectory Intelligence - Analyzes career progression and growth
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import re

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.models import Candidate
from backend.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CareerTrajectoryAnalyzer:
    """Analyzes career progression and growth patterns"""
    
    def __init__(self):
        self.promotion_keywords = ['promoted', 'promotion', 'advanced', 'promoted to',
                                  'moved up', 'elevated', 'stepped up', 'leveled']
        self.responsibility_keywords = ['increased responsibility', 'expanded role',
                                       'broader scope', 'additional responsibilities',
                                       'team lead', 'leading', 'managing']
        self.seniority_mapping = {
            'intern': 0, 'junior': 1, 'associate': 2, 'software engineer': 3,
            'senior': 4, 'staff': 5, 'principal': 6, 'lead': 4, 'manager': 5,
            'director': 6, 'vp': 7, 'head': 6, 'chief': 8
        }
    
    def analyze_career_trajectory(self, candidate: Candidate) -> Dict[str, float]:
        """Perform comprehensive career trajectory analysis"""
        
        # Sort career history by date
        sorted_career = sorted(candidate.career_history, key=lambda x: x.start_date)
        
        growth_score = self._calculate_growth_score(sorted_career)
        stability_score = self._calculate_stability_score(sorted_career)
        relevance_score = self._calculate_relevance_score(candidate, sorted_career)
        
        return {
            'growth_score': growth_score,
            'stability_score': stability_score,
            'relevance_score': relevance_score
        }
    
    def _calculate_growth_score(self, career_history: List) -> float:
        """Calculate career growth score (0-1)"""
        if not career_history or len(career_history) < 2:
            return 0.5  # Neutral score for limited data
        
        growth_points = 0
        max_points = 10
        
        # Check for promotions
        for i in range(1, len(career_history)):
            prev_title = career_history[i-1].title.lower()
            curr_title = career_history[i].title.lower()
            
            # Detect promotion from title change
            prev_level = self._get_seniority_level(prev_title)
            curr_level = self._get_seniority_level(curr_title)
            
            if curr_level > prev_level:
                growth_points += 2
        
        # Check for increasing responsibility in descriptions
        for job in career_history:
            desc_lower = job.description.lower()
            for keyword in self.responsibility_keywords:
                if keyword in desc_lower:
                    growth_points += 1
                    break
        
        # Check for company growth (moving to larger/better companies)
        company_sizes = [job.company_size for job in career_history]
        size_order = {'1-10': 1, '11-50': 2, '51-200': 3, '201-500': 4,
                     '501-1000': 5, '1001-5000': 6, '5001-10000': 7, '10001+': 8}
        
        for i in range(1, len(company_sizes)):
            if company_sizes[i-1] in size_order and company_sizes[i] in size_order:
                if size_order[company_sizes[i]] > size_order[company_sizes[i-1]]:
                    growth_points += 1
        
        # Normalize to 0-1
        return min(1.0, growth_points / max_points)
    
    def _calculate_stability_score(self, career_history: List) -> float:
        """Calculate job stability score (0-1)"""
        if not career_history:
            return 0.5
        
        # Calculate average tenure
        tenures = [job.duration_months for job in career_history]
        avg_tenure = sum(tenures) / len(tenures)
        
        # Stability points
        stability_points = 0
        
        # Average tenure points
        if avg_tenure >= 36:  # 3+ years
            stability_points += 3
        elif avg_tenure >= 24:  # 2+ years
            stability_points += 2
        elif avg_tenure >= 18:  # 1.5+ years
            stability_points += 1
        
        # Number of companies (fewer changes = more stable)
        num_companies = len(set(job.company for job in career_history))
        if num_companies <= 2:
            stability_points += 2
        elif num_companies <= 3:
            stability_points += 1
        
        # Normalize to 0-1
        return min(1.0, stability_points / 5.0)
    
    def _calculate_relevance_score(self, candidate: Candidate, career_history: List) -> float:
        """Calculate domain relevance score (0-1)"""
        # Check for relevant experience in ML/AI/Software Engineering
        relevant_keywords = ['machine learning', 'ai', 'artificial intelligence', 
                           'data science', 'software engineer', 'backend engineer',
                           'full stack', 'data engineer', 'ml engineer', 'ai engineer']
        
        relevant_months = 0
        total_months = 0
        
        for job in career_history:
            total_months += job.duration_months
            
            title_lower = job.title.lower()
            desc_lower = job.description.lower()
            industry_lower = job.industry.lower()
            
            # Check if job is relevant
            is_relevant = any(keyword in title_lower or keyword in desc_lower 
                           for keyword in relevant_keywords)
            
            # Also check if company is in tech/software industry
            tech_industries = ['technology', 'software', 'it services', 'internet',
                             'computer software', 'information technology']
            is_tech_industry = any(industry in industry_lower for industry in tech_industries)
            
            if is_relevant or is_tech_industry:
                relevant_months += job.duration_months
        
        if total_months == 0:
            return 0.5
        
        relevance_ratio = relevant_months / total_months
        return relevance_ratio
    
    def _get_seniority_level(self, title: str) -> int:
        """Get seniority level from title"""
        title_lower = title.lower()
        
        for keyword, level in self.seniority_mapping.items():
            if keyword in title_lower:
                return level
        
        return 2  # Default to mid-level
    
    def detect_promotions(self, career_history: List) -> List[Dict]:
        """Detect promotions in career history"""
        promotions = []
        
        sorted_career = sorted(career_history, key=lambda x: x.start_date)
        
        for i in range(1, len(sorted_career)):
            prev_job = sorted_career[i-1]
            curr_job = sorted_career[i]
            
            prev_level = self._get_seniority_level(prev_job.title)
            curr_level = self._get_seniority_level(curr_job.title)
            
            if curr_level > prev_level:
                promotions.append({
                    'from': prev_job.title,
                    'to': curr_job.title,
                    'company': curr_job.company,
                    'date': curr_job.start_date
                })
        
        return promotions
    
    def calculate_achievement_score(self, candidate: Candidate) -> float:
        """Calculate achievement impact score (0-1)"""
        achievement_points = 0
        max_points = 10
        
        # Check for quantified metrics in job descriptions
        metric_patterns = [
            r'\d+%',  # percentages
            r'\d+\+?\s*(?:users|customers|clients|projects|team members)',
            r'\$[\d,]+',
            r'\d+x\s*(?:improvement|increase|growth|reduction)'
        ]
        
        for job in candidate.career_history:
            desc = job.description
            for pattern in metric_patterns:
                matches = re.findall(pattern, desc, re.IGNORECASE)
                achievement_points += len(matches) * 0.5
        
        # Check for awards/publications
        summary = candidate.profile.summary.lower()
        if any(word in summary for word in ['award', 'published', 'patent', 'conference', 'recognized']):
            achievement_points += 2
        
        # GitHub activity
        github_score = candidate.redrob_signals.github_activity_score
        if github_score > 0:
            achievement_points += (github_score / 100) * 2
        
        # Certifications
        if candidate.certifications:
            achievement_points += len(candidate.certifications) * 0.5
        
        # Normalize
        return min(1.0, achievement_points / max_points)
    
    def analyze_title_progression(self, candidate: Candidate) -> Dict:
        """Analyze title progression over career"""
        sorted_career = sorted(candidate.career_history, key=lambda x: x.start_date)
        titles = [job.title for job in sorted_career]
        companies = [job.company for job in sorted_career]
        levels = [self._get_seniority_level(title) for title in titles]
        
        # Calculate progression trend
        if len(levels) > 1:
            progression_trend = levels[-1] - levels[0]
            is_upward = progression_trend > 0
        else:
            progression_trend = 0
            is_upward = False
        
        return {
            'titles': titles,
            'companies': companies,
            'seniority_levels': levels,
            'progression_trend': progression_trend,
            'is_upward_trend': is_upward,
            'total_levels_gained': max(levels) - min(levels) if levels else 0
        }