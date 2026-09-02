from langchain.agents import create_agent
from langchain_groq import ChatGroq
from groq import Groq
from typing import Any, Dict
import asyncio
import json
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
    def __init__(self):
        self.client = Groq(api_key=API_KEY)
        self.parser = OutputParser()
     
    async def invoke_grok(self, system_prompt:str message: str) -> Dict[str, Any]:
        """
        Call Groq API with user message
        
        Args:
            message: The user message/document text to process
            
        Returns:
            Parsed response dictionary
        """
        try:
            response = self.client.chat.completions.create(
                model=MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": f"Document text:\n{message}",
                    },
                ],
                temperature=TEMPERATURE,
                max_completion_tokens=MAX_TOKENS,
                top_p=TOP_P,
                reasoning_effort="medium",
            )
            return response
        except Exception as e:
            logger.error(f"Error invoking Groq: {str(e)}")
            return {"status": "error", "data": {"error": str(e)}}


groq=GroqClient()





