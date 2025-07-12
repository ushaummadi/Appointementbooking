import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from calendar_service import GoogleCalendarService

logger = logging.getLogger(__name__)

class CalendarTools:
    """Tools for calendar operations to be used by the LangGraph agent"""
    
    def __init__(self, calendar_service: GoogleCalendarService):
        self.calendar_service = calendar_service
    
    def check_specific_time_availability(self, date: str, start_time: str, duration: int = 60) -> bool:
        """
        Check if a specific time slot is available
        
        Args:
            date: Date in YYYY-MM-DD format
            start_time: Start time in HH:MM format
            duration: Duration in minutes
            
        Returns:
            bool: True if available, False if not
        """
        try:
            # Parse date and time
            start_datetime = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
            end_datetime = start_datetime + timedelta(minutes=duration)
            
            # Check availability
            is_available = self.calendar_service.check_availability(start_datetime, end_datetime)
            
            logger.info(f"Availability check for {date} {start_time}: {is_available}")
            return is_available
            
        except Exception as e:
            logger.error(f"Error checking specific time availability: {e}")
            return False
    
    def find_available_slots(self, start_date: str, duration: int = 60, 
                           num_suggestions: int = 3, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """
        Find available time slots
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            duration: Duration in minutes
            num_suggestions: Number of suggestions to return
            days_ahead: How many days ahead to search
            
        Returns:
            List of available time slots
        """
        try:
            # Parse start date
            start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
            
            # If start date is in the past, use today
            if start_datetime.date() < datetime.now().date():
                start_datetime = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
            
            # Search for slots up to days_ahead from start date
            end_search_date = start_datetime + timedelta(days=days_ahead)
            
            # Find free slots
            free_slots = self.calendar_service.find_free_slots(
                start_date=start_datetime,
                end_date=end_search_date,
                duration_minutes=duration,
                num_slots=num_suggestions
            )
            
            logger.info(f"Found {len(free_slots)} available slots")
            return free_slots
            
        except Exception as e:
            logger.error(f"Error finding available slots: {e}")
            return []
    
    def create_event(self, title: str, date: str, start_time: str, 
                    duration: int = 60, description: str = None, 
                    attendees: List[str] = None) -> Dict[str, Any]:
        """
        Create a calendar event
        
        Args:
            title: Event title
            date: Date in YYYY-MM-DD format
            start_time: Start time in HH:MM format
            duration: Duration in minutes
            description: Event description
            attendees: List of attendee emails
            
        Returns:
            Dictionary with event details
        """
        try:
            # Parse date and time
            start_datetime = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
            end_datetime = start_datetime + timedelta(minutes=duration)
            
            # Create the event
            event_result = self.calendar_service.create_event(
                title=title,
                start_time=start_datetime,
                end_time=end_datetime,
                description=description,
                attendees=attendees or []
            )
            
            # Format response
            booking_info = {
                'title': title,
                'description': description,
                'date': date,
                'start_time': start_time,
                'end_time': end_datetime.strftime('%H:%M'),
                'event_id': event_result['id'],
                'attendees': attendees or []
            }
            
            logger.info(f"Successfully created event: {event_result['id']}")
            return booking_info
            
        except Exception as e:
            logger.error(f"Error creating event: {e}")
            raise Exception(f"Failed to create appointment: {str(e)}")
    
    def update_event(self, event_id: str, title: str = None, 
                    date: str = None, start_time: str = None, 
                    duration: int = None, description: str = None) -> Dict[str, Any]:
        """
        Update an existing calendar event
        
        Args:
            event_id: Event ID to update
            title: New title (optional)
            date: New date in YYYY-MM-DD format (optional)
            start_time: New start time in HH:MM format (optional)
            duration: New duration in minutes (optional)
            description: New description (optional)
            
        Returns:
            Dictionary with updated event details
        """
        try:
            start_datetime = None
            end_datetime = None
            
            if date and start_time:
                start_datetime = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
                duration = duration or 60  # Default duration if not provided
                end_datetime = start_datetime + timedelta(minutes=duration)
            
            # Update the event
            updated_event = self.calendar_service.update_event(
                event_id=event_id,
                title=title,
                start_time=start_datetime,
                end_time=end_datetime,
                description=description
            )
            
            logger.info(f"Successfully updated event: {event_id}")
            return updated_event
            
        except Exception as e:
            logger.error(f"Error updating event: {e}")
            raise Exception(f"Failed to update appointment: {str(e)}")
    
    def delete_event(self, event_id: str) -> bool:
        """
        Delete a calendar event
        
        Args:
            event_id: Event ID to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            success = self.calendar_service.delete_event(event_id)
            
            if success:
                logger.info(f"Successfully deleted event: {event_id}")
            else:
                logger.error(f"Failed to delete event: {event_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting event: {e}")
            return False
    
    def get_upcoming_events(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """
        Get upcoming events
        
        Args:
            days_ahead: Number of days ahead to look
            
        Returns:
            List of upcoming events
        """
        try:
            start_time = datetime.now()
            end_time = start_time + timedelta(days=days_ahead)
            
            events = self.calendar_service.get_events(start_time, end_time)
            
            logger.info(f"Retrieved {len(events)} upcoming events")
            return events
            
        except Exception as e:
            logger.error(f"Error getting upcoming events: {e}")
            return []
    
    def parse_relative_date(self, date_string: str) -> str:
        """
        Parse relative date strings like 'tomorrow', 'next week', etc.
        
        Args:
            date_string: Relative date string
            
        Returns:
            Date in YYYY-MM-DD format
        """
        try:
            today = datetime.now().date()
            date_string = date_string.lower().strip()
            
            if date_string == "today":
                return today.strftime("%Y-%m-%d")
            elif date_string == "tomorrow":
                return (today + timedelta(days=1)).strftime("%Y-%m-%d")
            elif "next week" in date_string:
                days_to_add = 7 - today.weekday()  # Days until next Monday
                return (today + timedelta(days=days_to_add)).strftime("%Y-%m-%d")
            elif "next monday" in date_string:
                days_to_add = 7 - today.weekday() if today.weekday() != 0 else 7
                return (today + timedelta(days=days_to_add)).strftime("%Y-%m-%d")
            elif "next friday" in date_string:
                days_to_add = (4 - today.weekday()) % 7
                if days_to_add == 0:  # Today is Friday, get next Friday
                    days_to_add = 7
                return (today + timedelta(days=days_to_add)).strftime("%Y-%m-%d")
            else:
                # Try to parse as absolute date
                try:
                    parsed_date = datetime.strptime(date_string, "%Y-%m-%d").date()
                    return parsed_date.strftime("%Y-%m-%d")
                except:
                    # Default to tomorrow if can't parse
                    return (today + timedelta(days=1)).strftime("%Y-%m-%d")
                    
        except Exception as e:
            logger.error(f"Error parsing relative date: {e}")
            # Default to tomorrow
            return (datetime.now().date() + timedelta(days=1)).strftime("%Y-%m-%d")
