import logging
from fastapi import APIRouter, HTTPException, File, UploadFile
from service.chat_service import agent_chat

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
        response = await agent_chat(file)
        logger.info(f"File parsed successfully: {file.filename}")
        return {
            "status": "success",
            "message": "File processed successfully",
            "data": response
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
