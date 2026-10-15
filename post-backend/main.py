"""

Point de démarrage

"""
import os
import asyncio
from pathlib import Path
import jwt
from fastapi import FastAPI, Request, WebSocket
from contextlib import asynccontextmanager
from app.api.v1 import listing
from app.api.v1 import image
from pyrate_limiter import Duration, Limiter, Rate
from fastapi_limiter.middleware import RateLimiterMiddleware
from sqlalchemy import event
from app.models.image_entity import ImageEntity
from typing import Union
from firebase_admin import initialize_app
from app.core.db import init_db, shutdown
from app.services.file_service import FileService
from app.exception_handlers import add_exception_handlers

async def default_identifier(request: Union[Request, WebSocket]):
    """Implemente le rate limit par user id"""
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
    """Définie le comportement de l'application"""
    init_db()
    FileService.init_storage()
    yield
    shutdown()

def receive_before_delete(mapper, connection, target: ImageEntity):
        async def _async_delete():
            await FileService.remove_file_from_path(target.image_path)

        def run_cleanup():
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(_async_delete())
            except RuntimeError:
                asyncio.run(_async_delete())

        run_cleanup()

def _setup_image_listeners():
    if not event.contains(ImageEntity, "before_delete", receive_before_delete):
        event.listen(ImageEntity, "before_delete", receive_before_delete)
    

            
def create_application() -> FastAPI:
    """Initialisation de l'API"""
    application = FastAPI(
        title="Listing API",
        description="Returns book listings for 10Books",
        version="1.0.0",
        lifespan=lifespan
    )
    application.include_router(
        listing.router,
        prefix="/api/v1/listings",
        tags=["Listings"]
    )
    application.include_router(
        image.router,
        prefix="/api/v1/images",
        tags=["Images"]
    )
    if os.getenv("ENVIRONMENT") != "TEST":
        application.add_middleware(
            RateLimiterMiddleware,
            limiter=Limiter(Rate(60, Duration.SECOND)),
            identifier=default_identifier
        )
    _setup_image_listeners()
    add_exception_handlers(app=application)
    return application

firebase_app = initialize_app()
app = create_application()


@app.get("/")
async def root():
    """Route par défaut"""
    return {"message": "Hello World !"}
