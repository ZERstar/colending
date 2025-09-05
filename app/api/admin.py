"""
Administrative API endpoints for managing partners and partnerships.
"""

import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db, Partner, Partnership, Program
from app.models import (
    PartnerCreate, PartnerResponse, PartnershipCreate, PartnershipResponse,
    ProgramCreate, AllocationRecord
)

router = APIRouter(prefix="/api", tags=["admin"])


@router.get("/partners", response_model=List[PartnerResponse])
async def list_partners(
    orig_id: int = None,
    db: Session = Depends(get_db)
):
    """
    Get list of all partners or partners for specific originator.
    
    Args:
        orig_id: Optional originator ID to filter partnerships
        db: Database session
        
    Returns:
        List of partners
    """
    query = db.query(Partner).filter(Partner.active == True)
    
    if orig_id:
        # This would need to be refined based on business logic
        query = query.filter(Partner.id != orig_id)
    
    partners = query.all()
    return partners


@router.post("/partners", response_model=PartnerResponse)
async def create_partner(
    partner: PartnerCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new partner.
    
    Args:
        partner: Partner creation data
        db: Database session
        
    Returns:
        Created partner information
    """
    if partner.type not in ['YUBI', 'EXTERNAL', 'OWN_BOOK']:
        raise HTTPException(status_code=400, detail="Invalid partner type")
    
    # Check if partner name already exists
    existing = db.query(Partner).filter(Partner.name == partner.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Partner with this name already exists")
    
    db_partner = Partner(
        name=partner.name,
        type=partner.type,
        active=True
    )
    
    db.add(db_partner)
    db.commit()
    db.refresh(db_partner)
    
    return db_partner


@router.get("/partnerships", response_model=List[PartnershipResponse])
async def list_partnerships(
    orig_id: int = None,
    partner_id: int = None,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """
    Get list of partnerships with optional filtering.
    
    Args:
        orig_id: Optional originator ID filter
        partner_id: Optional partner ID filter
        active_only: Only return active partnerships
        db: Database session
        
    Returns:
        List of partnerships
    """
    query = db.query(Partnership).join(Partner, Partnership.partner_id == Partner.id)
    
    if orig_id:
        query = query.filter(Partnership.orig_id == orig_id)
    if partner_id:
        query = query.filter(Partnership.partner_id == partner_id)
    if active_only:
        query = query.filter(Partnership.active == True)
    
    partnerships = query.all()
    
    # Format response with partner names
    result = []
    for p in partnerships:
        partnership_data = {
            'id': p.id,
            'orig_id': p.orig_id,
            'partner_id': p.partner_id,
            'min_amount': p.min_amount,
            'max_amount': p.max_amount,
            'products': json.loads(p.products) if p.products else [],
            'monthly_limit': p.monthly_limit,
            'service_fee': p.service_fee,
            'cost_funds': p.cost_funds,
            'active': p.active,
            'partner_name': p.partner.name
        }
        result.append(PartnershipResponse(**partnership_data))
    
    return result


@router.post("/partnerships", response_model=PartnershipResponse)
async def create_partnership(
    partnership: PartnershipCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new partnership between originator and partner.
    
    Args:
        partnership: Partnership creation data
        db: Database session
        
    Returns:
        Created partnership information
    """
    # Validate partners exist
    originator = db.query(Partner).filter(Partner.id == partnership.orig_id).first()
    partner = db.query(Partner).filter(Partner.id == partnership.partner_id).first()
    
    if not originator:
        raise HTTPException(status_code=400, detail="Originator not found")
    if not partner:
        raise HTTPException(status_code=400, detail="Partner not found")
    
    # Validate amounts
    if partnership.min_amount >= partnership.max_amount:
        raise HTTPException(status_code=400, detail="Min amount must be less than max amount")
    
    # Check for existing partnership
    existing = db.query(Partnership).filter(
        Partnership.orig_id == partnership.orig_id,
        Partnership.partner_id == partnership.partner_id,
        Partnership.active == True
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Active partnership already exists between these parties")
    
    db_partnership = Partnership(
        orig_id=partnership.orig_id,
        partner_id=partnership.partner_id,
        min_amount=partnership.min_amount,
        max_amount=partnership.max_amount,
        products=json.dumps(partnership.products),
        rate_formula=json.dumps(partnership.rate_formula),
        monthly_limit=partnership.monthly_limit,
        service_fee=partnership.service_fee,
        cost_funds=partnership.cost_funds,
        active=True
    )
    
    db.add(db_partnership)
    db.commit()
    db.refresh(db_partnership)
    
    # Format response
    partnership_data = {
        'id': db_partnership.id,
        'orig_id': db_partnership.orig_id,
        'partner_id': db_partnership.partner_id,
        'min_amount': db_partnership.min_amount,
        'max_amount': db_partnership.max_amount,
        'products': json.loads(db_partnership.products),
        'monthly_limit': db_partnership.monthly_limit,
        'service_fee': db_partnership.service_fee,
        'cost_funds': db_partnership.cost_funds,
        'active': db_partnership.active,
        'partner_name': partner.name
    }
    
    return PartnershipResponse(**partnership_data)


@router.put("/partnerships/{partnership_id}")
async def update_partnership(
    partnership_id: int,
    updates: dict,
    db: Session = Depends(get_db)
):
    """
    Update partnership configuration.
    
    Args:
        partnership_id: Partnership ID
        updates: Dictionary of fields to update
        db: Database session
        
    Returns:
        Update confirmation
    """
    partnership = db.query(Partnership).filter(Partnership.id == partnership_id).first()
    
    if not partnership:
        raise HTTPException(status_code=404, detail="Partnership not found")
    
    # Update allowed fields
    allowed_fields = ['min_amount', 'max_amount', 'monthly_limit', 'service_fee', 'cost_funds', 'active']
    
    for field, value in updates.items():
        if field in allowed_fields:
            setattr(partnership, field, value)
        elif field == 'products':
            partnership.products = json.dumps(value)
        elif field == 'rate_formula':
            partnership.rate_formula = json.dumps(value)
    
    db.commit()
    
    return {"message": "Partnership updated successfully", "partnership_id": partnership_id}