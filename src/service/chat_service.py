from fastapi import HTTPException, UploadFile, File
from constant import ALLOWED_MIME_TYPES, PDF_MAGIC, MAX_FILE_SIZE
from utils.document_utils import file_storage_manager
from agent.document_agent import DocumentAgent, DocumentState
import logging
import asyncio

logger = logging.getLogger(__name__)


async def process_doc(file: UploadFile | str) -> dict:
    """
    Process uploaded PDF file with human-in-the-loop approval workflow.
    
    Args:
        file: Uploaded PDF file
        
    Returns:
        Dictionary with processing result including summary, approval status, and retries
    """
    try:
        logger.info(f"VALIDATION PHASE - Validating file: {file.filename}")
        
        # Read file content first to validate with magic bytes
        content = await file.read()
        
        # Validate PDF magic bytes (most reliable method)
        header = content[:5]
        if len(header) < 5 or header != PDF_MAGIC:
            logger.error(f"Invalid PDF magic bytes: {header} (expected: {PDF_MAGIC})")
            raise HTTPException(status_code=400, detail="File is not a valid PDF")
    
        # Validate file size
        if len(content) > MAX_FILE_SIZE:
            max_mb = MAX_FILE_SIZE / (1024*1024)
            logger.error(f" File size exceeds limit: {len(content)} bytes > {MAX_FILE_SIZE} bytes ({max_mb:.1f} MB)")
            raise HTTPException(status_code=400, detail=f"File must be <= {max_mb:.1f} MB")
        logger.info(f"✓ File size validation passed: {len(content)} bytes ({len(content) / (1024*1024):.2f} MB)") 
       
        # Save file to storage
        stored_file_path = file_storage_manager.save_file(content, file.filename)
        logger.info(f"✓ File stored successfully at: {stored_file_path}")

        agent = DocumentAgent()
        
        workflow = agent.build_graph()
        logger.debug("✓ Workflow graph compiled successfully")
        
        # Create initial state with stored file path
        initial_state: DocumentState = {
            "file_path": stored_file_path,
            "markdown_content": "",
            "summarized_text": "",
            "user_feedback": "",
            "retries": 0,
            "approved": False,
            "status": ""
        }

        final_state = await workflow.ainvoke(initial_state)
        
        # Return the result
        return {
            "status": "success",
            "file_path": stored_file_path,
            "filename": file.filename,
            "workflow_result": {
                "approved": final_state.get("approved"),
                "summary": final_state.get("summarized_text"),
                "retries": final_state.get("retries"),
                "final_status": final_state.get("status")
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
