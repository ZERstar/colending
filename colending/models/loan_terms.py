from dataclasses import dataclass
from typing import Optional
from decimal import Decimal


@dataclass
class LoanTerms:
    """Core loan terms for co-lending calculations"""
    originator_rate: Decimal
    lender_rate: Decimal
    originator_weight: Decimal
    lender_weight: Decimal
    loan_amount: Decimal
    servicing_fee_rate: Decimal
    
    def __post_init__(self):
        """Validate that weights sum to 1.0"""
        if abs(self.originator_weight + self.lender_weight - Decimal('1.0')) > Decimal('0.0001'):
            raise ValueError("Originator and lender weights must sum to 1.0")


@dataclass
class CostParameters:
    """Cost parameters for both originator and lender"""
    originator_cost_of_funds: Decimal
    lender_cost_of_funds: Decimal
    servicing_fee_rate: Decimal


@dataclass
class LoanRequest:
    """Initial loan request from originator"""
    originator_rate: Decimal
    loan_amount: Decimal
    servicing_fee: Decimal
    cost_of_funds: Decimal
    originator_id: Optional[str] = None