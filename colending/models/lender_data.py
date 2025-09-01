from dataclasses import dataclass
from decimal import Decimal


@dataclass
class LenderData:
    """Lender information for co-lending calculations"""
    lender_id: str
    base_interest_rate: Decimal
    approval_rate: Decimal
    monthly_limit: Decimal
    cost_of_funds: Decimal
    allocated_limit: Decimal
    
    def __post_init__(self):
        """Validate lender data"""
        if self.approval_rate <= 0 or self.approval_rate > 1:
            raise ValueError("Approval rate must be between 0 and 1")
        if self.allocated_limit < 0:
            raise ValueError("Allocated limit must be non-negative")
        if self.monthly_limit < 0:
            raise ValueError("Monthly limit must be non-negative")


@dataclass
class SelectionScore:
    """Selection score data for lender selection"""
    lender_id: str
    raw_score: Decimal
    normalized_score: int
    cumulative_range: tuple[int, int]  # (start, end) range for selection
    
    
@dataclass
class OptimizedTerms:
    """Optimized loan terms for a specific lender"""
    lender_id: str
    originator_weight: Decimal
    lender_weight: Decimal
    originator_profit: Decimal
    lender_profit: Decimal
    blended_rate: Decimal
    both_profitable: bool