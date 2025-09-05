"""
Batch processing API endpoints.
"""

import os
import uuid
from pathlib import Path
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import BatchUploadResponse, BatchStatusResponse
from app.core.excel import process_excel_batch, validate_excel_columns
import pandas as pd

router = APIRouter(prefix="/api", tags=["batch"])

# In-memory batch status tracking (in production, use Redis or database)
batch_status: Dict[str, Dict[str, Any]] = {}


@router.post("/batch-upload", response_model=BatchUploadResponse)
async def upload_batch_file(
    file: UploadFile = File(...),
    program_id: int = 1,
    db: Session = Depends(get_db)
):
    """
    Upload Excel file for batch loan processing.
    
    Args:
        file: Excel file with loan data
        program_id: Program ID for allocation strategy
        db: Database session
        
    Returns:
        Batch upload response with batch ID and status
    """
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are supported")
    
    try:
        # Generate batch ID
        batch_id = str(uuid.uuid4())
        
        # Create uploads directory if it doesn't exist
        uploads_dir = Path("uploads")
        uploads_dir.mkdir(exist_ok=True)
        
        # Save uploaded file
        file_path = uploads_dir / f"{batch_id}_{file.filename}"
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Quick validation of file structure
        try:
            df = pd.read_excel(file_path)
            missing_cols = validate_excel_columns(df)
            if missing_cols:
                # Clean up file and raise error
                os.remove(file_path)
                raise HTTPException(
                    status_code=400, 
                    detail=f"Missing required columns: {', '.join(missing_cols)}"
                )
            
            total_loans = len(df)
        except Exception as e:
            # Clean up file and raise error
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(status_code=400, detail=f"Invalid Excel file: {str(e)}")
        
        # Initialize batch status
        batch_status[batch_id] = {
            'status': 'UPLOADED',
            'progress': 0,
            'total_loans': total_loans,
            'processed_loans': 0,
            'failed_loans': 0,
            'file_path': str(file_path),
            'program_id': program_id
        }
        
        # Estimate processing time (roughly 10ms per loan + overhead)
        estimated_time_min = max(1, (total_loans * 10) // (60 * 1000))
        
        return BatchUploadResponse(
            batch_id=batch_id,
            total_loans=total_loans,
            status="UPLOADED",
            estimated_time_min=estimated_time_min
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/batch-process/{batch_id}")
async def start_batch_processing(
    batch_id: str,
    db: Session = Depends(get_db)
):
    """
    Start processing a batch of loans.
    
    Args:
        batch_id: Batch ID from upload
        db: Database session
        
    Returns:
        Processing status
    """
    if batch_id not in batch_status:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    batch_info = batch_status[batch_id]
    
    if batch_info['status'] != 'UPLOADED':
        raise HTTPException(status_code=400, detail=f"Batch is not ready for processing. Status: {batch_info['status']}")
    
    try:
        # Update status to processing
        batch_status[batch_id]['status'] = 'PROCESSING'
        
        # Process the batch (this is synchronous for simplicity, in production use background tasks)
        file_path = batch_info['file_path']
        program_id = batch_info['program_id']
        
        results_path = process_excel_batch(file_path, program_id, db)
        
        # Update batch status
        batch_status[batch_id].update({
            'status': 'COMPLETED',
            'progress': 100,
            'processed_loans': batch_info['total_loans'],
            'results_path': results_path
        })
        
        return {"message": "Processing completed", "batch_id": batch_id}
        
    except Exception as e:
        # Update status to failed
        batch_status[batch_id]['status'] = 'FAILED'
        batch_status[batch_id]['error'] = str(e)
        
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.get("/batch-status/{batch_id}", response_model=BatchStatusResponse)
async def get_batch_status(batch_id: str):
    """
    Get batch processing status.
    
    Args:
        batch_id: Batch ID
        
    Returns:
        Batch status information
    """
    if batch_id not in batch_status:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    batch_info = batch_status[batch_id]
    
    return BatchStatusResponse(
        batch_id=batch_id,
        status=batch_info['status'],
        progress=batch_info['progress'],
        total_loans=batch_info['total_loans'],
        processed_loans=batch_info['processed_loans'],
        failed_loans=batch_info['failed_loans']
    )


@router.get("/batch-download/{batch_id}")
async def download_batch_results(batch_id: str):
    """
    Download processed batch results as Excel file.
    
    Args:
        batch_id: Batch ID
        
    Returns:
        Excel file with results
    """
    if batch_id not in batch_status:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    batch_info = batch_status[batch_id]
    
    if batch_info['status'] != 'COMPLETED':
        raise HTTPException(status_code=400, detail=f"Batch is not completed. Status: {batch_info['status']}")
    
    results_path = batch_info.get('results_path')
    if not results_path or not os.path.exists(results_path):
        raise HTTPException(status_code=404, detail="Results file not found")
    
    return FileResponse(
        path=results_path,
        filename=f"allocation_results_{batch_id}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )