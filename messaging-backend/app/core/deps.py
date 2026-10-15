from fastapi import Request
from app.services.messaging_service import MessagingService

def get_messaging_service(request: Request) -> MessagingService:
    return request.app.state.messaging_service

