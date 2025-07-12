import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from pydantic import BaseModel

from calendar_service import GoogleCalendarService
from llm_service import LLMService
from tools import CalendarTools
from models import ChatResponse, ConversationState, BookingInfo, TimeSlot
from database import DatabaseService

logger = logging.getLogger(__name__)

class AgentState(BaseModel):
    """State model for the LangGraph agent"""
    messages: List[BaseMessage] = []
    conversation_id: str = ""
    user_intent: str = ""
    extracted_info: Dict[str, Any] = {}
    suggested_times: List[Dict[str, Any]] = []
    booking_confirmed: bool = False
    booking_info: Optional[Dict[str, Any]] = None
    needs_clarification: bool = False
    clarification_question: str = ""

class CalendarAgent:
    """Main conversational AI agent for calendar booking"""
    
    def __init__(self):
        self.calendar_service = GoogleCalendarService()
        self.llm_service = LLMService()
        self.tools = CalendarTools(self.calendar_service)
        self.db_service = DatabaseService()
        self.conversations: Dict[str, ConversationState] = {}
        
        # Build the agent graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state graph for conversation flow"""
        
        # Define the graph structure
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("understand_intent", self._understand_intent)
        workflow.add_node("extract_information", self._extract_information)
        workflow.add_node("check_availability", self._check_availability)
        workflow.add_node("confirm_booking", self._confirm_booking)
        workflow.add_node("ask_clarification", self._ask_clarification)
        workflow.add_node("generate_response", self._generate_response)
        
        # Set entry point
        workflow.set_entry_point("understand_intent")
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "understand_intent",
            self._route_after_intent,
            {
                "extract_info": "extract_information",
                "clarify": "ask_clarification",
                "general": "generate_response"
            }
        )
        
        workflow.add_conditional_edges(
            "extract_information",
            self._route_after_extraction,
            {
                "check_availability": "check_availability",
                "clarify": "ask_clarification",
                "complete": "generate_response"
            }
        )
        
        workflow.add_conditional_edges(
            "check_availability",
            self._route_after_availability,
            {
                "confirm": "confirm_booking",
                "suggest": "generate_response",
                "clarify": "ask_clarification"
            }
        )
        
        workflow.add_edge("ask_clarification", "generate_response")
        workflow.add_edge("confirm_booking", "generate_response")
        workflow.add_edge("generate_response", END)
        
        return workflow.compile()
    
    async def process_message(self, message: str, conversation_id: str) -> ChatResponse:
        """Process a user message through the agent"""
        try:
            # Save user message to database
            self.db_service.save_message(conversation_id, "user", message)
            
            # Get or create conversation state
            if conversation_id not in self.conversations:
                self.conversations[conversation_id] = ConversationState(
                    conversation_id=conversation_id
                )
            
            conversation = self.conversations[conversation_id]
            
            # Create initial agent state
            agent_state = AgentState(
                messages=[HumanMessage(content=message)],
                conversation_id=conversation_id
            )
            
            # Run the agent graph
            result = await self.graph.ainvoke(agent_state)
            
            # Get response text
            ai_response = result.get("response", "I'm sorry, I couldn't process that request.")
            
            # Save AI response to database
            self.db_service.save_message(conversation_id, "assistant", ai_response)
            
            # Update conversation history
            conversation.messages.append({
                "role": "user",
                "content": message,
                "timestamp": datetime.now().isoformat()
            })
            
            conversation.messages.append({
                "role": "assistant",
                "content": ai_response,
                "timestamp": datetime.now().isoformat()
            })
            
            conversation.updated_at = datetime.now()
            
            # Save conversation state if needed
            if result.get("user_intent") or result.get("extracted_info"):
                self.db_service.save_conversation_state(
                    conversation_id,
                    intent=result.get("user_intent"),
                    extracted_info=result.get("extracted_info"),
                    pending_booking=result.get("booking_info")
                )
            
            # Save calendar event if booking was confirmed
            if result.get("booking_confirmed") and result.get("booking_info"):
                event_data = result["booking_info"].copy()
                event_data["conversation_id"] = conversation_id
                # Ensure datetime strings are properly formatted
                if "start_time" in event_data and "date" in event_data:
                    start_datetime = f"{event_data['date']}T{event_data['start_time']}:00"
                    end_datetime = f"{event_data['date']}T{event_data.get('end_time', '00:00')}:00"
                    event_data["start_time"] = start_datetime
                    event_data["end_time"] = end_datetime
                self.db_service.save_calendar_event(event_data)
            
            # Build response
            response = ChatResponse(
                response=ai_response,
                conversation_id=conversation_id,
                timestamp=datetime.now().isoformat(),
                success=True
            )
            
            # Add booking info if available
            if result.get("booking_info"):
                response.booking_info = BookingInfo(**result["booking_info"])
            
            # Add suggested times if available
            if result.get("suggested_times"):
                response.suggested_times = [
                    TimeSlot(**slot) for slot in result["suggested_times"]
                ]
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return ChatResponse(
                response=f"I encountered an error: {str(e)}. Please try again.",
                conversation_id=conversation_id,
                timestamp=datetime.now().isoformat(),
                success=False
            )
    
    def _understand_intent(self, state: AgentState) -> Dict[str, Any]:
        """Understand user intent from the message"""
        try:
            last_message = state.messages[-1].content
            
            intent_prompt = f"""
            Analyze the following user message and determine their intent. 
            Possible intents: book_appointment, check_availability, modify_appointment, cancel_appointment, general_query
            
            User message: "{last_message}"
            
            Respond with JSON in this format:
            {{
                "intent": "intent_name",
                "confidence": 0.95,
                "reasoning": "brief explanation"
            }}
            """
            
            response = self.llm_service.get_structured_response(intent_prompt)
            intent_data = json.loads(response)
            
            return {
                **state.dict(),
                "user_intent": intent_data.get("intent", "general_query")
            }
            
        except Exception as e:
            logger.error(f"Error understanding intent: {e}")
            return {
                **state.dict(),
                "user_intent": "general_query"
            }
    
    def _extract_information(self, state: AgentState) -> Dict[str, Any]:
        """Extract booking information from user message"""
        try:
            last_message = state.messages[-1].content
            
            extraction_prompt = f"""
            Extract appointment booking information from this message: "{last_message}"
            
            Current date and time: {self.get_current_datetime()}
            
            Extract the following information if available:
            - title: appointment title/purpose
            - date: preferred date (convert relative dates like "tomorrow" to actual dates)
            - start_time: preferred start time
            - duration: appointment duration in minutes
            - attendees: other people to invite
            - description: additional details
            
            Respond with JSON format. Use null for missing information.
            """
            
            response = self.llm_service.get_structured_response(extraction_prompt)
            extracted_info = json.loads(response)
            
            return {
                **state.dict(),
                "extracted_info": extracted_info
            }
            
        except Exception as e:
            logger.error(f"Error extracting information: {e}")
            return {
                **state.dict(),
                "extracted_info": {}
            }
    
    def _check_availability(self, state: AgentState) -> Dict[str, Any]:
        """Check calendar availability and suggest times"""
        try:
            extracted_info = state.extracted_info
            
            # Use tools to check availability
            if extracted_info.get("date") and extracted_info.get("start_time"):
                # Check specific time
                is_available = self.tools.check_specific_time_availability(
                    date=extracted_info["date"],
                    start_time=extracted_info["start_time"],
                    duration=extracted_info.get("duration", 60)
                )
                
                if is_available:
                    return {
                        **state.dict(),
                        "booking_confirmed": True
                    }
            
            # Find available slots
            suggested_times = self.tools.find_available_slots(
                start_date=extracted_info.get("date", self.get_current_date()),
                duration=extracted_info.get("duration", 60),
                num_suggestions=3
            )
            
            return {
                **state.dict(),
                "suggested_times": suggested_times
            }
            
        except Exception as e:
            logger.error(f"Error checking availability: {e}")
            return {
                **state.dict(),
                "suggested_times": []
            }
    
    def _confirm_booking(self, state: AgentState) -> Dict[str, Any]:
        """Confirm and create the booking"""
        try:
            extracted_info = state.extracted_info
            
            # Create the event
            booking_result = self.tools.create_event(
                title=extracted_info.get("title", "Appointment"),
                description=extracted_info.get("description"),
                date=extracted_info["date"],
                start_time=extracted_info["start_time"],
                duration=extracted_info.get("duration", 60),
                attendees=extracted_info.get("attendees", [])
            )
            
            return {
                **state.dict(),
                "booking_info": booking_result,
                "booking_confirmed": True
            }
            
        except Exception as e:
            logger.error(f"Error confirming booking: {e}")
            return {
                **state.dict(),
                "booking_confirmed": False
            }
    
    def _ask_clarification(self, state: AgentState) -> Dict[str, Any]:
        """Generate clarification questions"""
        extracted_info = state.extracted_info
        missing_info = []
        
        if not extracted_info.get("title"):
            missing_info.append("the purpose of the appointment")
        if not extracted_info.get("date"):
            missing_info.append("the preferred date")
        if not extracted_info.get("start_time"):
            missing_info.append("the preferred time")
        
        if missing_info:
            question = f"I need more information to book your appointment. Could you please provide {', '.join(missing_info)}?"
        else:
            question = "Could you please provide more details about your appointment?"
        
        return {
            **state.dict(),
            "needs_clarification": True,
            "clarification_question": question
        }
    
    def _generate_response(self, state: AgentState) -> Dict[str, Any]:
        """Generate the final response"""
        try:
            if state.needs_clarification:
                response = state.clarification_question
            elif state.booking_confirmed and state.booking_info:
                booking_info = state.booking_info
                response = f"Great! I've successfully booked your appointment '{booking_info['title']}' for {booking_info['date']} at {booking_info['start_time']}."
            elif state.suggested_times:
                response = "I found some available time slots for you. Please let me know which one works best:"
                for i, slot in enumerate(state.suggested_times, 1):
                    response += f"\n{i}. {slot['date']} at {slot['start_time']} - {slot['end_time']}"
            else:
                # General response using LLM
                last_message = state.messages[-1].content
                prompt = f"""
                User message: "{last_message}"
                Context: This is a calendar booking assistant.
                
                Provide a helpful response. If the user is asking about booking appointments, 
                guide them on what information you need.
                """
                response = self.llm_service.get_response(prompt)
            
            return {
                **state.dict(),
                "response": response
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                **state.dict(),
                "response": "I apologize, but I encountered an error. Please try again."
            }
    
    def _route_after_intent(self, state: AgentState) -> str:
        """Route after intent understanding"""
        intent = state.user_intent
        
        if intent in ["book_appointment", "check_availability"]:
            return "extract_info"
        elif intent == "general_query":
            return "general"
        else:
            return "clarify"
    
    def _route_after_extraction(self, state: AgentState) -> str:
        """Route after information extraction"""
        extracted_info = state.extracted_info
        
        # Check if we have minimum required information
        if extracted_info.get("title") and extracted_info.get("date"):
            return "check_availability"
        else:
            return "clarify"
    
    def _route_after_availability(self, state: AgentState) -> str:
        """Route after availability check"""
        if state.booking_confirmed:
            return "confirm"
        elif state.suggested_times:
            return "suggest"
        else:
            return "clarify"
    
    def get_current_datetime(self) -> str:
        """Get current date and time as string"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def get_current_date(self) -> str:
        """Get current date as string"""
        return datetime.now().strftime("%Y-%m-%d")
    
    def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get conversation history"""
        # Try to get from database first
        db_history = self.db_service.get_conversation_history(conversation_id)
        if db_history:
            return db_history
        
        # Fallback to in-memory storage
        if conversation_id in self.conversations:
            return self.conversations[conversation_id].messages
        return []
    
    def clear_conversation(self, conversation_id: str):
        """Clear conversation history"""
        # Clear from database
        self.db_service.clear_conversation(conversation_id)
        
        # Clear from in-memory storage
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
