from fastapi import HTTPException, UploadFile, File
from constant import ALLOWED_MIME_TYPES, PDF_MAGIC, MAX_FILE_SIZE
from utils.document_utils import file_storage_manager
import logging

logger = logging.getLogger(__name__)


async def agent_chat(file: UploadFile | str):
    """
    Process uploaded PDF file and return chat response.
    
    Args:
        file: Uploaded file object
        
    Returns:
        Dictionary with status and file path
    """
    try:
        # Validate file type
        logger.debug(f"Validating file type: {file.content_type}")
        if file.content_type not in ALLOWED_MIME_TYPES:
            error_msg = f"Invalid file type: {file.content_type}. Only PDF is allowed."
            logger.warning(error_msg)
            raise HTTPException(
                status_code=400,
                detail=error_msg,
            )
        logger.info(f"File type validation passed: {file.content_type}")
        
        # Read file content
        content = await file.read()
        logger.debug(f"File content read successfully: {len(content)} bytes")
        
        # Validate PDF magic bytes
        logger.debug("Validating PDF magic bytes...")
        header = content[:5]
        if len(header) < 5 or header != PDF_MAGIC:
            error_msg = "File is not a valid PDF (magic bytes check failed)."
            logger.warning(error_msg)
            raise HTTPException(
                status_code=400,
                detail=error_msg,
            )
        logger.info("PDF magic bytes validation passed")
        
        # Validate file size
        logger.debug(f"Validating file size: {len(content)} bytes vs {MAX_FILE_SIZE} bytes max")
        if len(content) > MAX_FILE_SIZE:
            error_msg = f"File must be <= {MAX_FILE_SIZE / (1024*1024):.1f} MB"
            logger.warning(error_msg)
            raise HTTPException(400, detail=error_msg)
        logger.info(f"File size validation passed: {len(content)} bytes")
        
        # Save file to storage

        stored_file_path = file_storage_manager.save_file(content, file.filename)
        logger.info(f"File stored at: {stored_file_path}")
        
        # TODO: Add graph invocation here
        logger.info(f"agent_chat completed successfully for file: {file.filename}")
        
        return {
            "status": "success",
            "filename": file.filename,
            "file_path": stored_file_path
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in agent_chat: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
