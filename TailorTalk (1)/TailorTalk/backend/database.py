import os
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    logger.warning("DATABASE_URL environment variable not found, database features will be disabled")
    DATABASE_URL = None

if DATABASE_URL:
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    engine = None
    SessionLocal = None

Base = declarative_base()

class Conversation(Base):
    """Model for storing conversation data"""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = Column(String, index=True)  # For future multi-user support

class Message(Base):
    """Model for storing individual messages"""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String, index=True, nullable=False)
    role = Column(String, nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    message_metadata = Column(JSON)  # For storing additional message data

class CalendarEvent(Base):
    """Model for storing calendar event data"""
    __tablename__ = "calendar_events"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String, unique=True, index=True)  # Google Calendar event ID
    conversation_id = Column(String, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    attendees = Column(JSON)  # List of attendee emails
    status = Column(String, default="confirmed")  # confirmed, cancelled, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ConversationState(Base):
    """Model for storing conversation state and context"""
    __tablename__ = "conversation_states"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String, unique=True, index=True, nullable=False)
    current_intent = Column(String)
    extracted_info = Column(JSON)
    pending_booking = Column(JSON)
    last_activity = Column(DateTime, default=datetime.utcnow)

def create_tables():
    """Create all tables"""
    if engine:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    else:
        logger.warning("Database not available, skipping table creation")

@contextmanager
def get_db_session():
    """Get database session with automatic cleanup"""
    if not SessionLocal:
        logger.warning("Database not available")
        yield None
        return
        
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()

class DatabaseService:
    """Service for database operations"""
    
    def __init__(self):
        # Create tables if they don't exist
        create_tables()
    
    def save_message(self, conversation_id: str, role: str, content: str, msg_metadata: Dict[str, Any] = None) -> None:
        """Save a message to the database"""
        with get_db_session() as session:
            if not session:
                return
                
            message = Message(
                conversation_id=conversation_id,
                role=role,
                content=content,
                message_metadata=msg_metadata or {}
            )
            session.add(message)
            
            # Update or create conversation record
            conversation = session.query(Conversation).filter(
                Conversation.conversation_id == conversation_id
            ).first()
            
            if not conversation:
                conversation = Conversation(conversation_id=conversation_id)
                session.add(conversation)
            else:
                conversation.updated_at = datetime.utcnow()
    
    def get_conversation_history(self, conversation_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get conversation history"""
        with get_db_session() as session:
            if not session:
                return []
                
            messages = session.query(Message).filter(
                Message.conversation_id == conversation_id
            ).order_by(Message.timestamp.desc()).limit(limit).all()
            
            return [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "metadata": msg.message_metadata or {}
                }
                for msg in reversed(messages)
            ]
    
    def save_calendar_event(self, event_data: Dict[str, Any]) -> None:
        """Save calendar event to database"""
        with get_db_session() as session:
            if not session:
                return
                
            event = CalendarEvent(
                event_id=event_data.get('event_id'),
                conversation_id=event_data.get('conversation_id'),
                title=event_data.get('title'),
                description=event_data.get('description'),
                start_time=datetime.fromisoformat(event_data.get('start_time').replace('Z', '+00:00')),
                end_time=datetime.fromisoformat(event_data.get('end_time').replace('Z', '+00:00')),
                attendees=event_data.get('attendees', []),
                status=event_data.get('status', 'confirmed')
            )
            session.add(event)
    
    def get_calendar_events(self, conversation_id: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get calendar events"""
        with get_db_session() as session:
            if not session:
                return []
                
            query = session.query(CalendarEvent)
            
            if conversation_id:
                query = query.filter(CalendarEvent.conversation_id == conversation_id)
            
            events = query.order_by(CalendarEvent.start_time.desc()).limit(limit).all()
            
            return [
                {
                    "id": event.id,
                    "event_id": event.event_id,
                    "conversation_id": event.conversation_id,
                    "title": event.title,
                    "description": event.description,
                    "start_time": event.start_time.isoformat(),
                    "end_time": event.end_time.isoformat(),
                    "attendees": event.attendees or [],
                    "status": event.status,
                    "created_at": event.created_at.isoformat()
                }
                for event in events
            ]
    
    def save_conversation_state(self, conversation_id: str, intent: str = None, 
                              extracted_info: Dict[str, Any] = None, 
                              pending_booking: Dict[str, Any] = None) -> None:
        """Save conversation state"""
        with get_db_session() as session:
            if not session:
                return
                
            state = session.query(ConversationState).filter(
                ConversationState.conversation_id == conversation_id
            ).first()
            
            if state:
                if intent:
                    state.current_intent = intent
                if extracted_info:
                    state.extracted_info = extracted_info
                if pending_booking:
                    state.pending_booking = pending_booking
                state.last_activity = datetime.utcnow()
            else:
                state = ConversationState(
                    conversation_id=conversation_id,
                    current_intent=intent,
                    extracted_info=extracted_info or {},
                    pending_booking=pending_booking or {}
                )
                session.add(state)
    
    def get_conversation_state(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation state"""
        with get_db_session() as session:
            if not session:
                return None
                
            state = session.query(ConversationState).filter(
                ConversationState.conversation_id == conversation_id
            ).first()
            
            if state:
                return {
                    "conversation_id": state.conversation_id,
                    "current_intent": state.current_intent,
                    "extracted_info": state.extracted_info or {},
                    "pending_booking": state.pending_booking or {},
                    "last_activity": state.last_activity.isoformat()
                }
            return None
    
    def clear_conversation(self, conversation_id: str) -> None:
        """Clear conversation data"""
        with get_db_session() as session:
            if not session:
                return
                
            # Delete messages
            session.query(Message).filter(
                Message.conversation_id == conversation_id
            ).delete()
            
            # Delete conversation state
            session.query(ConversationState).filter(
                ConversationState.conversation_id == conversation_id
            ).delete()
            
            # Update conversation record
            conversation = session.query(Conversation).filter(
                Conversation.conversation_id == conversation_id
            ).first()
            if conversation:
                conversation.updated_at = datetime.utcnow()
    
    def get_recent_conversations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversations"""
        with get_db_session() as session:
            if not session:
                return []
                
            conversations = session.query(Conversation).order_by(
                Conversation.updated_at.desc()
            ).limit(limit).all()
            
            return [
                {
                    "conversation_id": conv.conversation_id,
                    "created_at": conv.created_at.isoformat(),
                    "updated_at": conv.updated_at.isoformat(),
                    "user_id": conv.user_id
                }
                for conv in conversations
            ]