"""
Utility helper functions.
"""

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict


def generate_batch_id() -> str:
    """Generate unique batch ID"""
    return str(uuid.uuid4())


def generate_loan_id() -> str:
    """Generate unique loan ID"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_id = uuid.uuid4().hex[:6]
    return f"LOAN_{timestamp}_{unique_id}"


def format_currency(amount: float) -> str:
    """Format amount as currency string"""
    if amount >= 10000000:  # >= 1 Cr
        return f"₹{amount/10000000:.1f} Cr"
    elif amount >= 100000:  # >= 1 L
        return f"₹{amount/100000:.1f} L"
    else:
        return f"₹{amount:,.0f}"


def calculate_processing_time(start_time: datetime, end_time: datetime) -> float:
    """Calculate processing time in milliseconds"""
    delta = end_time - start_time
    return delta.total_seconds() * 1000


def get_month_year_range(months_back: int) -> str:
    """Get month-year string for N months back"""
    date = datetime.now() - timedelta(days=months_back * 30)
    return date.strftime("%Y-%m")


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers with default for division by zero"""
    if denominator == 0:
        return default
    return numerator / denominator


def round_to_precision(value: float, precision: int = 4) -> float:
    """Round value to specified precision"""
    return round(value, precision)


def validate_rate_range(rate: float, min_rate: float = 0.0, max_rate: float = 1.0) -> bool:
    """Validate that rate is within acceptable range"""
    return min_rate <= rate <= max_rate


def convert_percentage(rate: float, input_as_percentage: bool = False) -> float:
    """Convert between decimal and percentage rates"""
    if input_as_percentage and rate > 1:
        return rate / 100
    return rate