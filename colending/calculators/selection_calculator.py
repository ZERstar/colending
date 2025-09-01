from decimal import Decimal
from typing import List, Dict, Optional
import random
import logging

from ..models import LenderData, SelectionScore, OptimizedTerms

logger = logging.getLogger(__name__)


def calculate_selection_scores(
    lenders_with_profits: List[Dict[str, any]]
) -> List[SelectionScore]:
    """
    Calculate selection scores for lenders using formula:
    Selection_Score_i = Allocated_Limit_i / Approval_Rate_i
    
    Args:
        lenders_with_profits: List of dicts containing lender data with profits
        Format: [{
            'lender_id': str,
            'profit_percentage': Decimal,
            'approval_rate': Decimal,
            'allocated_limit': Decimal
        }]
        
    Returns:
        List of SelectionScore objects with normalized scores and ranges
    """
    if not lenders_with_profits:
        return []
    
    scores = []
    
    # Calculate raw scores
    for lender_data in lenders_with_profits:
        if lender_data['approval_rate'] <= 0:
            logger.warning(f"Lender {lender_data['lender_id']} has zero approval rate, skipping")
            continue
            
        raw_score = lender_data['allocated_limit'] / lender_data['approval_rate']
        scores.append({
            'lender_id': lender_data['lender_id'],
            'raw_score': raw_score,
            'profit_percentage': lender_data['profit_percentage']
        })
    
    if not scores:
        return []
    
    # Calculate total raw score for normalization
    total_raw_score = sum(score['raw_score'] for score in scores)
    
    # Normalize scores to integers that sum to 1000 (for better distribution)
    selection_scores = []
    cumulative_sum = 0
    
    for i, score_data in enumerate(scores):
        # Calculate normalized score as percentage * 10 for integer precision
        normalized_score = int((score_data['raw_score'] / total_raw_score) * 1000)
        
        # Ensure we don't exceed 1000 due to rounding
        if i == len(scores) - 1:
            normalized_score = 1000 - cumulative_sum
        
        # Create cumulative range for this lender
        range_start = cumulative_sum
        range_end = cumulative_sum + normalized_score
        
        selection_score = SelectionScore(
            lender_id=score_data['lender_id'],
            raw_score=score_data['raw_score'],
            normalized_score=normalized_score,
            cumulative_range=(range_start, range_end)
        )
        
        selection_scores.append(selection_score)
        cumulative_sum += normalized_score
        
        logger.debug(f"Lender {score_data['lender_id']}: raw_score={score_data['raw_score']:.2f}, "
                    f"normalized={normalized_score}, range=({range_start}, {range_end})")
    
    return selection_scores


def select_lender_random(
    selection_scores: List[SelectionScore],
    random_seed: Optional[int] = None
) -> str:
    """
    Select a lender using weighted random selection based on selection scores.
    
    Args:
        selection_scores: List of SelectionScore objects with cumulative ranges
        random_seed: Optional seed for reproducible results
        
    Returns:
        Selected lender_id
        
    Raises:
        ValueError: If no lenders provided or invalid scores
    """
    if not selection_scores:
        raise ValueError("No lenders provided for selection")
    
    if random_seed is not None:
        random.seed(random_seed)
    
    # Generate random number between 0 and 999 (inclusive)
    random_number = random.randint(0, 999)
    
    # Find which lender this random number falls into
    for score in selection_scores:
        range_start, range_end = score.cumulative_range
        if range_start <= random_number < range_end:
            logger.debug(f"Random number {random_number} selected lender {score.lender_id} "
                        f"(range: {range_start}-{range_end})")
            return score.lender_id
    
    # Fallback to last lender if no match (shouldn't happen with proper ranges)
    logger.warning(f"Random number {random_number} didn't match any range, selecting last lender")
    return selection_scores[-1].lender_id


def validate_selection_distribution(
    selection_scores: List[SelectionScore],
    num_trials: int = 1000
) -> Dict[str, float]:
    """
    Validate selection distribution by running multiple trials.
    
    Args:
        selection_scores: List of SelectionScore objects
        num_trials: Number of trials to run
        
    Returns:
        Dict mapping lender_id to actual selection percentage
    """
    if not selection_scores:
        return {}
    
    selection_counts = {score.lender_id: 0 for score in selection_scores}
    
    for _ in range(num_trials):
        selected_lender = select_lender_random(selection_scores)
        selection_counts[selected_lender] += 1
    
    # Convert to percentages
    actual_distribution = {
        lender_id: (count / num_trials) * 100
        for lender_id, count in selection_counts.items()
    }
    
    # Log comparison with expected distribution
    logger.info("Selection distribution validation:")
    for score in selection_scores:
        expected_pct = (score.normalized_score / 1000) * 100
        actual_pct = actual_distribution[score.lender_id]
        logger.info(f"Lender {score.lender_id}: Expected {expected_pct:.1f}%, "
                   f"Actual {actual_pct:.1f}%, Diff {abs(expected_pct - actual_pct):.1f}%")
    
    return actual_distribution


def calculate_expected_distribution(
    lenders: List[LenderData]
) -> Dict[str, float]:
    """
    Calculate expected selection distribution percentages for given lenders.
    
    Args:
        lenders: List of LenderData objects
        
    Returns:
        Dict mapping lender_id to expected selection percentage
    """
    if not lenders:
        return {}
    
    # Calculate raw scores
    raw_scores = {}
    for lender in lenders:
        if lender.approval_rate > 0:
            raw_scores[lender.lender_id] = lender.allocated_limit / lender.approval_rate
    
    if not raw_scores:
        return {}
    
    # Calculate total and percentages
    total_score = sum(raw_scores.values())
    expected_distribution = {
        lender_id: (score / total_score) * 100
        for lender_id, score in raw_scores.items()
    }
    
    return expected_distribution