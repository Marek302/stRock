from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError
from app.models.messaging import Conversation, Message
from app.schemas.messaging import ConversationDTO, MessageDTO


@pytest.mark.parametrize('author', ['strock-demo-alice', 'strock-demo-karim', 'strock-demo-lea', 'u' * 128])
def test_conversation_accepts_publication_author(author):
    conversation = Conversation(
        id=uuid4(), listing_id=uuid4(), participants=['u' * 28, author],
        created_at=datetime.now(timezone.utc),
    )
    dto = ConversationDTO(**conversation.model_dump(), other_participant_firebase_uid=author)
    assert dto.participants[1] == author
    assert dto.other_participant_firebase_uid == author
    message = Message(
        id=uuid4(), conversation_id=conversation.id, sender_uid=author,
        content='Bonjour', timestamp=datetime.now(timezone.utc), read_by=[author],
    )
    assert MessageDTO(**message.model_dump()).sender_uid == author


@pytest.mark.parametrize('author', ['', 'u' * 129])
def test_conversation_rejects_invalid_author(author):
    with pytest.raises(ValidationError):
        Conversation(
            id=uuid4(), listing_id=uuid4(), participants=['u' * 28, author],
            created_at=datetime.now(timezone.utc),
        )
