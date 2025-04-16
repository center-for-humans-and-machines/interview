import time
import motor.motor_asyncio
from beanie import init_beanie
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.models import __beanie_models__, get_settings
from src.routes.dashboard import dashboard_router
from src.routes.download import download_router
from src.routes.project import project_router
from src.utils.logging import setup_logger
from src.routes.project import register_project, ProjectRegisterInput
from src.models.message import ConversationMessage, Conversations
from src.models.models import Project

# SETUP

logger = setup_logger(__name__)

app = FastAPI()
settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(project_router)
app.include_router(download_router)
app.include_router(dashboard_router)


# Initialize database
async def init_db():
    # Create an asynchronous MongoDB client
    client = motor.motor_asyncio.AsyncIOMotorClient(settings.mongo_url)
    database = client[settings.database_name]

    # Initialize Beanie ODM with the MongoDB database
    await init_beanie(database=database, document_models=__beanie_models__)


# Startup event to initialize the database
@app.on_event("startup")
async def startup_event():
    logger.info("Startup event started")
    await init_db()

    await Project.delete_all()
    await Conversations.delete_all()

    await register_project(
        data=ProjectRegisterInput(
            project_id="test_project",
            requested_by="test@mpib-berlin.mpg.de",
            system_message="test",
        )
    )

    example_chat = [
        ConversationMessage(
            role="system",
            content="it is the system_message",
            timestamp=time.time(),
            type="text",
        ),
        ConversationMessage(
            role="user", content="hi", timestamp=time.time(), type="text"
        ),
        ConversationMessage(
            role="assistant",
            content="hello, how can I help you?",
            timestamp=time.time(),
            type="text",
        ),
    ]

    new_conversation = Conversations(
        conversation_id="testid",
        created_at=time.time(),
        participant_id="test_participant",
        experiment_id="test_experiment",
        model="gpt-4o",
        messages=example_chat,
        project_id="test_project",
    )
    await new_conversation.insert()
