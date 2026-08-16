from fastapi import FastAPI

from app.api.routes.auth import router as auth_router
from app.api.routes.upload import router as upload_router
from app.api.routes.debug import router as debug_router
from app.api.routes.chat import router as chat_router
from app.api.routes.quiz import router as quiz_router
from app.api.routes.summary import router as summary_router
from app.api.routes.syllabus import router as syllabus_router

from app.core.database import (
    Base,
    engine
)

# Register models for automatic creation on startup
from app.models.chat_message import ChatMessage
from app.models.conversation import Conversation
from app.models.quiz import Quiz, QuizQuestion
from app.models.summary import Summary
from app.models.syllabus_topic import SyllabusTopic
from app.models.extracted_document import ExtractedDocument

Base.metadata.create_all(bind=engine)

def run_migrations():
    from sqlalchemy import inspect
    inspector = inspect(engine)
    try:
        columns = [c["name"] for c in inspector.get_columns("syllabus_topics")]
        with engine.begin() as conn:
            if "priority" not in columns:
                conn.execute("ALTER TABLE syllabus_topics ADD COLUMN priority VARCHAR(50)")
            if "reasoning" not in columns:
                conn.execute("ALTER TABLE syllabus_topics ADD COLUMN reasoning TEXT")
    except Exception as e:
        print(f"Migration check bypassed: {str(e)}")

run_migrations()


from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

app.include_router(auth_router)
app.include_router(upload_router)
app.include_router(debug_router)
app.include_router(chat_router)
app.include_router(quiz_router)
app.include_router(summary_router)
app.include_router(syllabus_router)

@app.get("/")
def home():
    return {
        "message": "AI Smart Study Planner Backend Running"
    }