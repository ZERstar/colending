from decimal import Decimal
from typing import List, Optional
import uuid
import logging

from ..models import (
    LoanRequest, LenderData, LoanResult, OptimizedTerms,
    CostParameters, LoanTerms
)
from ..calculators import (
    optimize_participation_ratio,
    calculate_selection_scores,
    select_lender_random
)

logger = logging.getLogger(__name__)


class LoanProcessor:
    """Main service for processing co-lending loan applications"""
    
    def __init__(self, available_lenders: List[LenderData]):
        """
        Initialize loan processor with available lenders.
        
        Args:
            available_lenders: List of available lenders
        """
        self.available_lenders = available_lenders
        logger.info(f"Initialized loan processor with {len(available_lenders)} lenders")
    
    def process_loan_application(
        self,
        loan_request: LoanRequest,
        loan_id: Optional[str] = None
    ) -> LoanResult:
        """
        Process a complete loan application through the co-lending pipeline.
        
        Steps:
        1. Get eligible lenders
        2. Find optimal terms for each lender
        3. Execute selection algorithm
        4. Return final loan terms
        
        Args:
            loan_request: Loan request from originator
            loan_id: Optional loan ID, will generate if not provided
            
        Returns:
            LoanResult with selected lender and final terms
            
        Raises:
            ValueError: If no profitable lenders found
        """
        if loan_id is None:
            loan_id = str(uuid.uuid4())
        
        logger.info(f"Processing loan application {loan_id} for amount {loan_request.loan_amount}")
        
        # Step 1: Get eligible lenders (all lenders for now)
        eligible_lenders = self.get_eligible_lenders(loan_request)
        
        if not eligible_lenders:
            raise ValueError("No eligible lenders found")
        
        # Step 2: Find optimal terms for each lender
        optimized_terms = self.optimize_terms_for_lenders(loan_request, eligible_lenders)
        
        profitable_lenders = [terms for terms in optimized_terms if terms.both_profitable]
        
        if not profitable_lenders:
            raise ValueError("No profitable lending terms found for any lender")
        
        logger.info(f"Found {len(profitable_lenders)} profitable lenders out of {len(eligible_lenders)}")
        
        # Step 3: Execute selection algorithm
        selected_lender_id = self.select_optimal_lender(profitable_lenders)
        
        # Step 4: Get final terms for selected lender
        selected_terms = next(
            terms for terms in profitable_lenders 
            if terms.lender_id == selected_lender_id
        )
        
        # Create final result
        result = LoanResult(
            loan_id=loan_id,
            selected_lender_id=selected_lender_id,
            originator_weight=selected_terms.originator_weight,
            lender_weight=selected_terms.lender_weight,
            blended_rate=selected_terms.blended_rate,
            originator_profit=selected_terms.originator_profit,
            lender_profit=selected_terms.lender_profit,
            both_profitable=selected_terms.both_profitable,
            loan_amount=loan_request.loan_amount
        )
        
        logger.info(f"Selected lender {selected_lender_id} for loan {loan_id} with "
                   f"blended rate {selected_terms.blended_rate:.4f}")
        
        return result
    
    def get_eligible_lenders(self, loan_request: LoanRequest) -> List[LenderData]:
        """
        Get eligible lenders for the loan request.
        Currently returns all lenders, but could be enhanced with eligibility criteria.
        
        Args:
            loan_request: Loan request to evaluate
            
        Returns:
            List of eligible lenders
        """
        # For now, all lenders are eligible
        # Could add criteria like:
        # - Monthly limit checks
        # - Loan amount limits
        # - Risk criteria
        return self.available_lenders.copy()
    
    def optimize_terms_for_lenders(
        self,
        loan_request: LoanRequest,
        eligible_lenders: List[LenderData]
    ) -> List[OptimizedTerms]:
        """
        Optimize loan terms for each eligible lender.
        
        Args:
            loan_request: Original loan request
            eligible_lenders: List of eligible lenders
            
        Returns:
            List of OptimizedTerms for each lender
        """
        optimized_terms = []
        
        for lender in eligible_lenders:
            try:
                # Optimize participation ratio for this lender
                optimization_result = optimize_participation_ratio(
                    originator_rate=loan_request.originator_rate,
                    lender_rate=lender.base_interest_rate,
                    loan_amount=loan_request.loan_amount,
                    originator_cost_of_funds=loan_request.cost_of_funds,
                    lender_cost_of_funds=lender.cost_of_funds,
                    servicing_fee_rate=loan_request.servicing_fee
                )
                
                terms = OptimizedTerms(
                    lender_id=lender.lender_id,
                    originator_weight=optimization_result.optimal_originator_weight,
                    lender_weight=optimization_result.optimal_lender_weight,
                    originator_profit=optimization_result.originator_profit,
                    lender_profit=optimization_result.lender_profit,
                    blended_rate=optimization_result.blended_rate,
                    both_profitable=optimization_result.both_profitable
                )
                
                optimized_terms.append(terms)
                
                logger.debug(f"Optimized terms for lender {lender.lender_id}: "
                           f"profitable={terms.both_profitable}, "
                           f"orig_profit={terms.originator_profit:.4f}, "
                           f"lend_profit={terms.lender_profit:.4f}")
                
            except Exception as e:
                logger.error(f"Error optimizing terms for lender {lender.lender_id}: {e}")
                continue
        
        return optimized_terms
    
    def select_optimal_lender(self, profitable_lenders: List[OptimizedTerms]) -> str:
        """
        Select optimal lender using weighted random selection based on selection scores.
        
        Args:
            profitable_lenders: List of profitable lender terms
            
        Returns:
            Selected lender ID
        """
        # Create lender data for selection scoring
        lenders_with_profits = []
        
        for terms in profitable_lenders:
            # Find the corresponding lender data
            lender_data = next(
                lender for lender in self.available_lenders 
                if lender.lender_id == terms.lender_id
            )
            
            lenders_with_profits.append({
                'lender_id': terms.lender_id,
                'profit_percentage': terms.lender_profit,
                'approval_rate': lender_data.approval_rate,
                'allocated_limit': lender_data.allocated_limit
            })
        
        # Calculate selection scores
        selection_scores = calculate_selection_scores(lenders_with_profits)
        
        if not selection_scores:
            # Fallback to first lender if scoring fails
            logger.warning("Selection scoring failed, selecting first profitable lender")
            return profitable_lenders[0].lender_id
        
        # Select lender using weighted random selection
        selected_lender_id = select_lender_random(selection_scores)
        
        return selected_lender_id
    
    def add_lender(self, lender: LenderData) -> None:
        """Add a new lender to the available pool"""
        self.available_lenders.append(lender)
        logger.info(f"Added lender {lender.lender_id}")
    
    def remove_lender(self, lender_id: str) -> bool:
        """Remove a lender from the available pool"""
        for i, lender in enumerate(self.available_lenders):
            if lender.lender_id == lender_id:
                del self.available_lenders[i]
                logger.info(f"Removed lender {lender_id}")
                return True
        return False
    
    def get_lender_statistics(self) -> dict:
        """Get statistics about available lenders"""
        if not self.available_lenders:
            return {}
        
        total_allocated = sum(lender.allocated_limit for lender in self.available_lenders)
        avg_approval_rate = sum(lender.approval_rate for lender in self.available_lenders) / len(self.available_lenders)
        avg_interest_rate = sum(lender.base_interest_rate for lender in self.available_lenders) / len(self.available_lenders)
        
        return {
            'total_lenders': len(self.available_lenders),
            'total_allocated_limit': total_allocated,
            'average_approval_rate': avg_approval_rate,
            'average_interest_rate': avg_interest_rate,
            'lenders': [lender.lender_id for lender in self.available_lenders]
        }