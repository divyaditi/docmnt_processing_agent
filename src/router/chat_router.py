import logging
from fastapi import APIRouter, HTTPException
from service.chat_service import agent_chat
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post('/chat')
async def process_chat(message:str):
    try:
       response=await agent_chat(message)
    except Exception as e:
      logging.Exception(str(e),exc_info=True)
      raise HTTPException(status_code=400,message=str(e))
