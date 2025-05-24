from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, Optional, List
import os
import tempfile
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
    title="Your Service API",
    description="API for Your Service that integrates with the Scaffold Framework",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify exact origins
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
        "service": "your-service",
        "version": "1.0.0",
    }

# Example API endpoint
@app.post("/your-endpoint")
async def your_endpoint(param1: str, param2: int) -> Dict[str, Any]:
    """
    Example endpoint for your service.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Dict: Results from the service
    """
    try:
        # Your service logic here
        result = {
            "status": "success",
            "service": "your-service",
            "results": {
                "param1": param1,
                "param2": param2,
                "processed": True,
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
    Process an uploaded file.
    
    Args:
        file: Uploaded file
        options: Optional processing parameters as JSON string
        
    Returns:
        Dict: Processing results
    """
    try:
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            content = await file.read()
            temp.write(content)
            temp_path = temp.name
        
        # Process the file (replace with your processing logic)
        # For example: result = your_processing_function(temp_path, options)
        
        # Cleanup
        os.unlink(temp_path)
        
        # Return results
        return {
            "status": "success",
            "service": "your-service",
            "filename": file.filename,
            "results": [
                # Your processing results here
            ]
        }
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