from datetime import datetime
from typing import List, Literal, TypedDict

from beanie import Document
from pydantic import Field


class OpenAIMessage(TypedDict):
    role: str
    content: str

class MessageDocument(TypedDict):
    content: str | List
    role: Literal["user", "assistant", "system"]
    timestamp: str
    type: Literal["image", "text"]

class ConversationMessage(TypedDict):
    content: str | List
    role: Literal["user", "assistant", "system"]
    timestamp: str
    type: Literal["image", "text"]

class Conversations(Document):
    conversation_id: str
    created_at: str
    participant_id: str
    experiment_id: str
    model: str = Field(..., env="MODEL")
    messages: List[ConversationMessage] = Field(default_factory=list)
    project_id: str

class SearchParameters(Document):
    session_id: str
    timestamp: str
    search_parameters: dict


class Participant(Document):
    participant_id: str
    black_listed: bool = Field(default=False)


def parse_from_open_ai(
    message: str,
) -> MessageDocument:
    return MessageDocument(
        content=message,
        role="assistant",
        timestamp=str(datetime.now()),
        type="text",
    )


def parse_to_open_ai(message: MessageDocument) -> OpenAIMessage:
    return {
        "role": message['role'],
        "content": message['content'],
    }
