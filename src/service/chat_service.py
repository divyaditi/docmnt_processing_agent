from fastapi import HTTPException, UploadFile, File
from constant import ALLOWED_MIME_TYPES, PDF_MAGIC, MAX_FILE_SIZE
from utils.document_utils import file_storage_manager
from client.llamaparse_client import LlamaparseClient
import logging

logger = logging.getLogger(__name__)


async def process_doc(file: UploadFile | str)->str:
    """
    Process uploaded PDF file and return markdown content.
    """
    try:
        # Validate file type
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        content = await file.read()
        
        header = content[:5]
        if len(header) < 5 or header != PDF_MAGIC:
            raise HTTPException(status_code=400, detail="File is not a valid PDF")
    
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail=f"File must be <= {MAX_FILE_SIZE / (1024*1024):.1f} MB")
        
        stored_file_path = file_storage_manager.save_file(content, file.filename)
        logger.info(f"File stored at: {stored_file_path}")
        
        return stored_file_path

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))