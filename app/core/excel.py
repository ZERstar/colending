"""
Excel processing functionality for batch loan processing.
"""

import uuid
import pandas as pd
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.core.allocation import allocate_loan


def validate_excel_columns(df: pd.DataFrame) -> List[str]:
    """
    Validate required columns in uploaded Excel file.
    
    Args:
        df: Pandas DataFrame
        
    Returns:
        List of missing columns (empty if valid)
    """
    required_cols = [
        'client_loan_id', 'loan_amount', 'cibil_score', 
        'loan_foir', 'interest_rate', 'product_type'
    ]
    missing_cols = [col for col in required_cols if col not in df.columns]
    return missing_cols


def process_excel_batch(file_path: str, program_id: int, db: Session) -> str:
    """
    Process Excel file with batch loan allocations.
    
    Args:
        file_path: Path to uploaded Excel file
        program_id: Program ID for allocation
        db: Database session
        
    Returns:
        Path to results Excel file
    """
    try:
        # Read Excel file
        df = pd.read_excel(file_path)
        
        # Validate columns
        missing_cols = validate_excel_columns(df)
        if missing_cols:
            raise ValueError(f"Missing required columns: {', '.join(missing_cols)}")
        
        # Process each loan
        results = []
        for idx, row in df.iterrows():
            try:
                # Prepare loan data
                loan_data = {
                    'loan_id': str(row['client_loan_id']),
                    'amount': float(row['loan_amount']),
                    'orig_rate': float(row['interest_rate']) / 100 if row['interest_rate'] > 1 else float(row['interest_rate']),
                    'cibil_score': int(row['cibil_score']),
                    'foir': float(row['loan_foir']),
                    'ltr': float(row.get('ltr', 0)),
                    'product_type': str(row['product_type']),
                    'cost_of_funds': float(row.get('cost_of_funds', 0.092))
                }
                
                # Allocate loan
                result = allocate_loan(loan_data, program_id, db)
                
                # Prepare result row
                result_row = {
                    **row.to_dict(),
                    'status': 'SUCCESS',
                    'selected_partner': result['recommended_partner'].name,
                    'selected_partner_id': result['recommended_partner'].partner_id,
                    'approval_probability': result['recommended_partner'].approval_prob,
                    'profit_score': result['recommended_partner'].profit_score,
                    'selection_score': result['recommended_partner'].selection_score,
                    'reasoning': result['reasoning'],
                    'processing_time_ms': result['processing_time_ms']
                }
                
                results.append(result_row)
                
            except Exception as e:
                # Handle individual loan errors
                error_row = {
                    **row.to_dict(),
                    'status': 'ERROR',
                    'error_message': str(e),
                    'selected_partner': None,
                    'selected_partner_id': None,
                    'approval_probability': None,
                    'profit_score': None,
                    'selection_score': None,
                    'reasoning': None,
                    'processing_time_ms': None
                }
                results.append(error_row)
        
        # Create results DataFrame
        results_df = pd.DataFrame(results)
        
        # Generate unique output filename
        output_filename = f"results_{uuid.uuid4().hex[:8]}.xlsx"
        output_path = f"results/{output_filename}"
        
        # Save results to Excel
        results_df.to_excel(output_path, index=False)
        
        return output_path
        
    except Exception as e:
        raise Exception(f"Excel processing failed: {str(e)}")


def create_batch_summary(results_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Create summary statistics for batch processing results.
    
    Args:
        results_df: Results DataFrame
        
    Returns:
        Summary statistics dictionary
    """
    total_loans = len(results_df)
    successful_loans = len(results_df[results_df['status'] == 'SUCCESS'])
    failed_loans = len(results_df[results_df['status'] == 'ERROR'])
    
    summary = {
        'total_loans': total_loans,
        'successful_allocations': successful_loans,
        'failed_allocations': failed_loans,
        'success_rate': (successful_loans / total_loans * 100) if total_loans > 0 else 0
    }
    
    if successful_loans > 0:
        success_df = results_df[results_df['status'] == 'SUCCESS']
        summary.update({
            'avg_processing_time_ms': success_df['processing_time_ms'].mean(),
            'avg_approval_probability': success_df['approval_probability'].mean(),
            'avg_profit_score': success_df['profit_score'].mean(),
            'partner_distribution': success_df['selected_partner'].value_counts().to_dict()
        })
    
    return summary