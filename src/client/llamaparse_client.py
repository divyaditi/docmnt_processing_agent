"""
Llamaparse client for parsing PDF documents and extracting markdown content.
Supports both file paths and binary content.
"""
import logging
import io
from typing import List
from pathlib import Path
from constant import LLAMA_PARSE_KEY
from llama_parse import LlamaParse


logger = logging.getLogger(__name__)


class LlamaparseClient:
    """Client for parsing PDF documents using Llamaparse API."""
    
    def __init__(self):
        """Initialize Llamaparse client with API key."""
        if not LLAMA_PARSE_KEY:
            raise ValueError("LLAMA_PARSE_KEY is not set in constants")
        
        self.api_key = LLAMA_PARSE_KEY
        self.parser = LlamaParse(api_key=self.api_key, result_type="markdown")
        logger.info("Llamaparse client initialized successfully")
    
    def read_file_bytes(self, file_path: str) -> bytes:
        """
        Read a file from disk and return its binary content.
        Args:
            file_path: Path to the file
        Returns:
            Binary content of the file
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            if not file_path.is_file():
                raise ValueError(f"Path is not a file: {file_path}")
            
            with open(file_path, 'rb') as f:
                file_bytes = f.read()
            
            logger.info(f"File read successfully: {file_path} ({len(file_bytes)} bytes)")
            return file_bytes
            
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {str(e)}", exc_info=True)
            raise
    
    async def parse_document_from_path(self, file_path: str) -> str:
        """
        Parse a PDF document from file path on disk using Llamaparse API.
        Reads the file bytes and parses to markdown.
        Args:
            file_path: Path to the PDF file on disk  
        Returns:
            Markdown content extracted from the PDF
        """
        try:
            logger.info(f"Starting document parsing from path: {file_path}")
            
            # Read file bytes from disk
            file_bytes = self.read_file_bytes(file_path)
            filename = Path(file_path).name
            
            logger.debug(f"File read: {filename} ({len(file_bytes)} bytes)")
            logger.debug(f"Calling Llamaparse API to parse: {filename}")
            
            # Create a temporary file-like object from bytes for Llamaparse
            file_obj = io.BytesIO(file_bytes)
            
            # Call Llamaparse API with extra_info containing filename
            markdown_content = await self.parser.aload_data(
                file_obj,
                extra_info={"file_name": filename}
            )
            
            logger.info(f"Document parsed successfully from path: {file_path}")
            logger.debug(f"Markdown content length: {len(markdown_content)} characters")
            
            return markdown_content
            
        except Exception as e:
            logger.error(f"Error parsing document from path {file_path}: {str(e)}", exc_info=True)
            raise
    
    async def parse_document(self, file_bytes: bytes, filename: str) -> str:
        """
        Parse a PDF document from bytes content.
        
        Args:
            file_bytes: Binary content of the PDF file
            filename: Name of the file for logging purposes
            
        Returns:
            Markdown content extracted from the PDF
        """
        try:
            logger.info(f"Starting document parsing: {filename} ({len(file_bytes)} bytes)")
            
            # Create a temporary file-like object from bytes
            file_obj = io.BytesIO(file_bytes)
            
            logger.debug(f"Calling Llamaparse API for: {filename}")
            
            # Parse the document with extra_info containing filename
            markdown_content = await self.parser.aload_data(
                file_obj,
                extra_info={"file_name": filename}
            )
            
            logger.info(f"Document parsed successfully: {filename}")
            logger.debug(f"Markdown content length: {len(markdown_content)} characters")
            
            return markdown_content
            
        except Exception as e:
            logger.error(f"Error parsing document {filename}: {str(e)}", exc_info=True)
            raise
    
  
llamaparser= LlamaparseClient()

