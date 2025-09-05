"""
Test cases for core mathematical functions.
"""

import pytest
from app.core.math import (
    calc_blended_rate, calc_orig_profit, calc_lender_profit,
    calc_selection_score, normalize_scores, weighted_random_select
)


def test_blended_rate_calculation():
    """Test core blended rate formula"""
    # Test case from specification: R_B = (w_O × R_O) + (w_L × R_L)
    # With orig_rate=16.5%, lender_rate=14.2%, orig_weight=25%
    rate = calc_blended_rate(0.165, 0.142, 0.25)
    expected = (0.25 * 0.165) + (0.75 * 0.142)  # 0.14775
    
    assert abs(rate - expected) < 0.0001
    assert abs(rate - 0.14775) < 0.0001


def test_profit_calculations():
    """Test dual profit formulas"""
    # Test originator profit: P_originator = (w_O × R_B) + S_O - (w_O × C_O)
    blended_rate = 0.14775
    orig_weight = 0.25
    service_fee = 0.018
    orig_cost = 0.092
    
    orig_profit = calc_orig_profit(orig_weight, blended_rate, service_fee, orig_cost)
    expected_orig = (0.25 * 0.14775) + 0.018 - (0.25 * 0.092)
    
    assert abs(orig_profit - expected_orig) < 0.0001
    
    # Test lender profit: P_lender = (w_L × R_B) - (w_L × C_L) - S_L
    lender_weight = 0.75
    lender_cost = 0.085
    
    lender_profit = calc_lender_profit(lender_weight, blended_rate, lender_cost, service_fee)
    expected_lender = (0.75 * 0.14775) - (0.75 * 0.085) - 0.018
    
    assert abs(lender_profit - expected_lender) < 0.0001


def test_selection_score():
    """Test selection score calculation"""
    # Test Selection_Score = Allocated_Limit / Approval_Rate
    score = calc_selection_score(1000000, 0.8)
    expected = 1000000 / 0.8
    
    assert score == expected
    
    # Test zero approval rate
    score_zero = calc_selection_score(1000000, 0)
    assert score_zero == 0


def test_normalize_scores():
    """Test score normalization"""
    scores = [1000, 2000, 3000]
    normalized = normalize_scores(scores)
    
    # Should normalize to [100, 200, 300] (min_score = 1000)
    expected = [100, 200, 300]
    assert normalized == expected
    
    # Test empty list
    assert normalize_scores([]) == []
    
    # Test with negative/zero scores
    assert normalize_scores([0, -1, 2]) == [100, 100, 100]


def test_weighted_selection_distribution():
    """Test weighted random selection converges to expected distribution"""
    scores = [350, 280, 210]  # Should give roughly 35%, 28%, 21% distribution
    
    # Run many selections and check distribution
    selections = []
    for _ in range(10000):
        selected = weighted_random_select(scores)
        selections.append(selected)
    
    # Count selections
    counts = [0, 0, 0]
    for selection in selections:
        counts[selection] += 1
    
    # Convert to percentages
    percentages = [count / len(selections) * 100 for count in counts]
    
    # Should be roughly proportional to scores
    total_score = sum(scores)
    expected_percentages = [score / total_score * 100 for score in scores]
    
    # Allow 2% tolerance for randomness
    for actual, expected in zip(percentages, expected_percentages):
        assert abs(actual - expected) < 3.0  # 3% tolerance for randomness


def test_weighted_selection_edge_cases():
    """Test edge cases for weighted selection"""
    # Test empty list
    result = weighted_random_select([])
    assert result == 0
    
    # Test single item
    result = weighted_random_select([100])
    assert result == 0
    
    # Test all zeros
    result = weighted_random_select([0, 0, 0])
    assert result == 0