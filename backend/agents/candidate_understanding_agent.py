"""
Candidate Understanding Agent - Extracts structured information from candidate profiles
"""

import logging
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
import re

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.models import Candidate, Skill, CareerHistory
from backend.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CandidateUnderstandingAgent:
    """Extracts and structures candidate information for matching"""
    
    def __init__(self):
        self.skill_categories = self._initialize_skill_categories()
        self.seniority_indicators = self._initialize_seniority_indicators()
        self.leadership_keywords = self._initialize_leadership_keywords()
    
    def _initialize_skill_categories(self) -> Dict[str, List[str]]:
        """Initialize skill categories for better matching"""
        return {
            'ml_ai': ['machine learning', 'deep learning', 'nlp', 'computer vision', 
                     'artificial intelligence', 'ml', 'ai', 'neural networks', 
                     'transformers', 'llm', 'generative ai'],
            'data_engineering': ['spark', 'airflow', 'kafka', 'data pipeline', 'etl',
                               'data warehouse', 'snowflake', 'dbt', 'sql',
                               'data engineering'],
            'backend': ['python', 'java', 'go', 'rust', 'api', 'rest', 'graphql',
                       'microservices', 'django', 'flask', 'fastapi'],
            'infrastructure': ['aws', 'gcp', 'azure', 'docker', 'kubernetes', 
                              'terraform', 'ci/cd', 'devops'],
            'databases': ['postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch',
                          'vector database', 'pinecone', 'weaviate', 'milvus', 'faiss'],
            'mlops': ['mlops', 'mlflow', 'kubeflow', 'experiment tracking',
                     'model deployment', 'model serving'],
            'research': ['pytorch', 'tensorflow', 'jax', 'research', 'paper',
                        'arxiv', 'publication', 'conference'],
            'web_frontend': ['react', 'angular', 'vue', 'javascript', 'typescript',
                            'frontend', 'css', 'html']
        }
    
    def _initialize_seniority_indicators(self) -> Dict[str, List[str]]:
        """Initialize indicators of seniority level"""
        return {
            'senior': ['senior', 'sr.', 'lead', 'principal', 'staff', 'head of',
                      'chief', 'vp', 'director', 'architect'],
            'mid': ['mid-level', 'experienced', 'software engineer ii', 'engineer ii'],
            'junior': ['junior', 'jr.', 'associate', 'entry level', 'intern']
        }
    
    def _initialize_leadership_keywords(self) -> List[str]:
        """Initialize leadership-related keywords"""
        return ['led', 'lead', 'managed', 'mentored', 'supervised', 'guided',
                'coordinated', 'headed', 'directed', 'oversaw', 'spearheaded',
                'built team', 'team lead', 'manager', 'head', 'principal']
    
    def analyze_candidate(self, candidate: Candidate) -> Dict[str, Any]:
        """Perform comprehensive candidate analysis"""
        analysis = {
            'candidate_id': candidate.candidate_id,
            'skills_analysis': self._analyze_skills(candidate),
            'seniority_analysis': self._analyze_seniority(candidate),
            'career_trajectory': self._analyze_career_trajectory(candidate),
            'domain_expertise': self._analyze_domain_expertise(candidate),
            'leadership_signals': self._analyze_leadership(candidate),
            'growth_signals': self._analyze_growth(candidate),
            'stability_signals': self._analyze_stability(candidate),
            'achievement_signals': self._analyze_achievements(candidate),
            'education_analysis': self._analyze_education(candidate)
        }
        
        return analysis
    
    def _analyze_skills(self, candidate: Candidate) -> Dict[str, Any]:
        """Analyze candidate skills"""
        skills = candidate.get_skills_list()
        skill_objects = candidate.skills
        
        # Categorize skills
        categorized_skills = {category: [] for category in self.skill_categories.keys()}
        skill_proficiency = {}
        skill_endorsements = {}
        skill_duration = {}
        
        for skill_obj in skill_objects:
            skill_name = skill_obj.name.lower()
            categorized = False
            
            # Categorize skill
            for category, keywords in self.skill_categories.items():
                if any(keyword in skill_name for keyword in keywords):
                    categorized_skills[category].append(skill_name)
                    categorized = True
                    break
            
            if not categorized:
                categorized_skills['other'] = categorized_skills.get('other', [])
                categorized_skills['other'].append(skill_name)
            
            # Track proficiency, endorsements, and duration
            skill_proficiency[skill_name] = skill_obj.proficiency
            skill_endorsements[skill_name] = skill_obj.endorsements
            skill_duration[skill_name] = skill_obj.duration_months
        
        # Calculate skill depth score
        advanced_skills = sum(1 for s in skills if skill_proficiency.get(s, '') in ['advanced', 'expert'])
        skill_depth_score = advanced_skills / len(skills) if skills else 0
        
        return {
            'total_skills': len(skills),
            'categorized_skills': categorized_skills,
            'skill_proficiency': skill_proficiency,
            'skill_endorsements': skill_endorsements,
            'skill_duration': skill_duration,
            'skill_depth_score': skill_depth_score,
            'top_skills_by_endorsements': sorted(skills, key=lambda x: skill_endorsements.get(x, 0), reverse=True)[:10],
            'top_skills_by_duration': sorted(skills, key=lambda x: skill_duration.get(x, 0), reverse=True)[:10]
        }
    
    def _analyze_seniority(self, candidate: Candidate) -> Dict[str, Any]:
        """Analyze candidate seniority level"""
        years_experience = candidate.profile.years_of_experience
        job_titles = candidate.get_job_titles()
        
        # Determine seniority from titles
        seniority_scores = {'senior': 0, 'mid': 0, 'junior': 0}
        
        for title in job_titles:
            title_lower = title.lower()
            for level, keywords in self.seniority_indicators.items():
                if any(keyword in title_lower for keyword in keywords):
                    seniority_scores[level] += 1
        
        # Determine overall seniority
        if seniority_scores['senior'] >= 2:
            seniority_level = 'senior'
        elif seniority_scores['mid'] >= 2 or years_experience >= 5:
            seniority_level = 'mid'
        elif seniority_scores['junior'] >= 1 or years_experience < 3:
            seniority_level = 'junior'
        else:
            seniority_level = 'mid'  # Default to mid
        
        return {
            'years_of_experience': years_experience,
            'seniority_level': seniority_level,
            'title_progression': job_titles,
            'seniority_scores': seniority_scores,
            'is_senior': seniority_level == 'senior'
        }
    
    def _analyze_career_trajectory(self, candidate: Candidate) -> Dict[str, Any]:
        """Analyze career progression"""
        career_history = candidate.career_history
        
        # Sort by start date
        sorted_career = sorted(career_history, key=lambda x: x.start_date)
        
        # Analyze progression
        title_progression = [job.title for job in sorted_career]
        company_progression = [job.company for job in sorted_career]
        
        # Detect promotions (title changes indicating growth)
        promotions = 0
        for i in range(1, len(sorted_career)):
            prev_title = sorted_career[i-1].title.lower()
            curr_title = sorted_career[i].title.lower()
            
            # Simple heuristic: promotion if seniority increases
            prev_is_senior = any(kw in prev_title for kw in self.seniority_indicators['senior'])
            curr_is_senior = any(kw in curr_title for kw in self.seniority_indicators['senior'])
            
            if not prev_is_senior and curr_is_senior:
                promotions += 1
        
        # Analyze company changes
        company_changes = sum(1 for i in range(1, len(company_progression)) 
                            if company_progression[i] != company_progression[i-1])
        
        return {
            'career_length_years': candidate.get_total_experience_months() / 12,
            'title_progression': title_progression,
            'company_progression': company_progression,
            'total_roles': len(career_history),
            'promotions_detected': promotions,
            'company_changes': company_changes,
            'avg_tenure_months': sum(job.duration_months for job in career_history) / len(career_history) if career_history else 0
        }
    
    def _analyze_domain_expertise(self, candidate: Candidate) -> Dict[str, Any]:
        """Analyze domain expertise"""
        industries = [job.industry for job in candidate.career_history]
        current_industry = candidate.profile.current_industry
        
        # Count industry experience
        industry_experience = {}
        for industry in industries:
            industry_experience[industry] = industry_experience.get(industry, 0) + 1
        
        # Determine primary domain
        primary_domain = max(industry_experience, key=industry_experience.get) if industry_experience else current_industry
        
        # Check for product company experience
        has_product_experience = any('services' not in industry.lower() for industry in industries)
        
        return {
            'industries': industries,
            'primary_domain': primary_domain,
            'industry_experience': industry_experience,
            'has_product_company_experience': has_product_experience,
            'domain_diversity': len(industries)
        }
    
    def _analyze_leadership(self, candidate: Candidate) -> Dict[str, Any]:
        """Analyze leadership signals"""
        leadership_score = 0
        leadership_evidence = []
        
        # Check titles for leadership indicators
        for title in candidate.get_job_titles():
            title_lower = title.lower()
            for keyword in self.leadership_keywords:
                if keyword in title_lower:
                    leadership_score += 1
                    leadership_evidence.append(f"Title: {title}")
                    break
        
        # Check job descriptions for leadership keywords
        for job in candidate.career_history:
            description_lower = job.description.lower()
            for keyword in self.leadership_keywords:
                if keyword in description_lower:
                    leadership_score += 1
                    leadership_evidence.append(f"Leadership in {job.title} at {job.company}")
                    break
        
        # Check for team size indicators
        for job in candidate.career_history:
            if 'team' in job.description.lower() or 'manage' in job.description.lower():
                leadership_score += 0.5
        
        return {
            'leadership_score': leadership_score,
            'has_leadership_experience': leadership_score > 0,
            'leadership_evidence': leadership_evidence[:5]  # Limit to top 5
        }
    
    def _analyze_growth(self, candidate: Candidate) -> Dict[str, Any]:
        """Analyze growth signals"""
        career_trajectory = self._analyze_career_trajectory(candidate)
        
        # Growth indicators
        growth_score = 0
        growth_evidence = []
        
        # Career progression
        if career_trajectory['promotions_detected'] > 0:
            growth_score += career_trajectory['promotions_detected'] * 2
            growth_evidence.append(f"{career_trajectory['promotions_detected']} promotions detected")
        
        # Increasing responsibility
        if len(career_trajectory['title_progression']) > 1:
            # Simple heuristic: later roles should be more senior
            first_title = career_trajectory['title_progression'][0].lower()
            last_title = career_trajectory['title_progression'][-1].lower()
            
            first_is_senior = any(kw in first_title for kw in self.seniority_indicators['senior'])
            last_is_senior = any(kw in last_title for kw in self.seniority_indicators['senior'])
            
            if not first_is_senior and last_is_senior:
                growth_score += 2
                growth_evidence.append("Career progression to senior role")
        
        # Skill growth (learning new skills)
        skill_durations = {}
        for skill in candidate.skills:
            if skill.duration_months > 0:
                skill_durations[skill.name] = skill.duration_months
        
        recent_skills = [name for name, duration in skill_durations.items() if duration < 12]
        if len(recent_skills) >= 3:
            growth_score += 1
            growth_evidence.append(f"Recently learned {len(recent_skills)} new skills")
        
        return {
            'growth_score': growth_score,
            'growth_evidence': growth_evidence
        }
    
    def _analyze_stability(self, candidate: Candidate) -> Dict[str, Any]:
        """Analyze job stability"""
        career_trajectory = self._analyze_career_trajectory(candidate)
        
        avg_tenure = career_trajectory['avg_tenure_months']
        company_changes = career_trajectory['company_changes']
        
        # Stability score (higher is more stable)
        stability_score = 0
        
        if avg_tenure >= 36:  # 3+ years average
            stability_score += 2
        elif avg_tenure >= 24:  # 2+ years average
            stability_score += 1
        
        if company_changes <= 2:
            stability_score += 1
        
        return {
            'avg_tenure_months': avg_tenure,
            'company_changes': company_changes,
            'stability_score': stability_score,
            'is_stable': stability_score >= 2
        }
    
    def _analyze_achievements(self, candidate: Candidate) -> Dict[str, Any]:
        """Analyze achievement signals"""
        achievement_score = 0
        achievement_evidence = []
        
        # Look for quantified metrics in job descriptions
        metric_patterns = [
            r'(\d+%)',  # percentages
            r'(\d+\+?\s*(?:users|customers|clients|projects|team members))',  # impact numbers
            r'(\$[\d,]+)',  # monetary impact
            r'(\d+x\s*(?:improvement|increase|growth|reduction))',  # multipliers
        ]
        
        for job in candidate.career_history:
            description = job.description
            
            for pattern in metric_patterns:
                matches = re.findall(pattern, description, re.IGNORECASE)
                if matches:
                    achievement_score += len(matches) * 0.5
                    achievement_evidence.extend(matches[:2])  # Limit evidence
        
        # Check for awards or recognition
        summary_lower = candidate.profile.summary.lower()
        if any(word in summary_lower for word in ['award', 'recognized', 'published', 'patent', 'conference']):
            achievement_score += 2
            achievement_evidence.append("Awards/recognition detected")
        
        # GitHub activity
        if candidate.redrob_signals.github_activity_score > 50:
            achievement_score += 1
            achievement_evidence.append(f"High GitHub activity ({candidate.redrob_signals.github_activity_score})")
        
        return {
            'achievement_score': achievement_score,
            'achievement_evidence': achievement_evidence[:5]
        }
    
    def _analyze_education(self, candidate: Candidate) -> Dict[str, Any]:
        """Analyze education background"""
        education = candidate.education
        
        if not education:
            return {
                'has_education': False,
                'education_count': 0,
                'highest_degree': None,
                'institution_tier': None
            }
        
        # Determine highest degree
        degree_hierarchy = {
            'phd': 5, 'doctor': 5,
            'master': 4, 'm.s.': 4, 'm.sc': 4, 'm.e.': 4,
            'bachelor': 3, 'b.s.': 3, 'b.e.': 3, 'b.tech': 3,
            'associate': 2,
            'diploma': 1
        }
        
        highest_level = 0
        highest_degree = None
        
        for edu in education:
            degree_lower = edu.degree.lower()
            for degree_name, level in degree_hierarchy.items():
                if degree_name in degree_lower and level > highest_level:
                    highest_level = level
                    highest_degree = edu.degree
        
        # Get institution tier
        institution_tiers = [edu.tier for edu in education if edu.tier]
        best_tier = min(institution_tiers, key=lambda x: int(x.split('_')[1])) if institution_tiers else None
        
        return {
            'has_education': True,
            'education_count': len(education),
            'highest_degree': highest_degree,
            'highest_level': highest_level,
            'institution_tier': best_tier,
            'fields_of_study': [edu.field_of_study for edu in education]
        }
    
    def extract_candidate_embedding_text(self, candidate: Candidate) -> str:
        """Extract text for embedding generation"""
        return candidate.get_full_text()
    
    def get_candidate_summary(self, candidate: Candidate) -> str:
        """Generate a comprehensive candidate summary"""
        analysis = self.analyze_candidate(candidate)
        
        summary_parts = [
            f"Candidate {candidate.candidate_id}: {candidate.profile.anonymized_name}",
            f"Role: {candidate.profile.current_title} at {candidate.profile.current_company}",
            f"Experience: {candidate.profile.years_of_experience} years",
            f"Location: {candidate.profile.location}, {candidate.profile.country}",
            f"Seniority: {analysis['seniority_analysis']['seniority_level']}",
            f"Primary Domain: {analysis['domain_expertise']['primary_domain']}",
            f"Total Skills: {analysis['skills_analysis']['total_skills']}",
            f"Leadership Score: {analysis['leadership_signals']['leadership_score']}",
            f"Growth Score: {analysis['growth_signals']['growth_score']}",
            f"Stability Score: {analysis['stability_signals']['stability_score']}"
        ]
        
        return "\n".join(summary_parts)