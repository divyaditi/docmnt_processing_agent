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
        # Validate file type
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Read file content
        content = await file.read()
        logger.debug(f"File read successfully: {len(content)} bytes")
        
        # Validate PDF magic bytes
        header = content[:5]
        if len(header) < 5 or header != PDF_MAGIC:
            raise HTTPException(status_code=400, detail="File is not a valid PDF")
        logger.info("PDF magic bytes validation passed")
    
        # Validate file size
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail=f"File must be <= {MAX_FILE_SIZE / (1024*1024):.1f} MB")
        logger.info(f"File size validation passed: {len(content)} bytes")
        
        # Save file to storage
        stored_file_path = file_storage_manager.save_file(content, file.filename)
        logger.info(f"File stored at: {stored_file_path}")

        # Initialize the document agent
        logger.info("Initializing DocumentAgent for workflow")
        agent = DocumentAgent()
        
        # Build the workflow graph
        workflow = agent.build_graph()
        logger.info("Workflow graph built successfully")
        
        # Create initial state with stored file path
        initial_state: DocumentState = {
            "file_path": stored_file_path,  # Use the stored file path
            "markdown_content": "",
            "summarized_text": "",
            "user_feedback": "",
            "retries": 0,
            "approved": False,
            "status": ""
        }
        logger.debug(f"Initial state created: file_path={stored_file_path}")
        
        # Invoke the workflow asynchronously using ainvoke
        logger.info("Starting workflow invocation")
        final_state = await workflow.ainvoke(initial_state)
        logger.info(f"Workflow completed with status: {final_state.get('status')}")
        
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
        logger.error(f"Error processing document: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
