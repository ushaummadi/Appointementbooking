# TailorTalk - AI Calendar Assistant

## Overview
TailorTalk is a conversational AI agent that assists users in booking appointments on Google Calendar through natural language interactions. The system uses advanced AI to understand user intent, check calendar availability, suggest time slots, and confirm bookings seamlessly through chat.

## 🚀 Live Demo
- **Streamlit Frontend**: [Your Deployment URL]
- **API Backend**: [Your Backend URL]

## ✨ Features
- **Natural Language Processing**: Book meetings with phrases like "schedule a meeting tomorrow at 2pm"
- **Google Calendar Integration**: Real calendar booking using Service Account authentication
- **Intelligent Conversation Flow**: Multi-turn conversations with context awareness
- **Smart Scheduling**: Automatic availability checking and time suggestions
- **Persistent Storage**: PostgreSQL database for conversation history and booking records

## 🛠️ Technical Stack
- **Backend**: Python with FastAPI
- **Agent Framework**: LangGraph for conversation flow management
- **Frontend**: Streamlit chat interface
- **AI Model**: Google Gemini for natural language understanding
- **Database**: PostgreSQL for data persistence
- **Calendar**: Google Calendar API with Service Account authentication

## 📋 Assignment Requirements Met
✅ Backend: Python with FastAPI  
✅ Agent Framework: LangGraph  
✅ Frontend: Streamlit chat interface  
✅ LLM Integration: Google Gemini API  
✅ Google Calendar: Service Account integration  
✅ Conversational AI: Full natural language booking capability  

## 🎯 How to Test
1. Visit the Streamlit URL above
2. Try natural language booking requests:
   - "Can you schedule a meeting with John tomorrow at 3pm?"
   - "Book a 1-hour call next Tuesday morning"
   - "Find me an available slot this week"
3. The system will check your calendar and either book the meeting or suggest alternatives

## 🏗️ Architecture
- **Microservices Design**: Separate frontend and backend services
- **State Management**: LangGraph for complex conversation flows
- **Database Integration**: Persistent conversation and booking storage
- **Error Handling**: Comprehensive error management and health monitoring

## 🔧 Local Development
```bash
# Backend
cd backend
python main.py

# Frontend  
streamlit run app.py
```

## 📞 Contact
Built for internship assignment - demonstrating full-stack AI development with real-world calendar integration.