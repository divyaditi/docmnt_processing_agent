from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

async def agent_chat(chat_message: str):
    try:
        return chat_message
    except Exception as e:
        logger.exception(str(e))
        raise HTTPException(status_code=400, detail=str(e))