# routes.py
from datetime import datetime

from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel
from src.models.models import Project
from src.utils.logging import setup_logger

logger = setup_logger(__name__)

project_router = APIRouter(prefix="/project", tags=["project"])

class ProjectRegisterInput(BaseModel):
    project_id: str
    requested_by: str
    system_message: str

@project_router.post("/register")
async def register_project(data: ProjectRegisterInput):
    if not data.requested_by.endswith("@mpib-berlin.mpg.de"):
        raise HTTPException(status_code=400, detail="the value of requested_by is not valid.")

    project = await Project.find_many({"project_id": data.project_id}).to_list()

    if len(project)>0:
        raise HTTPException(status_code=400, detail="there is already a project with this project_id")

    new_project = Project(
        project_id = data.project_id,
        created_by = data.requested_by,
        system_message = data.system_message,
        created_at = str(datetime.now())
    )

    await new_project.insert()


    return {"status": True, "doc_id": new_project.id, "project": new_project}
