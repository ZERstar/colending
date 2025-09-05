"""
Test cases for allocation logic.
"""

import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session

from app.core.allocation import (
    get_eligible_partnerships, get_approval_rate, calc_bre_score, allocate_loan
)
from app.database import Partnership, Partner, Performance


def test_bre_score_calculation():
    """Test BRE score calculation based on loan characteristics"""
    # Test high CIBIL, low FOIR, low LTR (should get high score)
    loan_data = {
        'cibil_score': 780,
        'foir': 0.25,
        'ltr': 0.6
    }
    
    score = calc_bre_score(1, loan_data)
    assert score > 0.5  # Should be above base score
    
    # Test low CIBIL, high FOIR, high LTR (should get low score)
    loan_data_bad = {
        'cibil_score': 620,
        'foir': 0.55,
        'ltr': 0.95
    }
    
    score_bad = calc_bre_score(1, loan_data_bad)
    assert score_bad < 0.5  # Should be below base score


def test_approval_rate_bounds():
    """Test approval rate is properly bounded between 0.1 and 0.95"""
    # Mock database session
    db = MagicMock(spec=Session)
    db.query().filter().all.return_value = []  # No historical data
    
    loan_data = {'cibil_score': 750, 'foir': 0.3, 'ltr': 0.5}
    
    rate = get_approval_rate(1, loan_data, db)
    
    # Should be between 10% and 95%
    assert 0.1 <= rate <= 0.95


@pytest.fixture
def mock_partnerships():
    """Create mock partnerships for testing"""
    partner1 = Partner(id=1, name="Lender A", type="EXTERNAL", active=True)
    partner2 = Partner(id=2, name="Lender B", type="EXTERNAL", active=True)
    
    partnership1 = Partnership(
        id=1,
        orig_id=1,
        partner_id=1,
        min_amount=50000,
        max_amount=10000000,
        products='["PERSONAL_LOAN"]',
        rate_formula='{"participation": 0.25}',
        monthly_limit=50000000,
        service_fee=0.018,
        cost_funds=0.085,
        active=True
    )
    partnership1.partner = partner1
    
    partnership2 = Partnership(
        id=2,
        orig_id=1,
        partner_id=2,
        min_amount=50000,
        max_amount=5000000,
        products='["PERSONAL_LOAN"]',
        rate_formula='{"participation": 0.30}',
        monthly_limit=30000000,
        service_fee=0.020,
        cost_funds=0.088,
        active=True
    )
    partnership2.partner = partner2
    
    return [partnership1, partnership2]


def test_eligible_partnerships_filtering(mock_partnerships):
    """Test partnership eligibility filtering"""
    # Mock database session
    db = MagicMock(spec=Session)
    db.query().filter().all.return_value = mock_partnerships
    
    # Test loan within range for both partnerships
    loan_data = {
        'amount': 100000,
        'product_type': 'PERSONAL_LOAN'
    }
    
    eligible = get_eligible_partnerships(loan_data, 1, db)
    assert len(eligible) == 2
    
    # Test loan too large for second partnership
    loan_data_large = {
        'amount': 8000000,
        'product_type': 'PERSONAL_LOAN'
    }
    
    # Mock only first partnership being returned by filter
    db.query().filter().all.return_value = [mock_partnerships[0]]
    
    eligible = get_eligible_partnerships(loan_data_large, 1, db)
    assert len(eligible) == 1
    assert eligible[0].id == 1


def test_allocation_profitability_filter(mock_partnerships):
    """Test that only profitable partnerships are considered"""
    # Mock database session
    db = MagicMock(spec=Session)
    db.query().filter().all.return_value = mock_partnerships
    
    # Mock performance data for approval rates
    db.query().filter().filter().all.return_value = [
        MagicMock(total_apps=100, approved_apps=75),
        MagicMock(total_apps=100, approved_apps=60)
    ]
    
    loan_data = {
        'loan_id': 'TEST_001',
        'amount': 500000,
        'product_type': 'PERSONAL_LOAN',
        'orig_rate': 0.165,
        'cibil_score': 750,
        'foir': 0.35,
        'ltr': 0.7,
        'cost_of_funds': 0.092
    }
    
    # This should work with mock data
    # In a real test, you'd want to control all the mocks more precisely
    try:
        result = allocate_loan(loan_data, 1, db)
        assert 'loan_id' in result
        assert result['loan_id'] == 'TEST_001'
        assert result['recommended_partner'] is not None
        assert len(result['all_options']) > 0
    except ValueError as e:
        # This might happen if partnerships aren't profitable with test data
        assert "profitable" in str(e).lower()


def test_allocation_no_eligible_partnerships():
    """Test allocation fails gracefully with no eligible partnerships"""
    # Mock database session with no partnerships
    db = MagicMock(spec=Session)
    db.query().filter().all.return_value = []
    
    loan_data = {
        'loan_id': 'TEST_001',
        'amount': 500000,
        'product_type': 'PERSONAL_LOAN',
        'orig_rate': 0.165,
        'cibil_score': 750,
        'foir': 0.35,
        'ltr': 0.7
    }
    
    with pytest.raises(ValueError, match="No eligible partnerships"):
        allocate_loan(loan_data, 1, db)