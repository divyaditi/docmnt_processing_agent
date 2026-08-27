from fastapi import FastAPI
from router.health_router import router as health_router
from router.chat_router import router as process_chat
import uvicorn

app = FastAPI()
app.include_router(health_router)
app.include_router(process_chat)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080, reload=True)