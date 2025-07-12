from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    message: str = Field(..., description="User message")
    conversation_id: str = Field(..., description="Unique conversation identifier")

class BookingInfo(BaseModel):
    """Booking information model"""
    title: str
    description: Optional[str] = None
    date: str
    start_time: str
    end_time: str
    event_id: Optional[str] = None
    attendees: Optional[List[str]] = None

class TimeSlot(BaseModel):
    """Time slot model for availability"""
    date: str
    start_time: str
    end_time: str
    available: bool = True

class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    response: str = Field(..., description="Agent response message")
    success: bool = Field(default=True, description="Whether the request was successful")
    booking_info: Optional[BookingInfo] = Field(None, description="Booking information if appointment was created")
    suggested_times: Optional[List[TimeSlot]] = Field(None, description="Suggested available time slots")
    conversation_id: str = Field(..., description="Conversation identifier")
    timestamp: str = Field(..., description="Response timestamp")

class ConversationState(BaseModel):
    """Conversation state model"""
    conversation_id: str
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)
    pending_booking: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class CalendarEvent(BaseModel):
    """Calendar event model"""
    id: Optional[str] = None
    title: str
    description: Optional[str] = None
    start_datetime: datetime
    end_datetime: datetime
    attendees: Optional[List[str]] = None
    location: Optional[str] = None

class AvailabilityRequest(BaseModel):
    """Request model for checking availability"""
    start_date: str
    end_date: str
    duration_minutes: int = 60
    preferred_times: Optional[List[str]] = None  # e.g., ["morning", "afternoon", "evening"]
