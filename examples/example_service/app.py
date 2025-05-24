from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, Optional, List
import os
import tempfile
import json
import pandas as pd
import uvicorn
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Example Data Processing Service",
    description="Example service that processes data files and integrates with the Scaffold Framework",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.
    
    Returns:
        Dict: Service health status
    """
    return {
        "status": "healthy",
        "service": "example-data-processor",
        "version": "1.0.0",
    }

# Data statistics endpoint
@app.post("/get-stats")
async def get_stats(columns: List[str]) -> Dict[str, Any]:
    """
    Get statistics for specified columns in the dataset.
    
    Args:
        columns: List of column names to analyze
        
    Returns:
        Dict: Column statistics
    """
    try:
        # This would normally process a stored dataset
        # For this example, we'll just return mock data
        result = {
            "status": "success",
            "service": "example-data-processor",
            "results": {
                column: {
                    "mean": 0.5,
                    "median": 0.4,
                    "std": 0.2,
                    "min": 0.0,
                    "max": 1.0,
                } for column in columns
            }
        }
        return result
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# File upload endpoint
@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    options: Optional[str] = Form(None)
) -> Dict[str, Any]:
    """
    Process an uploaded data file.
    
    Args:
        file: Uploaded file (CSV, Excel)
        options: Optional processing parameters as JSON string
        
    Returns:
        Dict: Processing results with data summary
    """
    try:
        # Parse options if provided
        process_options = {}
        if options:
            process_options = json.loads(options)
            
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp:
            content = await file.read()
            temp.write(content)
            temp_path = temp.name
        
        # Process the file
        try:
            # Read data file
            df = pd.read_csv(temp_path)
            
            # Basic data summary
            summary = {
                "rows": len(df),
                "columns": list(df.columns),
                "numeric_columns": list(df.select_dtypes(include=['number']).columns),
                "missing_values": df.isnull().sum().to_dict(),
                "column_types": {col: str(dtype) for col, dtype in df.dtypes.items()}
            }
            
            # Optional: calculate statistics for numeric columns
            if process_options.get("calculate_stats", True):
                stats = {}
                for col in df.select_dtypes(include=['number']).columns:
                    stats[col] = {
                        "mean": float(df[col].mean()),
                        "median": float(df[col].median()),
                        "std": float(df[col].std()),
                        "min": float(df[col].min()),
                        "max": float(df[col].max()),
                    }
                summary["statistics"] = stats
                
            # Return results
            return {
                "status": "success",
                "service": "example-data-processor",
                "filename": file.filename,
                "summary": summary
            }
            
        except Exception as e:
            logger.error(f"Error processing file: {e}")
            raise HTTPException(status_code=422, detail=f"Error processing file: {str(e)}")
        finally:
            # Cleanup temporary file
            os.unlink(temp_path)
            
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid options format")
    except Exception as e:
        logger.error(f"Error processing file upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Run the application
if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    ) 