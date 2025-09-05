#!/usr/bin/env python3
"""
Script to run the FastAPI server.
"""

import uvicorn
import os

if __name__ == "__main__":
    # Ensure required directories exist
    os.makedirs("data", exist_ok=True)
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("results", exist_ok=True)
    
    # Run the server
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload in development
        log_level="info"
    )