# -*- coding: utf-8 -*-
from decimal import Decimal
from typing import Union
import logging

from ..models import LoanTerms, CostParameters, ProfitCalculation, OptimizationResult
from .rate_calculator import calculate_blended_rate

logger = logging.getLogger(__name__)


def calculate_profits(
    loan_terms: LoanTerms,
    cost_params: CostParameters
) -> ProfitCalculation:
    """
    Calculate profits for both originator and lender using:
    P_originator = (w_O * R_B) + S_O - (w_O * C_O)
    P_lender = (w_L * R_B) - (w_L * C_L) - S_L
    
    Args:
        loan_terms: Loan terms including rates and weights
        cost_params: Cost parameters for both parties
        
    Returns:
        ProfitCalculation with profits for both parties
    """
    # Calculate blended rate
    blended_rate = calculate_blended_rate(
        loan_terms.originator_rate,
        loan_terms.lender_rate,
        loan_terms.originator_weight,
        loan_terms.lender_weight
    )
    
    # Calculate originator profit
    # P_originator = (w_O * R_B) + S_O - (w_O * C_O)
    originator_profit = (
        (loan_terms.originator_weight * blended_rate) + 
        loan_terms.servicing_fee_rate - 
        (loan_terms.originator_weight * cost_params.originator_cost_of_funds)
    )
    
    # Calculate lender profit  
    # P_lender = (w_L * R_B) - (w_L * C_L) - S_L
    lender_profit = (
        (loan_terms.lender_weight * blended_rate) -
        (loan_terms.lender_weight * cost_params.lender_cost_of_funds) -
        cost_params.servicing_fee_rate
    )
    
    both_profitable = originator_profit > 0 and lender_profit > 0
    
    logger.debug(f"Calculated profits - Originator: {originator_profit:.4f}, Lender: {lender_profit:.4f}, Blended: {blended_rate:.4f}")
    
    return ProfitCalculation(
        originator_profit=originator_profit,
        lender_profit=lender_profit,
        blended_rate=blended_rate,
        both_profitable=both_profitable
    )


def optimize_participation_ratio(
    originator_rate: Union[Decimal, float],
    lender_rate: Union[Decimal, float],
    loan_amount: Union[Decimal, float],
    originator_cost_of_funds: Union[Decimal, float],
    lender_cost_of_funds: Union[Decimal, float],
    servicing_fee_rate: Union[Decimal, float],
    min_participation: float = 0.15,
    max_participation: float = 0.50,
    step_size: float = 0.05
) -> OptimizationResult:
    """
    Optimize participation ratio to maximize combined profits while ensuring both parties are profitable.
    Tests participation ratios from 15% to 50% in 5% steps.
    
    Args:
        originator_rate: Originator interest rate
        lender_rate: Lender interest rate
        loan_amount: Total loan amount
        originator_cost_of_funds: Originator cost of funds
        lender_cost_of_funds: Lender cost of funds
        servicing_fee_rate: Servicing fee rate
        min_participation: Minimum originator participation (default 15%)
        max_participation: Maximum originator participation (default 50%)
        step_size: Step size for optimization (default 5%)
        
    Returns:
        OptimizationResult with optimal participation split
    """
    # Convert to Decimal
    orig_rate = Decimal(str(originator_rate))
    lend_rate = Decimal(str(lender_rate))
    loan_amt = Decimal(str(loan_amount))
    orig_cost = Decimal(str(originator_cost_of_funds))
    lend_cost = Decimal(str(lender_cost_of_funds))
    service_fee = Decimal(str(servicing_fee_rate))
    
    best_result = None
    best_combined_profit = Decimal('-1')
    
    # Test different participation ratios
    current_participation = Decimal(str(min_participation))
    step = Decimal(str(step_size))
    max_part = Decimal(str(max_participation))
    
    while current_participation <= max_part:
        lender_participation = Decimal('1') - current_participation
        
        # Create loan terms for this participation ratio
        loan_terms = LoanTerms(
            originator_rate=orig_rate,
            lender_rate=lend_rate,
            originator_weight=current_participation,
            lender_weight=lender_participation,
            loan_amount=loan_amt,
            servicing_fee_rate=service_fee
        )
        
        cost_params = CostParameters(
            originator_cost_of_funds=orig_cost,
            lender_cost_of_funds=lend_cost,
            servicing_fee_rate=service_fee
        )
        
        # Calculate profits
        profit_calc = calculate_profits(loan_terms, cost_params)
        
        # Check if both parties are profitable
        if profit_calc.both_profitable:
            combined_profit = profit_calc.originator_profit + profit_calc.lender_profit
            
            if combined_profit > best_combined_profit:
                best_combined_profit = combined_profit
                best_result = OptimizationResult(
                    optimal_originator_weight=current_participation,
                    optimal_lender_weight=lender_participation,
                    originator_profit=profit_calc.originator_profit,
                    lender_profit=profit_calc.lender_profit,
                    blended_rate=profit_calc.blended_rate,
                    both_profitable=True
                )
        
        current_participation += step
    
    if best_result is None:
        # No profitable combination found
        logger.warning("No profitable participation ratio found")
        return OptimizationResult(
            optimal_originator_weight=Decimal(str(min_participation)),
            optimal_lender_weight=Decimal('1') - Decimal(str(min_participation)),
            originator_profit=Decimal('0'),
            lender_profit=Decimal('0'),
            blended_rate=Decimal('0'),
            both_profitable=False
        )
    
    logger.info(f"Optimal participation - Originator: {best_result.optimal_originator_weight:.3f}, Combined profit: {best_combined_profit:.4f}")
    
    return best_result