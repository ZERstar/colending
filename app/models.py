"""
Pydantic models for request/response validation.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class LoanRequest(BaseModel):
    """Loan request model for single allocation"""
    loan_id: str
    amount: float
    tenure: int
    product_type: str
    orig_rate: float
    cibil_score: int
    foir: float
    ltr: float = 0.0


class PartnerScore(BaseModel):
    """Partner evaluation score"""
    partner_id: int
    name: str
    profit_score: float
    selection_score: float
    approval_prob: float


class AllocationResponse(BaseModel):
    """Response for loan allocation"""
    loan_id: str
    recommended_partner: PartnerScore
    all_options: List[PartnerScore]
    reasoning: str
    processing_time_ms: float


class BatchUploadResponse(BaseModel):
    """Response for batch upload"""
    batch_id: str
    total_loans: int
    status: str
    estimated_time_min: int


class BatchStatusResponse(BaseModel):
    """Batch processing status"""
    batch_id: str
    status: str  # PROCESSING, COMPLETED, FAILED
    progress: int  # 0-100
    total_loans: int
    processed_loans: int
    failed_loans: int
    estimated_completion: Optional[datetime] = None


class PartnershipCreate(BaseModel):
    """Create new partnership"""
    orig_id: int
    partner_id: int
    min_amount: float
    max_amount: float
    products: List[str]
    rate_formula: dict
    monthly_limit: float
    service_fee: float
    cost_funds: float


class PartnerCreate(BaseModel):
    """Create new partner"""
    name: str
    type: str  # 'YUBI', 'EXTERNAL', 'OWN_BOOK'


class ProgramCreate(BaseModel):
    """Create new program"""
    orig_id: int
    name: str
    product_types: List[str]
    strategy_config: dict


class PartnerResponse(BaseModel):
    """Partner information response"""
    id: int
    name: str
    type: str
    active: bool
    
    class Config:
        from_attributes = True


class PartnershipResponse(BaseModel):
    """Partnership information response"""
    id: int
    orig_id: int
    partner_id: int
    min_amount: float
    max_amount: float
    products: List[str]
    monthly_limit: float
    service_fee: float
    cost_funds: float
    active: bool
    partner_name: str
    
    class Config:
        from_attributes = True


class AllocationRecord(BaseModel):
    """Allocation record"""
    id: int
    loan_id: str
    partnership_id: int
    orig_profit: float
    lender_profit: float
    blended_rate: float
    selection_score: float
    created_at: datetime
    
    class Config:
        from_attributes = True