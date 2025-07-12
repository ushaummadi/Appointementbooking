from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
import uvicorn
from agent import CalendarAgent
from models import ChatRequest, ChatResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="TailorTalk Calendar Agent API",
    description="Conversational AI agent for Google Calendar appointment booking",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the calendar agent
calendar_agent = CalendarAgent()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "TailorTalk Calendar Agent API is running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test calendar service connection
        calendar_service = calendar_agent.calendar_service
        test_result = calendar_service.test_connection()
        
        return {
            "status": "healthy" if test_result else "degraded",
            "calendar_service": "connected" if test_result else "disconnected",
            "timestamp": calendar_agent.get_current_datetime()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": calendar_agent.get_current_datetime()
        }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint for conversational AI interaction
    """
    try:
        logger.info(f"Received message: {request.message} for conversation: {request.conversation_id}")
        
        # Process the message through the agent
        response = await calendar_agent.process_message(
            message=request.message,
            conversation_id=request.conversation_id
        )
        
        logger.info(f"Agent response: {response.response}")
        
        return response
    
    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/conversations/{conversation_id}/history")
async def get_conversation_history(conversation_id: str):
    """Get conversation history for a specific conversation"""
    try:
        history = calendar_agent.get_conversation_history(conversation_id)
        return {"conversation_id": conversation_id, "history": history}
    except Exception as e:
        logger.error(f"Error retrieving conversation history: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving conversation history: {str(e)}"
        )

@app.delete("/conversations/{conversation_id}")
async def clear_conversation(conversation_id: str):
    """Clear conversation history for a specific conversation"""
    try:
        calendar_agent.clear_conversation(conversation_id)
        return {"message": f"Conversation {conversation_id} cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing conversation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing conversation: {str(e)}"
        )

@app.get("/conversations")
async def get_recent_conversations():
    """Get recent conversations"""
    try:
        conversations = calendar_agent.db_service.get_recent_conversations(limit=20)
        return {"conversations": conversations}
    except Exception as e:
        logger.error(f"Error getting conversations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get conversations")

@app.get("/calendar/events")
async def get_calendar_events(conversation_id: str = None):
    """Get calendar events"""
    try:
        events = calendar_agent.db_service.get_calendar_events(conversation_id=conversation_id)
        return {"events": events}
    except Exception as e:
        logger.error(f"Error getting calendar events: {e}")
        raise HTTPException(status_code=500, detail="Failed to get calendar events")

@app.get("/database/status")
async def get_database_status():
    """Get database connection status"""
    try:
        # Try to get recent conversations as a health check
        conversations = calendar_agent.db_service.get_recent_conversations(limit=1)
        return {
            "status": "connected",
            "tables_exist": True,
            "recent_conversations_count": len(conversations)
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "disconnected",
            "error": str(e),
            "tables_exist": False
        }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
