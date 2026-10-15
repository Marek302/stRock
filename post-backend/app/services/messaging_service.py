"""
Fichier de la classe MessagingService
"""
from uuid import UUID
import httpx

from app.schemas.conversation import Conversation

MESSAGING_API_BASE_URL="http://messaging-api:8000"

class MessagingService:
    """Classe du service de massging"""

    def __init__(self):
        self.messaging_api_base_url = MESSAGING_API_BASE_URL
        if not self.messaging_api_base_url:
            raise ValueError("MESSAGING_API_BASE_URL environment variable not set")

    @staticmethod
    async def get_messaging_service() -> "MessagingService":
        """Récupération du service"""
        return MessagingService()

    async def get_message_by_post_and_participant(
            self,
            buyer_id,
            encoded_token,
            post_id
        ):
        """
        Méthode du service pour appellé la
        route /conversations/by-post-and-participant
        """
        url = (
            f"{self.messaging_api_base_url}"
            "/messaging/conversations/by-post-and-participant"
            f"?post_id={post_id}&buyer_id={buyer_id}"
        )
        async with httpx.AsyncClient() as client:
            response = await client.get(url=url,headers={
                "Authorization": f"Bearer {encoded_token}"
            })
            if response.status_code == 200:
                return Conversation.model_validate(response.json())
            else:
                response.raise_for_status()

    async def delete_by_post_id(
            self,
            post_id,
            encoded_token
            ) -> None:
        """Suppression des conversations avec le id d'un post"""
        url = (
            f"{self.messaging_api_base_url}"
            f"/messaging/post/{post_id}"
        )
        async with httpx.AsyncClient() as client:
            response = await client.delete(url=url,headers={
                "Authorization": f"Bearer {encoded_token}"
            })
            if response.status_code != 204:
                response.raise_for_status()



