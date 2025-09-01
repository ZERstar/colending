# -*- coding: utf-8 -*-
import unittest
from decimal import Decimal
import sys
import os

# Add parent directory to path to import colending package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from colending.calculators import (
    calculate_blended_rate, 
    calculate_profits,
    optimize_participation_ratio,
    calculate_selection_scores,
    select_lender_random,
    validate_selection_distribution
)
from colending.models import LoanTerms, CostParameters, LenderData, LoanRequest
from colending.services import LoanProcessor


class TestBlendedRateCalculation(unittest.TestCase):
    """Test blended rate calculations"""
    
    def test_basic_blended_rate(self):
        """Test Case 1: Basic Calculation from requirements"""
        # Input: R_O=16.5%, R_L=14.2%, w_O=0.25, w_L=0.75
        # Expected Blended: 14.775%
        
        blended_rate = calculate_blended_rate(
            originator_rate=Decimal('0.165'),
            lender_rate=Decimal('0.142'),
            originator_weight=Decimal('0.25'),
            lender_weight=Decimal('0.75')
        )
        
        expected = Decimal('0.14775')
        self.assertAlmostEqual(blended_rate, expected, places=5)
    
    def test_weight_validation(self):
        """Test that weights must sum to 1.0"""
        with self.assertRaises(ValueError):
            calculate_blended_rate(
                originator_rate=0.165,
                lender_rate=0.142,
                originator_weight=0.6,
                lender_weight=0.5  # Sum = 1.1, should fail
            )
    
    def test_equal_rates(self):
        """Test with equal rates"""
        blended_rate = calculate_blended_rate(
            originator_rate=0.15,
            lender_rate=0.15,
            originator_weight=0.3,
            lender_weight=0.7
        )
        
        self.assertAlmostEqual(blended_rate, Decimal('0.15'), places=5)


class TestProfitCalculation(unittest.TestCase):
    """Test profit calculations"""
    
    def test_basic_profit_calculation(self):
        """Test Case 2: Profit Calculation from requirements"""
        # Input: R_O=16.5%, R_L=14.2%, w_O=0.25, w_L=0.75
        # Additional: S=1.8%, C_O=9.2%, C_L=8.5%
        # Expected Originator Profit: 3.194%
        # Expected Lender Profit: 2.906%
        
        loan_terms = LoanTerms(
            originator_rate=Decimal('0.165'),
            lender_rate=Decimal('0.142'),
            originator_weight=Decimal('0.25'),
            lender_weight=Decimal('0.75'),
            loan_amount=Decimal('100000'),
            servicing_fee_rate=Decimal('0.018')
        )
        
        cost_params = CostParameters(
            originator_cost_of_funds=Decimal('0.092'),
            lender_cost_of_funds=Decimal('0.085'),
            servicing_fee_rate=Decimal('0.018')
        )
        
        result = calculate_profits(loan_terms, cost_params)
        
        self.assertAlmostEqual(result.blended_rate, Decimal('0.14775'), places=5)
        self.assertAlmostEqual(result.originator_profit, Decimal('0.03194'), places=4)
        self.assertAlmostEqual(result.lender_profit, Decimal('0.02906'), places=4)
        self.assertTrue(result.both_profitable)


class TestOptimizationCalculation(unittest.TestCase):
    """Test participation ratio optimization"""
    
    def test_optimization_finds_profitable_ratio(self):
        """Test that optimization finds profitable ratios"""
        result = optimize_participation_ratio(
            originator_rate=0.165,
            lender_rate=0.142,
            loan_amount=100000,
            originator_cost_of_funds=0.092,
            lender_cost_of_funds=0.085,
            servicing_fee_rate=0.018
        )
        
        # Should find a profitable combination
        self.assertTrue(result.both_profitable)
        self.assertGreater(result.originator_profit, 0)
        self.assertGreater(result.lender_profit, 0)
        
        # Weights should sum to 1
        self.assertAlmostEqual(
            result.optimal_originator_weight + result.optimal_lender_weight,
            Decimal('1.0'),
            places=5
        )
    
    def test_optimization_no_profitable_ratio(self):
        """Test optimization when no profitable ratio exists"""
        # Use very high cost of funds to make unprofitable
        result = optimize_participation_ratio(
            originator_rate=0.10,
            lender_rate=0.10,
            loan_amount=100000,
            originator_cost_of_funds=0.15,  # Higher than rates
            lender_cost_of_funds=0.15,
            servicing_fee_rate=0.02
        )
        
        self.assertFalse(result.both_profitable)


class TestSelectionCalculation(unittest.TestCase):
    """Test lender selection calculations"""
    
    def setUp(self):
        """Set up test data matching requirements"""
        # Test Case 3: Selection Algorithm from requirements
        self.test_lenders = [
            {
                'lender_id': 'A',
                'profit_percentage': Decimal('0.032'),
                'approval_rate': Decimal('0.85'),
                'allocated_limit': Decimal('3500000000')  # 35Cr
            },
            {
                'lender_id': 'B', 
                'profit_percentage': Decimal('0.028'),
                'approval_rate': Decimal('0.72'),
                'allocated_limit': Decimal('2800000000')  # 28Cr
            },
            {
                'lender_id': 'C',
                'profit_percentage': Decimal('0.021'),
                'approval_rate': Decimal('0.58'),
                'allocated_limit': Decimal('2100000000')  # 21Cr
            }
        ]
    
    def test_selection_score_calculation(self):
        """Test selection score calculation"""
        selection_scores = calculate_selection_scores(self.test_lenders)
        
        self.assertEqual(len(selection_scores), 3)
        
        # Check that scores are calculated and normalized
        total_normalized = sum(score.normalized_score for score in selection_scores)
        self.assertEqual(total_normalized, 1000)
        
        # Verify cumulative ranges don't overlap
        prev_end = 0
        for score in selection_scores:
            range_start, range_end = score.cumulative_range
            self.assertEqual(range_start, prev_end)
            self.assertGreater(range_end, range_start)
            prev_end = range_end
    
    def test_selection_distribution(self):
        """Test Case 3: Selection Algorithm Distribution"""
        # Expected Distribution: A=35.5%, B=33.3%, C=31.2% (within 2% tolerance)
        
        selection_scores = calculate_selection_scores(self.test_lenders)
        
        # Validate distribution over 1000 runs
        actual_distribution = validate_selection_distribution(selection_scores, 1000)
        
        # Check distributions are within tolerance
        expected_distributions = {'A': 35.5, 'B': 33.3, 'C': 31.2}
        
        for lender_id, expected_pct in expected_distributions.items():
            actual_pct = actual_distribution[lender_id]
            tolerance = 2.0  # within 2% tolerance as per requirements
            
            self.assertAlmostEqual(
                actual_pct, expected_pct, delta=tolerance,
                msg=f"Lender {lender_id}: expected {expected_pct}%, got {actual_pct}%"
            )
    
    def test_zero_approval_rate_handling(self):
        """Test handling of zero approval rates"""
        test_data = [
            {
                'lender_id': 'A',
                'profit_percentage': Decimal('0.03'),
                'approval_rate': Decimal('0.85'),
                'allocated_limit': Decimal('1000000000')
            },
            {
                'lender_id': 'B',
                'profit_percentage': Decimal('0.02'),
                'approval_rate': Decimal('0'),  # Zero approval rate
                'allocated_limit': Decimal('500000000')
            }
        ]
        
        selection_scores = calculate_selection_scores(test_data)
        
        # Should only include lender A
        self.assertEqual(len(selection_scores), 1)
        self.assertEqual(selection_scores[0].lender_id, 'A')


class TestLoanProcessor(unittest.TestCase):
    """Test complete loan processing"""
    
    def setUp(self):
        """Set up test lenders and processor"""
        self.test_lenders = [
            LenderData(
                lender_id='LENDER_A',
                base_interest_rate=Decimal('0.142'),
                approval_rate=Decimal('0.85'),
                monthly_limit=Decimal('50000000'),
                cost_of_funds=Decimal('0.085'),
                allocated_limit=Decimal('3500000000')
            ),
            LenderData(
                lender_id='LENDER_B',
                base_interest_rate=Decimal('0.145'),
                approval_rate=Decimal('0.72'),
                monthly_limit=Decimal('40000000'),
                cost_of_funds=Decimal('0.088'),
                allocated_limit=Decimal('2800000000')
            )
        ]
        
        self.processor = LoanProcessor(self.test_lenders)
        
        self.loan_request = LoanRequest(
            originator_rate=Decimal('0.165'),
            loan_amount=Decimal('100000'),
            servicing_fee=Decimal('0.018'),
            cost_of_funds=Decimal('0.092'),
            originator_id='ORIG_001'
        )
    
    def test_complete_loan_processing(self):
        """Test complete loan application processing"""
        result = self.processor.process_loan_application(self.loan_request)
        
        # Validate result structure
        self.assertIsNotNone(result.loan_id)
        self.assertIn(result.selected_lender_id, ['LENDER_A', 'LENDER_B'])
        self.assertTrue(result.both_profitable)
        self.assertGreater(result.originator_profit, 0)
        self.assertGreater(result.lender_profit, 0)
        self.assertEqual(result.loan_amount, self.loan_request.loan_amount)
        
        # Validate weights sum to 1
        self.assertAlmostEqual(
            result.originator_weight + result.lender_weight,
            Decimal('1.0'),
            places=5
        )


if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)