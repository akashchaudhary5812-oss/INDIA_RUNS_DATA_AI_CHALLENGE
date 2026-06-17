"""
Evaluation Metrics Module - Implements ranking quality metrics
"""

import logging
from typing import List, Dict, Set, Tuple
import numpy as np
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.models import CandidateScore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EvaluationMetrics:
    """Calculate various ranking quality metrics"""
    
    def __init__(self, k_values: List[int] = [5, 10, 20, 50, 100]):
        self.k_values = k_values
    
    def calculate_precision_at_k(self, ranked_results: List[CandidateScore], 
                                 relevant_ids: Set[str], k: int) -> float:
        """Calculate Precision@K"""
        if k > len(ranked_results):
            k = len(ranked_results)
        
        top_k = ranked_results[:k]
        relevant_in_top_k = sum(1 for score in top_k if score.candidate_id in relevant_ids)
        
        return relevant_in_top_k / k if k > 0 else 0.0
    
    def calculate_recall_at_k(self, ranked_results: List[CandidateScore],
                              relevant_ids: Set[str], k: int) -> float:
        """Calculate Recall@K"""
        if k > len(ranked_results):
            k = len(ranked_results)
        
        if not relevant_ids:
            return 0.0
        
        top_k = ranked_results[:k]
        relevant_in_top_k = sum(1 for score in top_k if score.candidate_id in relevant_ids)
        
        return relevant_in_top_k / len(relevant_ids)
    
    def calculate_mrr(self, ranked_results: List[CandidateScore], 
                     relevant_ids: Set[str]) -> float:
        """Calculate Mean Reciprocal Rank"""
        for i, score in enumerate(ranked_results, 1):
            if score.candidate_id in relevant_ids:
                return 1.0 / i
        
        return 0.0
    
    def calculate_ndcg(self, ranked_results: List[CandidateScore], 
                      relevant_ids: Set[str], k: int) -> float:
        """Calculate Normalized Discounted Cumulative Gain at K"""
        if k > len(ranked_results):
            k = len(ranked_results)
        
        dcg = 0.0
        for i, score in enumerate(ranked_results[:k], 1):
            if score.candidate_id in relevant_ids:
                # Binary relevance: 1 if relevant, 0 otherwise
                dcg += 1.0 / np.log2(i + 1)
        
        # Ideal DCG: all relevant items ranked first
        ideal_dcg = 0.0
        num_relevant = min(len(relevant_ids), k)
        for i in range(1, num_relevant + 1):
            ideal_dcg += 1.0 / np.log2(i + 1)
        
        return dcg / ideal_dcg if ideal_dcg > 0 else 0.0
    
    def calculate_ranking_accuracy(self, ranked_results: List[CandidateScore],
                                  relevant_ids: Set[str]) -> float:
        """Calculate simple ranking accuracy (fraction of relevant in top half)"""
        if not ranked_results:
            return 0.0
        
        half_point = len(ranked_results) // 2
        top_half = ranked_results[:half_point]
        
        relevant_in_top_half = sum(1 for score in top_half if score.candidate_id in relevant_ids)
        total_relevant = sum(1 for score in ranked_results if score.candidate_id in relevant_ids)
        
        return relevant_in_top_half / total_relevant if total_relevant > 0 else 0.0
    
    def calculate_fairness_metrics(self, ranked_results: List[CandidateScore]) -> Dict[str, float]:
        """Calculate fairness-related metrics"""
        # Score distribution by group would require group labels
        # For now, calculate overall score distribution metrics
        
        scores = [score.final_score for score in ranked_results]
        
        fairness_metrics = {
            'score_mean': np.mean(scores),
            'score_std': np.std(scores),
            'score_min': np.min(scores),
            'score_max': np.max(scores),
            'score_median': np.median(scores),
            'score_range': np.max(scores) - np.min(scores)
        }
        
        return fairness_metrics
    
    def evaluate_ranking(self, ranked_results: List[CandidateScore],
                        relevant_ids: Set[str]) -> Dict[str, Dict[str, float]]:
        """Calculate all evaluation metrics"""
        results = {}
        
        # Precision@K for various K values
        precision_results = {}
        for k in self.k_values:
            precision_results[f'precision@{k}'] = self.calculate_precision_at_k(
                ranked_results, relevant_ids, k
            )
        results['precision'] = precision_results
        
        # Recall@K for various K values
        recall_results = {}
        for k in self.k_values:
            recall_results[f'recall@{k}'] = self.calculate_recall_at_k(
                ranked_results, relevant_ids, k
            )
        results['recall'] = recall_results
        
        # MRR
        results['mrr'] = {'mrr': self.calculate_mrr(ranked_results, relevant_ids)}
        
        # NDCG@K for various K values
        ndcg_results = {}
        for k in self.k_values:
            ndcg_results[f'ndcg@{k}'] = self.calculate_ndcg(ranked_results, relevant_ids, k)
        results['ndcg'] = ndcg_results
        
        # Ranking accuracy
        results['ranking_accuracy'] = {
            'ranking_accuracy': self.calculate_ranking_accuracy(ranked_results, relevant_ids)
        }
        
        # Fairness metrics
        results['fairness'] = self.calculate_fairness_metrics(ranked_results)
        
        return results
    
    def generate_evaluation_report(self, evaluation_results: Dict[str, Dict[str, float]]) -> str:
        """Generate a human-readable evaluation report"""
        
        report = "TalentMind AI Evaluation Report\n"
        report += "=" * 50 + "\n\n"
        
        # Precision@K
        report += "Precision@K:\n"
        for k, value in evaluation_results['precision'].items():
            report += f"  {k}: {value:.4f}\n"
        report += "\n"
        
        # Recall@K
        report += "Recall@K:\n"
        for k, value in evaluation_results['recall'].items():
            report += f"  {k}: {value:.4f}\n"
        report += "\n"
        
        # MRR
        report += f"MRR: {evaluation_results['mrr']['mrr']:.4f}\n\n"
        
        # NDCG@K
        report += "NDCG@K:\n"
        for k, value in evaluation_results['ndcg'].items():
            report += f"  {k}: {value:.4f}\n"
        report += "\n"
        
        # Ranking accuracy
        report += f"Ranking Accuracy: {evaluation_results['ranking_accuracy']['ranking_accuracy']:.4f}\n\n"
        
        # Fairness metrics
        report += "Score Distribution:\n"
        for metric, value in evaluation_results['fairness'].items():
            report += f"  {metric}: {value:.4f}\n"
        
        return report
    
    def compare_with_baseline(self, our_results: List[CandidateScore],
                            baseline_results: List[CandidateScore],
                            relevant_ids: Set[str]) -> Dict[str, Dict[str, float]]:
        """Compare our results with a baseline ranking"""
        
        our_metrics = self.evaluate_ranking(our_results, relevant_ids)
        baseline_metrics = self.evaluate_ranking(baseline_results, relevant_ids)
        
        comparison = {}
        
        # Calculate improvements
        for metric_category in our_metrics:
            if metric_category in baseline_metrics:
                comparison[metric_category] = {}
                for metric_name in our_metrics[metric_category]:
                    our_value = our_metrics[metric_category][metric_name]
                    baseline_value = baseline_metrics[metric_category].get(metric_name, 0)
                    
                    improvement = our_value - baseline_value
                    relative_improvement = (improvement / baseline_value * 100) if baseline_value > 0 else 0
                    
                    comparison[metric_category][metric_name] = {
                        'our_value': our_value,
                        'baseline_value': baseline_value,
                        'absolute_improvement': improvement,
                        'relative_improvement': relative_improvement
                    }
        
        return comparison