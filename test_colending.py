#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple test script to validate the co-lending system implementation
"""

import sys
import time
from decimal import Decimal

# Add colending package to path
sys.path.append('colending')

from colending import (
    calculate_blended_rate,
    calculate_profits,
    calculate_selection_scores,
    validate_selection_distribution,
    LoanTerms,
    CostParameters,
    LenderData,
    LoanRequest,
    LoanProcessor
)


def test_basic_calculations():
    """Test basic mathematical formulas"""
    print("="*50)
    print("TESTING BASIC CALCULATIONS")
    print("="*50)
    
    # Test Case 1: Blended Rate
    print("\n1. Testing Blended Rate Calculation")
    blended_rate = calculate_blended_rate(
        originator_rate=Decimal('0.165'),
        lender_rate=Decimal('0.142'),
        originator_weight=Decimal('0.25'),
        lender_weight=Decimal('0.75')
    )
    expected = Decimal('0.14775')
    passed = abs(blended_rate - expected) < Decimal('0.0001')
    print(f"   Expected: {expected:.4%}")
    print(f"   Actual: {blended_rate:.4%}")
    print(f"   Result: {'PASS' if passed else 'FAIL'}")
    
    # Test Case 2: Profit Calculation
    print("\n2. Testing Profit Calculation")
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
    
    profits = calculate_profits(loan_terms, cost_params)
    
    expected_orig = Decimal('0.03194')
    expected_lend = Decimal('0.02906')
    
    orig_pass = abs(profits.originator_profit - expected_orig) < Decimal('0.0001')
    lend_pass = abs(profits.lender_profit - expected_lend) < Decimal('0.0001')
    
    print(f"   Originator Expected: {expected_orig:.4%}, Actual: {profits.originator_profit:.4%} - {'PASS' if orig_pass else 'FAIL'}")
    print(f"   Lender Expected: {expected_lend:.4%}, Actual: {profits.lender_profit:.4%} - {'PASS' if lend_pass else 'FAIL'}")
    print(f"   Both Profitable: {profits.both_profitable}")
    
    return passed and orig_pass and lend_pass


def test_selection_algorithm():
    """Test selection algorithm"""
    print("\n3. Testing Selection Algorithm")
    
    # Test data from requirements
    test_lenders = [
        {
            'lender_id': 'A',
            'profit_percentage': Decimal('0.032'),
            'approval_rate': Decimal('0.85'),
            'allocated_limit': Decimal('3500000000')
        },
        {
            'lender_id': 'B',
            'profit_percentage': Decimal('0.028'),
            'approval_rate': Decimal('0.72'),
            'allocated_limit': Decimal('2800000000')
        },
        {
            'lender_id': 'C',
            'profit_percentage': Decimal('0.021'),
            'approval_rate': Decimal('0.58'),
            'allocated_limit': Decimal('2100000000')
        }
    ]
    
    selection_scores = calculate_selection_scores(test_lenders)
    
    print(f"   Generated {len(selection_scores)} selection scores")
    
    # Test distribution
    actual_distribution = validate_selection_distribution(selection_scores, 1000)
    
    expected = {'A': 35.5, 'B': 33.3, 'C': 31.2}
    all_pass = True
    
    for lender_id in ['A', 'B', 'C']:
        actual = actual_distribution[lender_id]
        exp = expected[lender_id]
        diff = abs(actual - exp)
        passed = diff <= 2.0
        all_pass = all_pass and passed
        print(f"   {lender_id}: Expected {exp:.1f}%, Actual {actual:.1f}%, Diff {diff:.1f}% - {'PASS' if passed else 'FAIL'}")
    
    return all_pass


def test_complete_workflow():
    """Test complete workflow"""
    print("\n4. Testing Complete Workflow")
    
    # Create test lenders
    lenders = [
        LenderData(
            lender_id='TEST_LENDER_A',
            base_interest_rate=Decimal('0.142'),
            approval_rate=Decimal('0.85'),
            monthly_limit=Decimal('50000000'),
            cost_of_funds=Decimal('0.085'),
            allocated_limit=Decimal('3500000000')
        ),
        LenderData(
            lender_id='TEST_LENDER_B',
            base_interest_rate=Decimal('0.145'),
            approval_rate=Decimal('0.72'),
            monthly_limit=Decimal('40000000'),
            cost_of_funds=Decimal('0.088'),
            allocated_limit=Decimal('2800000000')
        )
    ]
    
    processor = LoanProcessor(lenders)
    
    loan_request = LoanRequest(
        originator_rate=Decimal('0.165'),
        loan_amount=Decimal('500000'),
        servicing_fee=Decimal('0.018'),
        cost_of_funds=Decimal('0.092')
    )
    
    # Test performance
    start_time = time.time()
    result = processor.process_loan_application(loan_request)
    processing_time = (time.time() - start_time) * 1000
    
    performance_pass = processing_time < 100
    profitability_pass = result.both_profitable
    
    print(f"   Selected Lender: {result.selected_lender_id}")
    print(f"   Processing Time: {processing_time:.2f}ms - {'PASS' if performance_pass else 'FAIL'}")
    print(f"   Both Profitable: {result.both_profitable} - {'PASS' if profitability_pass else 'FAIL'}")
    print(f"   Blended Rate: {result.blended_rate:.4%}")
    print(f"   Originator Profit: {result.originator_profit:.4%}")
    print(f"   Lender Profit: {result.lender_profit:.4%}")
    
    return performance_pass and profitability_pass


def main():
    """Run all tests"""
    print("Co-Lending Interest Rate Management System")
    print("Testing Core Functionality")
    
    try:
        test1_pass = test_basic_calculations()
        test2_pass = test_selection_algorithm()
        test3_pass = test_complete_workflow()
        
        all_tests_pass = test1_pass and test2_pass and test3_pass
        
        print("\n" + "="*50)
        print("TEST RESULTS SUMMARY")
        print("="*50)
        print(f"Basic Calculations: {'PASS' if test1_pass else 'FAIL'}")
        print(f"Selection Algorithm: {'PASS' if test2_pass else 'FAIL'}")
        print(f"Complete Workflow: {'PASS' if test3_pass else 'FAIL'}")
        print(f"\nOVERALL: {'ALL TESTS PASSED' if all_tests_pass else 'SOME TESTS FAILED'}")
        
        if all_tests_pass:
            print("\nSystem successfully implements all requirements:")
            print("- Mathematical formulas validated")
            print("- Selection algorithm working correctly")
            print("- Performance requirements met (<100ms)")
            print("- Complete workflow functional")
        
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return all_tests_pass


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)