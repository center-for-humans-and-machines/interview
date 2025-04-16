# routes.py
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel
from src.models.message import Conversations
from src.models.models import Project
from src.utils.llm_model import completion_with_backoff, init_model_endpoint
from src.utils.logging import setup_logger

logger = setup_logger(__name__)

dashboard_router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@dashboard_router.get("/login/{email}/{project_id}")
async def login(email: str, project_id: str):
    project = await Project.find_many(
        {"project_id": project_id, "created_by": email}
    ).to_list()
    if len(project) == 0:
        raise HTTPException(
            status_code=404, detail="project not found or email is wrong."
        )

    return {"status": True}


@dashboard_router.get("/projects/{email}")
async def list_of_projects(email: str):
    projects = await Project.find_many({"created_by": email}).to_list()
    return projects


@dashboard_router.get("/project/{project_id}")
async def list_of_projects(project_id: str):
    projects = await Project.find_many({"project_id": project_id}).to_list()
    return projects[0]


@dashboard_router.get("/conversations/{project_id}")
async def list_of_conversations(project_id: str):
    conversations = await Conversations.find_many({"project_id": project_id}).to_list()
    return conversations


@dashboard_router.get("/conversation/{conversation_id}")
async def list_of_conversations(conversation_id: str):
    conversations = await Conversations.find_many(
        {"conversation_id": conversation_id}
    ).to_list()
    return conversations[0]


@dashboard_router.post("/update_system_message")
async def list_of_conversations(project_id: str = Body(...), message: str = Body(...)):
    project = await Project.find_one(
        {"project_id": project_id}
    )

    logger.info(project)

    if not project:
        raise HTTPException(
            status_code=404, detail="project not found"
        )

    project.system_message = message
    await project.save()

    return {"status": True}
