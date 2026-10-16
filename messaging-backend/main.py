import os
import jwt
from typing import Union
from fastapi_limiter.middleware import RateLimiterMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import FastAPI, Request, WebSocket
from fastapi.concurrency import asynccontextmanager
from pyrate_limiter import Duration, Limiter, Rate

from app.api.routes import router
from app.api.images import router as images_router
from app.core.exception_handler import add_exception_handlers
from app.services.messaging_repo import MongoMessagingRepository
from app.services.messaging_service import MessagingService
from app.services.image_repo import MongoImageRepository
from app.services.image_service import ImageService
from app.services.push_notification_service import PushNotificationService
from app.services.ws_manager import ConversationWebSocketManager
from app.core.db import get_settings
from fastapi.middleware.cors import CORSMiddleware

async def default_identifier(request: Union[Request, WebSocket]):
    """Implemente le rate limit par user id / """
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        return request.client.host 

    try:
        token = auth_header.split(" ")[1]
        decoded_token = jwt.decode(token, options={"verify_signature": False}) 
        return decoded_token.get("uid") or request.client.host
    except Exception:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0]
        elif request.client:
            ip = request.client.host
        else:
            ip = "127.0.0.1"
        return ip + ":" + request.scope["path"]

@asynccontextmanager
async def lifespan(app: FastAPI):
    client = AsyncIOMotorClient(get_settings().mongo_uri)
    db = client[get_settings().mongo_db_name]
    
    # Images
    image_repo = MongoImageRepository(db)
    image_service = ImageService(image_repo)
    app.state.image_service = image_service

    # Messaging
    messaging_repo = MongoMessagingRepository(db)
    await messaging_repo.ensure_indexes()
    notification_service = PushNotificationService()
    app.state.messaging_service = MessagingService(messaging_repo, image_service, notification_service)
    
    app.state.mongo_client = client
    app.state.ws_manager = ConversationWebSocketManager()
    yield
    client.close()

def create_app() -> FastAPI:

    app = FastAPI(
        title="Rock-On! Messaging API",
        lifespan=lifespan,
        description="Messaging service for Rock-On!",
        version="1.0.0"
        )

    origins = [
    "http://localhost:5173",      
    "http://127.0.0.1:5173",          
    "http://localhost:8080",
]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],          
        allow_headers=["*"],              
    )

    @app.get("/health")
    async def health():
        return {"service": "Rock-On! Messaging API", "status": "ok"}

    app.include_router(
        router,
        prefix="/messaging",
        tags=["messaging"]
    )
    app.include_router(
        images_router,
        prefix="/messaging/images",
        tags=["images"]
    )
    add_exception_handlers(app)
    if os.getenv("ENVIRONMENT") != "TEST":
        app.add_middleware(
            RateLimiterMiddleware,
            limiter=Limiter(Rate(5, Duration.SECOND)),
            identifier=default_identifier
        )
    return app

app = create_app()
