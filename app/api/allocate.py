"""
Loan allocation API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import LoanRequest, AllocationResponse
from app.core.allocation import allocate_loan

router = APIRouter(prefix="/api", tags=["allocation"])


@router.post("/allocate", response_model=AllocationResponse)
async def allocate_single_loan(
    loan: LoanRequest, 
    program_id: int,
    db: Session = Depends(get_db)
):
    """
    Allocate a single loan to the best partner using weighted random selection.
    
    Args:
        loan: Loan request data
        program_id: Program ID for allocation strategy
        db: Database session
        
    Returns:
        Allocation response with recommended partner and all options
    """
    try:
        # Convert Pydantic model to dict
        loan_data = {
            'loan_id': loan.loan_id,
            'amount': loan.amount,
            'orig_rate': loan.orig_rate,
            'cibil_score': loan.cibil_score,
            'foir': loan.foir,
            'ltr': loan.ltr,
            'product_type': loan.product_type,
            'cost_of_funds': 0.092  # Default cost of funds
        }
        
        # Perform allocation
        result = allocate_loan(loan_data, program_id, db)
        
        return AllocationResponse(**result)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Allocation failed: {str(e)}")