"""
Core allocation logic for co-lending loans.
"""

import json
from datetime import datetime, timedelta
from functools import lru_cache
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session

from app.database import Partnership, Performance, Allocation
from app.core.math import (
    calc_blended_rate, calc_orig_profit, calc_lender_profit, 
    calc_selection_score, normalize_scores, weighted_random_select
)
from app.models import LoanRequest, PartnerScore, AllocationResponse


def get_eligible_partnerships(loan_data: Dict[str, Any], program_id: int, db: Session) -> List[Partnership]:
    """
    Get partnerships eligible for the loan based on amount and product type.
    
    Args:
        loan_data: Loan information
        program_id: Program ID (currently unused, can be extended)
        db: Database session
        
    Returns:
        List of eligible partnerships
    """
    partnerships = db.query(Partnership).filter(
        Partnership.active == True,
        Partnership.min_amount <= loan_data['amount'],
        Partnership.max_amount >= loan_data['amount']
    ).all()
    
    # Filter by product type
    eligible = []
    for p in partnerships:
        products = json.loads(p.products) if p.products else []
        if loan_data.get('product_type') in products:
            eligible.append(p)
    
    return eligible


@lru_cache(maxsize=1000)
def get_approval_rate_cached(partnership_id: int, cibil_range: str) -> float:
    """Cache approval rates by CIBIL ranges for performance"""
    # This would connect to actual DB, simplified for cache demo
    return 0.75


def get_approval_rate(partnership_id: int, loan_data: Dict[str, Any], db: Session) -> float:
    """
    Calculate approval probability combining historical data and BRE rules.
    
    Args:
        partnership_id: Partnership ID
        loan_data: Loan information for BRE scoring
        db: Database session
        
    Returns:
        Approval probability (0.1 to 0.95)
    """
    # Get historical approval rate (last 6 months)
    six_months_ago = (datetime.now() - timedelta(days=180)).strftime("%Y-%m")
    
    historical_data = db.query(Performance).filter(
        Performance.partnership_id == partnership_id,
        Performance.month_year >= six_months_ago
    ).all()
    
    if historical_data:
        total_apps = sum(p.total_apps for p in historical_data)
        approved_apps = sum(p.approved_apps for p in historical_data)
        hist_rate = approved_apps / total_apps if total_apps > 0 else 0.75
    else:
        hist_rate = 0.75  # Default rate
    
    # Simple BRE score based on loan characteristics
    bre_score = calc_bre_score(partnership_id, loan_data)
    
    # Weighted combination (70% historical, 30% BRE)
    approval_rate = (0.7 * hist_rate) + (0.3 * bre_score)
    
    # Cap between 10% and 95%
    return min(max(approval_rate, 0.1), 0.95)


def calc_bre_score(partnership_id: int, loan_data: Dict[str, Any]) -> float:
    """
    Calculate BRE (Business Rule Engine) score based on loan characteristics.
    
    Args:
        partnership_id: Partnership ID
        loan_data: Loan information
        
    Returns:
        BRE score (0.0 to 1.0)
    """
    score = 0.5  # Base score
    
    # CIBIL score rules
    cibil = loan_data.get('cibil_score', 700)
    if cibil >= 750:
        score += 0.3
    elif cibil >= 700:
        score += 0.1
    elif cibil < 650:
        score -= 0.2
    
    # FOIR rules
    foir = loan_data.get('foir', 0.4)
    if foir <= 0.3:
        score += 0.1
    elif foir >= 0.5:
        score -= 0.1
    
    # LTR rules
    ltr = loan_data.get('ltr', 0.0)
    if ltr <= 0.7:
        score += 0.05
    elif ltr >= 0.9:
        score -= 0.1
    
    return min(max(score, 0.0), 1.0)


def allocate_loan(loan_data: Dict[str, Any], program_id: int, db: Session) -> Dict[str, Any]:
    """
    Main loan allocation function using weighted random selection.
    
    Args:
        loan_data: Loan information
        program_id: Program ID
        db: Database session
        
    Returns:
        Allocation result with selected partner and all options
    """
    start_time = datetime.now()
    
    # Get eligible partnerships
    partnerships = get_eligible_partnerships(loan_data, program_id, db)
    
    if not partnerships:
        raise ValueError("No eligible partnerships found for this loan")
    
    # Calculate scores for each partnership
    scores = []
    for p in partnerships:
        # Get rate configuration
        rate_config = json.loads(p.rate_formula) if p.rate_formula else {}
        participation = rate_config.get('participation', 0.25)
        
        # Calculate blended rate (assuming lender rate from cost_funds + margin)
        lender_rate = p.cost_funds + 0.02  # Simple margin
        blended = calc_blended_rate(loan_data['orig_rate'], lender_rate, participation)
        
        # Calculate profits
        orig_profit = calc_orig_profit(participation, blended, p.service_fee, loan_data.get('cost_of_funds', 0.092))
        lender_profit = calc_lender_profit(1 - participation, blended, p.cost_funds, p.service_fee)
        
        # Only consider if both are profitable
        if orig_profit > 0 and lender_profit > 0:
            approval_rate = get_approval_rate(p.id, loan_data, db)
            available_limit = p.monthly_limit  # Simplified - would need actual tracking
            selection_score = calc_selection_score(available_limit, approval_rate)
            
            scores.append({
                'partnership': p,
                'orig_profit': orig_profit,
                'lender_profit': lender_profit,
                'blended_rate': blended,
                'selection_score': selection_score,
                'approval_rate': approval_rate,
                'participation': participation
            })
    
    if not scores:
        raise ValueError("No profitable partnerships found for this loan")
    
    # Weighted random selection
    selection_scores = [s['selection_score'] for s in scores]
    normalized = normalize_scores(selection_scores)
    selected_idx = weighted_random_select(normalized)
    
    selected = scores[selected_idx]
    processing_time = (datetime.now() - start_time).total_seconds() * 1000
    
    # Store allocation record
    allocation = Allocation(
        loan_id=loan_data['loan_id'],
        partnership_id=selected['partnership'].id,
        orig_profit=selected['orig_profit'],
        lender_profit=selected['lender_profit'],
        blended_rate=selected['blended_rate'],
        selection_score=selected['selection_score']
    )
    db.add(allocation)
    db.commit()
    
    # Format response
    recommended_partner = PartnerScore(
        partner_id=selected['partnership'].partner_id,
        name=selected['partnership'].partner.name,
        profit_score=selected['orig_profit'] + selected['lender_profit'],
        selection_score=selected['selection_score'],
        approval_prob=selected['approval_rate']
    )
    
    all_options = []
    for score_data in scores:
        option = PartnerScore(
            partner_id=score_data['partnership'].partner_id,
            name=score_data['partnership'].partner.name,
            profit_score=score_data['orig_profit'] + score_data['lender_profit'],
            selection_score=score_data['selection_score'],
            approval_prob=score_data['approval_rate']
        )
        all_options.append(option)
    
    return {
        'loan_id': loan_data['loan_id'],
        'recommended_partner': recommended_partner,
        'all_options': all_options,
        'reasoning': f"Selected based on weighted random algorithm with participation: {selected['participation']:.1%}",
        'processing_time_ms': processing_time
    }