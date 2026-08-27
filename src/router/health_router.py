from fastapi import APIRouter, HTTPException
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/health")
def healthcheck():
    try:
        return {
            "message": "Healthy",
            "status": 200
        }
    except Exception as e:
        logger.exception(str(e),exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))
