"""
Core mathematical functions for co-lending calculations.
"""

import random
from typing import List


def calc_blended_rate(orig_rate: float, lender_rate: float, orig_weight: float) -> float:
    """
    Calculate blended rate: R_B = (w_O × R_O) + (w_L × R_L)
    
    Args:
        orig_rate: Originator interest rate
        lender_rate: Lender interest rate  
        orig_weight: Originator weight (lender weight = 1 - orig_weight)
        
    Returns:
        Blended interest rate
    """
    return (orig_weight * orig_rate) + ((1 - orig_weight) * lender_rate)


def calc_orig_profit(orig_weight: float, blended_rate: float, service_fee: float, cost_funds: float) -> float:
    """
    Calculate originator profit: P_originator = (w_O × R_B) + S_O - (w_O × C_O)
    
    Args:
        orig_weight: Originator weight
        blended_rate: Blended interest rate
        service_fee: Service fee rate
        cost_funds: Originator cost of funds
        
    Returns:
        Originator profit rate
    """
    return (orig_weight * blended_rate) + service_fee - (orig_weight * cost_funds)


def calc_lender_profit(lender_weight: float, blended_rate: float, cost_funds: float, service_fee: float) -> float:
    """
    Calculate lender profit: P_lender = (w_L × R_B) - (w_L × C_L) - S_L
    
    Args:
        lender_weight: Lender weight
        blended_rate: Blended interest rate
        cost_funds: Lender cost of funds
        service_fee: Service fee paid to originator
        
    Returns:
        Lender profit rate
    """
    return (lender_weight * blended_rate) - (lender_weight * cost_funds) - service_fee


def calc_selection_score(limit: float, approval_rate: float) -> float:
    """
    Calculate selection score: Selection_Score = Allocated_Limit / Approval_Rate
    
    Args:
        limit: Available/allocated limit
        approval_rate: Historical approval rate
        
    Returns:
        Selection score for weighted random selection
    """
    return limit / approval_rate if approval_rate > 0 else 0


def normalize_scores(scores: List[float]) -> List[int]:
    """
    Convert scores to whole numbers for bucketing algorithm.
    
    Args:
        scores: List of selection scores
        
    Returns:
        List of normalized integer scores
    """
    if not scores:
        return []
    
    min_score = min(scores)
    if min_score <= 0:
        return [100] * len(scores)
    
    return [round((score / min_score) * 100) for score in scores]


def weighted_random_select(normalized_scores: List[int]) -> int:
    """
    Select index based on cumulative distribution using weighted random selection.
    
    Args:
        normalized_scores: List of normalized integer scores
        
    Returns:
        Selected index
    """
    if not normalized_scores:
        return 0
    
    total = sum(normalized_scores)
    if total == 0:
        return 0
    
    rand_num = random.randint(1, total)
    cumulative = 0
    
    for i, score in enumerate(normalized_scores):
        cumulative += score
        if rand_num <= cumulative:
            return i
    
    return 0