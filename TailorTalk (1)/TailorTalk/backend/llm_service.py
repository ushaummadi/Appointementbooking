import os
import json
import logging
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

class LLMService:
    """Service for LLM interactions using Gemini"""
    
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.5-flash"
        
    def get_response(self, prompt: str) -> str:
        """Get a simple text response from the LLM"""
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            
            return response.text or "I apologize, but I couldn't generate a response."
            
        except Exception as e:
            logger.error(f"Error getting LLM response: {e}")
            return "I encountered an error while processing your request."
    
    def get_structured_response(self, prompt: str) -> str:
        """Get a structured JSON response from the LLM"""
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-pro",
                contents=[
                    types.Content(role="user", parts=[types.Part(text=prompt)])
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )
            
            return response.text or "{}"
            
        except Exception as e:
            logger.error(f"Error getting structured LLM response: {e}")
            return "{}"
    
    def extract_intent(self, message: str) -> dict:
        """Extract user intent from message"""
        prompt = f"""
        Analyze this user message and extract the intent: "{message}"
        
        Possible intents:
        - book_appointment: User wants to schedule a new appointment
        - check_availability: User wants to check when they're available
        - modify_appointment: User wants to change an existing appointment
        - cancel_appointment: User wants to cancel an appointment
        - general_query: General questions or conversation
        
        Respond with JSON:
        {{
            "intent": "intent_name",
            "confidence": 0.95,
            "reasoning": "brief explanation"
        }}
        """
        
        try:
            response_text = self.get_structured_response(prompt)
            return json.loads(response_text)
        except:
            return {"intent": "general_query", "confidence": 0.5, "reasoning": "Failed to parse intent"}
    
    def extract_booking_info(self, message: str, current_datetime: str) -> dict:
        """Extract booking information from user message"""
        prompt = f"""
        Extract appointment booking information from this user message: "{message}"
        
        Current date and time: {current_datetime}
        
        Please extract:
        - title: What is the appointment for? (meeting title/purpose)
        - date: What date? Convert relative dates like "tomorrow", "next week" to YYYY-MM-DD format
        - start_time: What time should it start? (HH:MM format in 24-hour)
        - duration: How long should it be? (in minutes, default 60)
        - attendees: Who else should be invited? (email addresses)
        - description: Any additional details?
        
        Important rules:
        - If today is mentioned and it's after business hours, assume tomorrow
        - If no specific time is given but "morning" is mentioned, use 09:00
        - If no specific time is given but "afternoon" is mentioned, use 14:00
        - If no specific time is given but "evening" is mentioned, use 18:00
        - Default duration is 60 minutes if not specified
        
        Respond with JSON format. Use null for missing information:
        {{
            "title": "extracted title or null",
            "date": "YYYY-MM-DD or null",
            "start_time": "HH:MM or null",
            "duration": 60,
            "attendees": ["email1", "email2"] or null,
            "description": "additional details or null"
        }}
        """
        
        try:
            response_text = self.get_structured_response(prompt)
            return json.loads(response_text)
        except:
            return {}
    
    def generate_clarification_question(self, extracted_info: dict) -> str:
        """Generate a clarification question based on missing information"""
        missing_fields = []
        
        if not extracted_info.get("title"):
            missing_fields.append("the purpose or title of your appointment")
        if not extracted_info.get("date"):
            missing_fields.append("the date you'd prefer")
        if not extracted_info.get("start_time"):
            missing_fields.append("what time you'd like to meet")
        
        if not missing_fields:
            return "Could you provide more details about your appointment?"
        
        if len(missing_fields) == 1:
            return f"I need to know {missing_fields[0]} to book your appointment."
        elif len(missing_fields) == 2:
            return f"I need to know {missing_fields[0]} and {missing_fields[1]} to book your appointment."
        else:
            return f"I need to know {', '.join(missing_fields[:-1])}, and {missing_fields[-1]} to book your appointment."
    
    def generate_booking_confirmation(self, booking_info: dict) -> str:
        """Generate a booking confirmation message"""
        title = booking_info.get("title", "your appointment")
        date = booking_info.get("date", "")
        start_time = booking_info.get("start_time", "")
        end_time = booking_info.get("end_time", "")
        
        message = f"Perfect! I've successfully booked '{title}' for {date} from {start_time} to {end_time}."
        
        if booking_info.get("attendees"):
            attendees = booking_info["attendees"]
            if len(attendees) == 1:
                message += f" I've also sent an invitation to {attendees[0]}."
            else:
                message += f" I've also sent invitations to {', '.join(attendees)}."
        
        message += " You should receive a calendar notification shortly."
        
        return message
    
    def generate_availability_response(self, available_slots: list) -> str:
        """Generate a response showing available time slots"""
        if not available_slots:
            return "I couldn't find any available slots in the timeframe you requested. Would you like me to check a different date range?"
        
        message = "I found some available time slots for you:\n\n"
        
        for i, slot in enumerate(available_slots, 1):
            date = slot.get("date", "")
            start_time = slot.get("start_time", "")
            end_time = slot.get("end_time", "")
            message += f"{i}. {date} from {start_time} to {end_time}\n"
        
        message += "\nWhich slot would you prefer? You can just tell me the number or describe your preference."
        
        return message
