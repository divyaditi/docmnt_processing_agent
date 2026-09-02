from fastapi import FastAPI
from router.health_router import router as health_router
from router.chat_router import router as chat_router
from config.logging_config import setup_logging
import uvicorn
import logging


setup_logging(log_level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Document Processing Agent", version="1.0.0")

app.include_router(health_router)
app.include_router(chat_router, prefix="/api")

logger.info("FastAPI application initialized")


@app.get("/")
async def root():
    return {
        "message": "Document Processing Agent API",
        "version": "1.0.0",
        "endpoints": {
            "health": "GET /health",
            "chat": "POST /api/chat"
        }
    }

if __name__ == "__main__":
    logger.info("Starting Uvicorn server on 0.0.0.0:8080")
    uvicorn.run(app, host="0.0.0.0", port=8080)