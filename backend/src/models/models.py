from datetime import datetime
from typing import Any, Dict, List

from beanie import Document
from pydantic import Field


class Project(Document):
    project_id: str
    created_at: str
    created_by: str
    system_message: str

class LlmCall(Document):
    project_id: str
    chat: List[Dict[str, Any]]
    response: Dict[str, Any]
    created_at: str
