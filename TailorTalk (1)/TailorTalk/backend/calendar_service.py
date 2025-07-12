import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

class GoogleCalendarService:
    """Service for Google Calendar API integration using Service Account"""
    
    def __init__(self):
        self.calendar_id = 'primary'  # Use primary calendar
        self.service = self._authenticate()
    
    def _authenticate(self):
        """Authenticate using Service Account credentials"""
        try:
            # Get service account credentials from environment variable
            service_account_info = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
            
            if not service_account_info:
                raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON environment variable not found")
            
            # Clean up the JSON string - remove extra whitespace and newlines
            service_account_info = service_account_info.strip()
            
            # Fix common JSON formatting issues
            if not service_account_info.startswith('{') and service_account_info.startswith('"type"'):
                # Missing opening brace - add it
                service_account_info = '{' + service_account_info
                logger.info("Added missing opening brace to JSON")
            
            if not service_account_info.endswith('}') and service_account_info.endswith('"'):
                # Missing closing brace - add it
                service_account_info = service_account_info + '}'
                logger.info("Added missing closing brace to JSON")
            
            # Parse the JSON credentials
            if isinstance(service_account_info, str):
                try:
                    credentials_info = json.loads(service_account_info)
                    logger.info("Successfully parsed service account JSON")
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parsing error at position {e.pos}: {e.msg}")
                    logger.error(f"Problematic part: '{service_account_info[max(0, e.pos-10):e.pos+10]}'")
                    raise ValueError(f"Invalid JSON format in GOOGLE_SERVICE_ACCOUNT_JSON: {e.msg}")
            else:
                credentials_info = service_account_info
            
            # Create credentials
            credentials = service_account.Credentials.from_service_account_info(
                credentials_info,
                scopes=['https://www.googleapis.com/auth/calendar']
            )
            
            # Build the service
            service = build('calendar', 'v3', credentials=credentials)
            logger.info("Successfully authenticated with Google Calendar API")
            
            return service
            
        except Exception as e:
            logger.error(f"Failed to authenticate with Google Calendar API: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test the connection to Google Calendar API"""
        try:
            # Try to get calendar list to test connection
            calendar_list = self.service.calendarList().list().execute()
            logger.info("Google Calendar API connection test successful")
            return True
        except Exception as e:
            logger.error(f"Google Calendar API connection test failed: {e}")
            return False
    
    def get_events(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Get events within a time range"""
        try:
            # Convert datetime to RFC3339 format
            start_time_rfc = start_time.isoformat() + 'Z'
            end_time_rfc = end_time.isoformat() + 'Z'
            
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=start_time_rfc,
                timeMax=end_time_rfc,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            formatted_events = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                
                formatted_events.append({
                    'id': event['id'],
                    'title': event.get('summary', 'No Title'),
                    'start': start,
                    'end': end,
                    'description': event.get('description', ''),
                    'attendees': [attendee.get('email') for attendee in event.get('attendees', [])]
                })
            
            logger.info(f"Retrieved {len(formatted_events)} events")
            return formatted_events
            
        except HttpError as e:
            logger.error(f"HTTP error getting events: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting events: {e}")
            raise
    
    def create_event(self, title: str, start_time: datetime, end_time: datetime, 
                    description: str = None, attendees: List[str] = None) -> Dict[str, Any]:
        """Create a new calendar event"""
        try:
            event_body = {
                'summary': title,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'UTC',
                },
            }
            
            if description:
                event_body['description'] = description
            
            if attendees:
                event_body['attendees'] = [{'email': email} for email in attendees]
            
            # Create the event
            event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event_body
            ).execute()
            
            logger.info(f"Successfully created event: {event['id']}")
            
            return {
                'id': event['id'],
                'title': event.get('summary'),
                'start': event['start']['dateTime'],
                'end': event['end']['dateTime'],
                'description': event.get('description', ''),
                'html_link': event.get('htmlLink', ''),
                'attendees': attendees or []
            }
            
        except HttpError as e:
            logger.error(f"HTTP error creating event: {e}")
            raise
        except Exception as e:
            logger.error(f"Error creating event: {e}")
            raise
    
    def update_event(self, event_id: str, title: str = None, start_time: datetime = None, 
                    end_time: datetime = None, description: str = None) -> Dict[str, Any]:
        """Update an existing calendar event"""
        try:
            # First, get the existing event
            event = self.service.events().get(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            
            # Update fields if provided
            if title:
                event['summary'] = title
            if start_time:
                event['start']['dateTime'] = start_time.isoformat()
            if end_time:
                event['end']['dateTime'] = end_time.isoformat()
            if description:
                event['description'] = description
            
            # Update the event
            updated_event = self.service.events().update(
                calendarId=self.calendar_id,
                eventId=event_id,
                body=event
            ).execute()
            
            logger.info(f"Successfully updated event: {event_id}")
            return updated_event
            
        except HttpError as e:
            logger.error(f"HTTP error updating event: {e}")
            raise
        except Exception as e:
            logger.error(f"Error updating event: {e}")
            raise
    
    def delete_event(self, event_id: str) -> bool:
        """Delete a calendar event"""
        try:
            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            
            logger.info(f"Successfully deleted event: {event_id}")
            return True
            
        except HttpError as e:
            logger.error(f"HTTP error deleting event: {e}")
            return False
        except Exception as e:
            logger.error(f"Error deleting event: {e}")
            return False
    
    def check_availability(self, start_time: datetime, end_time: datetime) -> bool:
        """Check if a time slot is available (no conflicts)"""
        try:
            events = self.get_events(start_time, end_time)
            
            # Check for overlapping events
            for event in events:
                event_start = datetime.fromisoformat(event['start'].replace('Z', '+00:00'))
                event_end = datetime.fromisoformat(event['end'].replace('Z', '+00:00'))
                
                # Check for time overlap
                if (start_time < event_end and end_time > event_start):
                    logger.info(f"Time conflict found with event: {event['title']}")
                    return False
            
            logger.info(f"Time slot {start_time} - {end_time} is available")
            return True
            
        except Exception as e:
            logger.error(f"Error checking availability: {e}")
            return False
    
    def find_free_slots(self, start_date: datetime, end_date: datetime, 
                       duration_minutes: int = 60, num_slots: int = 5) -> List[Dict[str, Any]]:
        """Find available time slots within a date range"""
        try:
            free_slots = []
            current_time = start_date
            slot_duration = timedelta(minutes=duration_minutes)
            
            # Define business hours (9 AM to 5 PM)
            business_start = 9
            business_end = 17
            
            while current_time < end_date and len(free_slots) < num_slots:
                # Skip weekends
                if current_time.weekday() >= 5:
                    current_time += timedelta(days=1)
                    current_time = current_time.replace(hour=business_start, minute=0, second=0, microsecond=0)
                    continue
                
                # Skip non-business hours
                if current_time.hour < business_start:
                    current_time = current_time.replace(hour=business_start, minute=0, second=0, microsecond=0)
                elif current_time.hour >= business_end:
                    current_time += timedelta(days=1)
                    current_time = current_time.replace(hour=business_start, minute=0, second=0, microsecond=0)
                    continue
                
                slot_end = current_time + slot_duration
                
                # Check if this slot is available
                if self.check_availability(current_time, slot_end):
                    free_slots.append({
                        'date': current_time.strftime('%Y-%m-%d'),
                        'start_time': current_time.strftime('%H:%M'),
                        'end_time': slot_end.strftime('%H:%M'),
                        'start_datetime': current_time.isoformat(),
                        'end_datetime': slot_end.isoformat()
                    })
                
                # Move to next 30-minute slot
                current_time += timedelta(minutes=30)
            
            logger.info(f"Found {len(free_slots)} available slots")
            return free_slots
            
        except Exception as e:
            logger.error(f"Error finding free slots: {e}")
            return []
