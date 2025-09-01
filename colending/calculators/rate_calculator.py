# -*- coding: utf-8 -*-
from decimal import Decimal
from typing import Union
import logging

logger = logging.getLogger(__name__)


def calculate_blended_rate(
    originator_rate: Union[Decimal, float],
    lender_rate: Union[Decimal, float],
    originator_weight: Union[Decimal, float],
    lender_weight: Union[Decimal, float]
) -> Decimal:
    """
    Calculate blended interest rate using the formula:
    R_B = (w_O * R_O) + (w_L * R_L)
    
    Args:
        originator_rate: Originator interest rate
        lender_rate: Lender interest rate  
        originator_weight: Originator participation weight
        lender_weight: Lender participation weight
        
    Returns:
        Blended interest rate as Decimal
        
    Raises:
        ValueError: If weights don't sum to 1.0
    """
    # Convert to Decimal for precision
    orig_rate = Decimal(str(originator_rate))
    lend_rate = Decimal(str(lender_rate))
    orig_weight = Decimal(str(originator_weight))
    lend_weight = Decimal(str(lender_weight))
    
    # Validate weights sum to 1.0
    if abs(orig_weight + lend_weight - Decimal('1.0')) > Decimal('0.0001'):
        raise ValueError(f"Weights must sum to 1.0. Got: {orig_weight + lend_weight}")
    
    # Calculate blended rate
    blended_rate = (orig_weight * orig_rate) + (lend_weight * lend_rate)
    
    logger.debug(f"Calculated blended rate: {blended_rate:.4f} from rates {orig_rate:.4f}, {lend_rate:.4f} with weights {orig_weight:.4f}, {lend_weight:.4f}")
    
    return blended_rate


def validate_rate_inputs(
    originator_rate: Union[Decimal, float],
    lender_rate: Union[Decimal, float],
    originator_weight: Union[Decimal, float], 
    lender_weight: Union[Decimal, float]
) -> bool:
    """
    Validate rate calculation inputs
    
    Args:
        originator_rate: Originator interest rate
        lender_rate: Lender interest rate
        originator_weight: Originator participation weight
        lender_weight: Lender participation weight
        
    Returns:
        True if valid, False otherwise
    """
    try:
        # Check rates are positive
        if originator_rate <= 0 or lender_rate <= 0:
            logger.error("Interest rates must be positive")
            return False
            
        # Check weights are between 0 and 1
        if not (0 <= originator_weight <= 1) or not (0 <= lender_weight <= 1):
            logger.error("Weights must be between 0 and 1")
            return False
            
        # Check weights sum to 1
        if abs(originator_weight + lender_weight - 1.0) > 0.0001:
            logger.error("Weights must sum to 1.0")
            return False
            
        return True
        
    except (TypeError, ValueError) as e:
        logger.error(f"Invalid input types: {e}")
        return False