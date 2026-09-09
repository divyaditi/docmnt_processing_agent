import logging
from fastapi import APIRouter, HTTPException, File, UploadFile
from service.chat_service import process_doc

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])

@router.post("/chat")
async def process_chat(file: UploadFile = File(...)):
    """
    Upload and process a PDF file.
    
    Parameters:
    - file: PDF file to upload (multipart/form-data)
    
    Returns:
    - Success response with file path
    """
    
    try:
        
        response = await process_doc(file)
        
        return {
            "status": "success",
            "message": "File processed successfully",
            "data": response
        }
    except HTTPException as http_exc:
        logger.warning(f"⚠️  HTTP Exception: {http_exc.status_code} - {http_exc.detail}")
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
