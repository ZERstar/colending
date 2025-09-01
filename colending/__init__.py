"""
Co-Lending Interest Rate Management System

A complete system for calculating blended rates, optimizing profits, 
and implementing weighted random lender selection for co-lending scenarios.

Core Features:
- Blended interest rate calculations
- Profit optimization for originators and lenders
- Weighted random lender selection algorithm
- Complete loan processing pipeline

Mathematical Formulas:
- R_B = (w_O * R_O) + (w_L * R_L)
- P_originator = (w_O * R_B) + S_O - (w_O * C_O)
- P_lender = (w_L * R_B) - (w_L * C_L) - S_L
- Selection_Score_i = Allocated_Limit_i / Approval_Rate_i
"""

__version__ = "1.0.0"
__author__ = "Co-Lending System"

from .models import (
    LoanTerms,
    CostParameters, 
    LoanRequest,
    LenderData,
    SelectionScore,
    OptimizedTerms,
    LoanResult,
    ProfitCalculation,
    OptimizationResult
)

from .calculators import (
    calculate_blended_rate,
    validate_rate_inputs,
    calculate_profits,
    optimize_participation_ratio,
    calculate_selection_scores,
    select_lender_random,
    validate_selection_distribution,
    calculate_expected_distribution
)

from .services import LoanProcessor

__all__ = [
    # Models
    'LoanTerms',
    'CostParameters',
    'LoanRequest', 
    'LenderData',
    'SelectionScore',
    'OptimizedTerms',
    'LoanResult',
    'ProfitCalculation',
    'OptimizationResult',
    
    # Calculators
    'calculate_blended_rate',
    'validate_rate_inputs',
    'calculate_profits',
    'optimize_participation_ratio',
    'calculate_selection_scores',
    'select_lender_random',
    'validate_selection_distribution',
    'calculate_expected_distribution',
    
    # Services
    'LoanProcessor'
]