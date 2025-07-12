# TailorTalk - AI Calendar Assistant

## Overview

TailorTalk is a conversational AI calendar assistant that enables users to book appointments through natural language interactions. The system consists of a Streamlit frontend for user interaction and a FastAPI backend powered by Google's Gemini AI and integrated with Google Calendar API.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

The application follows a client-server architecture with the following components:

### Frontend (Streamlit)
- **Technology**: Streamlit web application
- **Purpose**: Provides a chat-based user interface for calendar interactions
- **Communication**: HTTP requests to FastAPI backend
- **State Management**: Session-based conversation tracking

### Backend (FastAPI)
- **Technology**: FastAPI with Python
- **Purpose**: Handles business logic, AI processing, and external service integrations
- **Architecture Pattern**: Agent-based conversational AI using LangGraph
- **API Design**: RESTful endpoints with JSON communication

## Key Components

### 1. Calendar Agent (`agent.py`)
- **Purpose**: Core conversational AI logic using LangGraph state machine
- **Key Features**:
  - Intent understanding and information extraction
  - Multi-step conversation flow management
  - Availability checking and booking confirmation
- **State Management**: Maintains conversation context and booking information

### 2. Google Calendar Service (`calendar_service.py`)
- **Authentication**: Service Account-based authentication
- **Capabilities**:
  - Calendar availability checking
  - Event creation and management
  - Calendar querying and manipulation
- **Integration**: Direct Google Calendar API integration

### 3. LLM Service (`llm_service.py`)
- **AI Provider**: Google Gemini (gemini-2.5-flash and gemini-2.5-pro models)
- **Capabilities**:
  - Natural language understanding
  - Structured JSON response generation
  - Intent classification and information extraction

### 4. Calendar Tools (`tools.py`)
- **Purpose**: Utility functions for calendar operations
- **Features**:
  - Time slot availability checking
  - Available slot discovery
  - Calendar event management

### 5. Database Service (`database.py`)
- **Purpose**: PostgreSQL database integration for persistent data storage
- **Features**:
  - Conversation history storage and retrieval
  - Calendar event tracking
  - User session management
  - Conversation state persistence
- **Models**: Conversations, Messages, Calendar Events, Conversation States

## Data Flow

1. **User Input**: User sends natural language message through Streamlit interface
2. **Request Processing**: Frontend sends HTTP POST to `/chat` endpoint
3. **Database Storage**: User message saved to PostgreSQL database
4. **Agent Processing**: LangGraph agent processes message through state machine:
   - Intent understanding
   - Information extraction
   - Availability checking
   - Response generation
5. **External Services**: Agent interacts with Google Calendar API as needed
6. **Database Persistence**: AI response, conversation state, and calendar events saved to database
7. **Response**: Structured response sent back to frontend with booking information

## External Dependencies

### Required Services
- **Google Calendar API**: For calendar management and availability
- **Google Gemini API**: For AI language processing
- **Service Account**: For Google Calendar authentication
- **PostgreSQL Database**: For persistent data storage

### Environment Variables
- `GOOGLE_SERVICE_ACCOUNT_JSON`: Service account credentials for Google Calendar
- `GEMINI_API_KEY`: API key for Google Gemini AI service
- `DATABASE_URL`: PostgreSQL connection string for data persistence

### Python Dependencies
- FastAPI for backend API
- Streamlit for frontend
- LangGraph for conversation flow management
- Google API clients for calendar integration
- Pydantic for data validation
- SQLAlchemy and PostgreSQL for database operations

## Deployment Strategy

### Development Setup
- **Frontend**: Streamlit development server
- **Backend**: FastAPI with uvicorn server on port 8000
- **Local Testing**: Both services run locally with direct HTTP communication

### Architecture Decisions

1. **Microservices Approach**: Separate frontend and backend for scalability and maintainability
2. **State Machine Pattern**: LangGraph for complex conversation flow management
3. **Service Account Authentication**: Eliminates need for user OAuth flow
4. **JSON Communication**: Structured data exchange between services
5. **Database-backed Conversations**: Persistent conversation storage with PostgreSQL
6. **Session-based Conversations**: Maintains context across multiple interactions

### Key Design Choices

- **Agent-Based AI**: Uses LangGraph for sophisticated conversation management
- **Google Ecosystem**: Leverages Google Calendar and Gemini for comprehensive functionality
- **Stateful Conversations**: Maintains conversation context for multi-turn interactions
- **Persistent Data Storage**: PostgreSQL database for conversation history and calendar events
- **Error Handling**: Comprehensive error handling for external service failures
- **Health Monitoring**: Health check endpoints for service monitoring

## Recent Changes (July 12, 2025)

✓ **Added PostgreSQL Database Integration**
- Created database models for conversations, messages, calendar events, and conversation states
- Implemented DatabaseService with full CRUD operations
- Updated CalendarAgent to save/retrieve conversation data from database
- Added new API endpoints: `/conversations`, `/calendar/events`, `/database/status`
- Enabled persistent conversation history across sessions

✓ **Enhanced Data Persistence**
- All user and AI messages now stored in database
- Calendar events tracked with conversation context
- Conversation state maintained for complex booking flows
- Database gracefully handles offline scenarios

The system is designed for easy deployment and scaling, with clear separation of concerns between UI, business logic, external service integrations, and data persistence.