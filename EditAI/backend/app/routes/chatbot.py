from fastapi import APIRouter
import os
from app.models.schemas import ChatbotCommandRequest, ChatbotCommandResponse
from app.services.command_parser import CommandParser
from app.services.timeline_manager import TimelineManager
from app.services.ai_adapter import AIModelAdapter

router = APIRouter(prefix="/api/chatbot", tags=["Chatbot"])
timeline_manager = TimelineManager()

@router.post("/command", response_model=ChatbotCommandResponse)
@router.post("/message", response_model=ChatbotCommandResponse)
async def process_chat_command(request: ChatbotCommandRequest):
    """
    Interprets natural-language commands and executes the corresponding editing action.
    """
    response = CommandParser.interpret_and_execute(request, timeline_manager)
    return response

@router.get("/providers")
async def get_llm_providers():
    """Returns available LLM engines and their configuration status."""
    ollama_status = AIModelAdapter.get_ollama_status()
    gemini_key = bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))
    openai_key = bool(os.environ.get("OPENAI_API_KEY") or os.environ.get("GROQ_API_KEY"))

    active = "Semantic NLP (Offline)"
    if ollama_status["online"] and ollama_status["active_model"]:
        active = f"Local Qwen 2.5 ({ollama_status['active_model']})"
    elif gemini_key:
        active = "Google Gemini"
    elif openai_key:
        active = "OpenAI / Groq"

    return {
        "gemini_ready": gemini_key,
        "openai_ready": openai_key,
        "ollama_ready": ollama_status["online"],
        "ollama_models": ollama_status["installed_models"],
        "active_model": ollama_status["active_model"],
        "ollama_base_url": ollama_status["base_url"],
        "active_engine": active,
        "setup_instructions": ollama_status["setup_instructions"]
    }

@router.get("/suggestions")
async def get_command_suggestions():
    """Returns sample test and workflow commands for the chatbot UI."""
    return {
        "workflow_demo_commands": [
            "Select the clip from 00:10 to 00:25.",
            "Split at 00:18.",
            "Delete the selected segment.",
            "Explain why this section was selected or removed.",
            "Find repeated statements across these videos.",
            "Arrange these clips into a logical story.",
            "Create a shorter version while preserving the main message.",
            "Export the edited video."
        ],
        "all_supported_commands": [
            "Explain why this section was selected or removed.",
            "Find repeated statements across these videos.",
            "Arrange these clips into a logical story.",
            "Show me the important moments.",
            "Create a shorter version while preserving the main message.",
            "Select the first 10 seconds.",
            "Select the clip from 00:15 to 00:30.",
            "Split the clip at 00:20.",
            "Cut the selected section.",
            "Delete the selected segment.",
            "Remove the first 5 seconds.",
            "Trim the video from 00:10 to 01:20.",
            "Undo the last edit.",
            "Redo the last edit.",
            "Show all detected scenes.",
            "Play the selected clip.",
            "Export the edited video."
        ]
    }
