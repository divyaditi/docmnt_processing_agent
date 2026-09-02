from groq import Groq
from typing import Any, Dict
import asyncio
import logging
from constant import (
    API_KEY, 
    MODEL, 
    TEMPERATURE,
    MAX_TOKENS,
    MAX_RETRIES, 
    TOP_P
)   

logger = logging.getLogger(__name__)


class GroqClient:
    """Client for invoking Groq API for document summarization"""
    
    def __init__(self):
        """Initialize Groq client with API key"""
        self.client = Groq(api_key=API_KEY)
        logger.info("GroqClient initialized")
     
    async def invoke_grok(self, message: str) -> Dict[str, Any]:
        """
        Call Groq API to summarize document content
        
        Args:
            message: The document text to summarize
            
        Returns:
            Dictionary with status and summarized content
        """
        try:
            logger.info(f"Invoking Groq API with {len(message)} characters")
            
            # Run the blocking Groq API call in a thread
            response = await asyncio.to_thread(
                self._call_groq_api,
                message
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error invoking Groq: {str(e)}", exc_info=True)
            return {
                "status": "error", 
                "data": {"error": str(e)}
            }
    
    def _call_groq_api(self, message: str) -> Dict[str, Any]:
        """
        Synchronous wrapper for Groq API call
        
        Args:
            message: Document text to summarize
            
        Returns:
            Parsed response dictionary
        """
        try:
            system_prompt = """You are an expert document summarizer. 
Analyze the provided document and create a concise, comprehensive summary that:
- Captures the main points and key information
- Maintains the original meaning and context
- Uses clear, professional language
- Is approximately 30-40% of the original length

Return ONLY the summary text, nothing else."""
            
            response = self.client.chat.completions.create(
                model=MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": f"Document to summarize:\n\n{message}",
                    },
                ],
                temperature=TEMPERATURE,
                max_completion_tokens=MAX_TOKENS,
                top_p=TOP_P,
                reasoning_effort="medium",
            )
            
            # Extract summary from response
            summary = response.choices[0].message.content if response.choices else ""
            
            logger.info(f"✅ Groq API returned summary: {len(summary)} characters")
            
            return {
                "status": "success",
                "data": {
                    "summary": summary,
                    "model": MODEL,
                    "tokens_used": response.usage.completion_tokens if hasattr(response, 'usage') else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error in Groq API call: {str(e)}", exc_info=True)
            raise
