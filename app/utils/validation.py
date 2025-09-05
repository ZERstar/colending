"""
Input validation utilities.
"""

from typing import Dict, Any, List


def validate_loan_request(loan_data: Dict[str, Any]) -> List[str]:
    """
    Validate loan request data.
    
    Args:
        loan_data: Loan request data
        
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    # Required fields
    required_fields = ['loan_id', 'amount', 'orig_rate', 'cibil_score', 'foir', 'product_type']
    for field in required_fields:
        if field not in loan_data or loan_data[field] is None:
            errors.append(f"Missing required field: {field}")
    
    # Numeric validations
    if 'amount' in loan_data:
        if not isinstance(loan_data['amount'], (int, float)) or loan_data['amount'] <= 0:
            errors.append("Amount must be a positive number")
    
    if 'orig_rate' in loan_data:
        if not isinstance(loan_data['orig_rate'], (int, float)) or not (0 < loan_data['orig_rate'] < 1):
            errors.append("Originator rate must be between 0 and 1")
    
    if 'cibil_score' in loan_data:
        if not isinstance(loan_data['cibil_score'], int) or not (300 <= loan_data['cibil_score'] <= 900):
            errors.append("CIBIL score must be between 300 and 900")
    
    if 'foir' in loan_data:
        if not isinstance(loan_data['foir'], (int, float)) or not (0 <= loan_data['foir'] <= 1):
            errors.append("FOIR must be between 0 and 1")
    
    if 'ltr' in loan_data:
        if not isinstance(loan_data['ltr'], (int, float)) or not (0 <= loan_data['ltr'] <= 1):
            errors.append("LTR must be between 0 and 1")
    
    return errors


def validate_partnership_data(partnership_data: Dict[str, Any]) -> List[str]:
    """
    Validate partnership creation data.
    
    Args:
        partnership_data: Partnership data
        
    Returns:
        List of validation errors
    """
    errors = []
    
    # Required fields
    required_fields = ['orig_id', 'partner_id', 'min_amount', 'max_amount', 'products', 'monthly_limit', 'service_fee', 'cost_funds']
    for field in required_fields:
        if field not in partnership_data or partnership_data[field] is None:
            errors.append(f"Missing required field: {field}")
    
    # Amount validations
    if 'min_amount' in partnership_data and 'max_amount' in partnership_data:
        if partnership_data['min_amount'] >= partnership_data['max_amount']:
            errors.append("Min amount must be less than max amount")
    
    # Rate validations
    for field in ['service_fee', 'cost_funds']:
        if field in partnership_data:
            if not isinstance(partnership_data[field], (int, float)) or not (0 <= partnership_data[field] <= 1):
                errors.append(f"{field} must be between 0 and 1")
    
    return errors