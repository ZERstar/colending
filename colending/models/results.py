from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class LoanResult:
    """Final loan processing result"""
    loan_id: str
    selected_lender_id: str
    originator_weight: Decimal
    lender_weight: Decimal
    blended_rate: Decimal
    originator_profit: Decimal
    lender_profit: Decimal
    both_profitable: bool
    loan_amount: Decimal
    

@dataclass
class ProfitCalculation:
    """Profit calculation result for both parties"""
    originator_profit: Decimal
    lender_profit: Decimal
    blended_rate: Decimal
    both_profitable: bool
    
    
@dataclass
class OptimizationResult:
    """Result of participation ratio optimization"""
    optimal_originator_weight: Decimal
    optimal_lender_weight: Decimal
    originator_profit: Decimal
    lender_profit: Decimal
    blended_rate: Decimal
    both_profitable: bool