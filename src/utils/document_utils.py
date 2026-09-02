"""
Utility functions for document processing and file handling.
"""
import logging
import json
from typing import Any, Dict
from pathlib import Path
from datetime import datetime
from constant import FILES_STORAGE_PATH
from fastapi import UploadFile

logger = logging.getLogger(__name__)


class FileStorageManager:
    """Manages file storage operations."""
    
    def __init__(self, storage_path: str = FILES_STORAGE_PATH):
        """
        Initialize the file storage manager.
        Args:
            storage_path: Path where files will be stored
        """
        self.storage_path = Path(storage_path)
        self._ensure_storage_directory()
    
    def _ensure_storage_directory(self):
        """Create storage directory if it doesn't exist."""
        try:
            self.storage_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Storage directory ready: {self.storage_path.absolute()}")
        except Exception as e:
            logger.error(f"Failed to create storage directory: {str(e)}", exc_info=True)
            raise
    
    def save_file(self, file_content: bytes, original_filename: str) -> str:
        """
        Save file to storage directory.
        Args:
            file_content: Binary content of the file
            original_filename: Original name of the file
            
        Returns:
            Relative file path where the file was stored
        """
        try:
            # Generate filename with timestamp to avoid conflicts
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_stem = Path(original_filename).stem
            file_suffix = Path(original_filename).suffix
            
            stored_filename = f"{file_stem}_{timestamp}{file_suffix}"
            file_path = self.storage_path / stored_filename
            
            logger.debug(f"Writing file to disk: {file_path}")
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            logger.info(f"File saved successfully: {file_path} ({len(file_content)} bytes)")
            
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Failed to save file: {str(e)}", exc_info=True)
            raise
    
    def get_file_path(self, filename: str) -> Path:
        """
        Get full path to a stored file.
        Args:
            filename: Name of the file  
        Returns:
            Path object to the file
        """
        return self.storage_path / filename
    
    def file_exists(self, filename: str) -> bool:
        """
        Check if a file exists in storage.
        Args:
            filename: Name of the file    
        Returns:
            True if file exists, False otherwise
        """
        file_path = self.get_file_path(filename)
        return file_path.exists()


class DocumentUtils:
    """Utility class for document processing."""
    
    @staticmethod
    def parse_response(response: Any) -> Dict[str, str]:
        """
        Extract the text content from Groq API response
        Args:
            response: The response object from Groq API
        Returns:
            Dictionary containing parsed response
        """
        try:
            # Extract the text content from the response
            if hasattr(response, 'choices') and len(response.choices) > 0:
                content = response.choices[0].message.content   
                try:
                    parsed_json = json.loads(content)
                    return {"status": "success", "data": parsed_json}
                except json.JSONDecodeError:
                    # If not valid JSON, return as plain text
                    return {"status": "success", "data": {"summary": content}}
            else:
                return {"status": "error", "data": {"error": "No choices in response"}}
                
        except Exception as e:
            logger.error(f"Error parsing response: {str(e)}")
            return {"status": "error", "data": {"error": str(e)}}
    
    @staticmethod
    def parse_stream_response(stream_response: Any) -> str:
        """
        Parse streaming response from Groq API 
        Args:
            stream_response: The streaming response object
        Returns:
            Concatenated string of all chunks
        """
        try:
            content = ""
            for chunk in stream_response:
                if chunk.choices[0].delta.content:
                    content += chunk.choices[0].delta.content
            try:
                parsed_json = json.loads(content)
                return json.dumps(parsed_json, indent=2)
            except json.JSONDecodeError:
                return content
                
        except Exception as e:
            logger.error(f"Error parsing stream: {str(e)}")
            return ""



file_storage_manager = FileStorageManager()
doc_utils = DocumentUtils()
