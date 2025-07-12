import streamlit as st
import requests
import json
from datetime import datetime
import time

# Page configuration
st.set_page_config(
    page_title="TailorTalk - AI Calendar Assistant",
    page_icon="📅",
    layout="wide"
)

# Backend URL
BACKEND_URL = "http://0.0.0.0:8000"

def initialize_session_state():
    """Initialize session state variables"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = f"conv_{int(time.time())}"

def send_message_to_backend(message: str, conversation_id: str):
    """Send message to FastAPI backend and get response"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/chat",
            json={
                "message": message,
                "conversation_id": conversation_id
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "response": f"Error: Backend returned status {response.status_code}",
                "success": False
            }
    except requests.exceptions.ConnectionError:
        return {
            "response": "Error: Could not connect to backend. Please make sure the FastAPI server is running on port 8000.",
            "success": False
        }
    except requests.exceptions.Timeout:
        return {
            "response": "Error: Request timed out. Please try again.",
            "success": False
        }
    except Exception as e:
        return {
            "response": f"Error: {str(e)}",
            "success": False
        }

def main():
    """Main application function"""
    initialize_session_state()
    
    # Header
    st.title("📅 TailorTalk - AI Calendar Assistant")
    st.markdown("### Book appointments naturally with conversational AI")
    
    # Sidebar with information
    with st.sidebar:
        st.markdown("## How it works")
        st.markdown("""
        1. **Tell me what you need**: Describe your appointment in natural language
        2. **I'll check availability**: I'll look at your calendar and suggest times
        3. **Confirm booking**: Once you're happy with the time, I'll book it for you
        
        ### Example requests:
        - "I need a 1-hour meeting with John tomorrow afternoon"
        - "Book a doctor's appointment for next week"
        - "Schedule a team call for Friday at 2 PM"
        """)
        
        st.markdown("---")
        st.markdown("**Conversation ID:**")
        st.code(st.session_state.conversation_id)
        
        if st.button("Start New Conversation"):
            st.session_state.messages = []
            st.session_state.conversation_id = f"conv_{int(time.time())}"
            st.rerun()
    
    # Chat interface
    st.markdown("## Chat with your AI assistant")
    
    # Display chat messages
    chat_container = st.container()
    
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response_data = send_message_to_backend(prompt, st.session_state.conversation_id)
                
                if response_data.get("success", True):
                    ai_response = response_data.get("response", "I'm sorry, I couldn't process that request.")
                    
                    # Check if there's booking information to display
                    if "booking_info" in response_data:
                        booking_info = response_data["booking_info"]
                        st.success("✅ Appointment booked successfully!")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("**Event Details:**")
                            st.write(f"📝 **Title:** {booking_info.get('title', 'N/A')}")
                            st.write(f"📅 **Date:** {booking_info.get('date', 'N/A')}")
                            st.write(f"⏰ **Time:** {booking_info.get('start_time', 'N/A')} - {booking_info.get('end_time', 'N/A')}")
                        
                        with col2:
                            if booking_info.get('description'):
                                st.markdown("**Description:**")
                                st.write(booking_info['description'])
                            if booking_info.get('event_id'):
                                st.markdown("**Event ID:**")
                                st.code(booking_info['event_id'])
                    
                    # Check if there are suggested times to display
                    if "suggested_times" in response_data:
                        suggested_times = response_data["suggested_times"]
                        st.markdown("**Available time slots:**")
                        
                        for i, slot in enumerate(suggested_times, 1):
                            st.write(f"{i}. {slot['date']} at {slot['start_time']} - {slot['end_time']}")
                else:
                    ai_response = response_data.get("response", "I encountered an error. Please try again.")
                    st.error(ai_response)
                
                st.markdown(ai_response)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": ai_response})

if __name__ == "__main__":
    main()
