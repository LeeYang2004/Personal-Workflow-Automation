"""
This script retrieves upcoming Zoom meetings from a user's Google Calendar.
"""
import datetime
import os.path
import re
import datetime
from core.logger import logger
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from fastapi import APIRouter
from core.utils import get_credentials_path, get_token_path

router = APIRouter()

@router.get("/calendar-service")
def calendar_service():
    credential = auth_google_calendar()

    return fetch_calendar_events(credential)

def auth_google_calendar() -> Credentials:
    """
    Start the OAuth flow to retrieve credentials for accessing the Google Calendar API.
    
    - token.json stores the user's access and refresh tokens
    - It is created automatically when the authorization flow completes for the first time.
    """
    # Define credential variable
    # If modifying these scopes, delete the file token.json.
    SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

    credential = None

    if os.path.exists(get_token_path()):
        credential = Credentials.from_authorized_user_file(get_token_path(), SCOPES)

    # If there are no (valid) credentials available, let the user log in.
    if not credential or not credential.valid:
        if credential and credential.expired and credential.refresh_token:
            credential.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                get_credentials_path(),
                SCOPES
            )
            credential = flow.run_local_server(port=0)
      
        # Save the credentials for the next run
        with open(get_token_path(), "w") as token:
            token.write(credential.to_json())
    
    return credential

def fetch_calendar_events(credential) -> dict:
    """
    Fetch upcoming events from the user's Google Calendar and extract relevant information for Zoom meetings.
    
    - Only events that are Zoom meetings are processed.
    """
    # Initialize an empty list to store all event data
    CALENDAR_NEEDED = ["leey270604@gmail.com"]
    
    all_events_data = []
    page_token = None

    try:
        service = build("calendar", "v3", credentials=credential)

        # Call the Calendar API to list the user's calendars
        calendar_list_result = service.calendarList().list().execute()
        calendars = calendar_list_result.get("items", [])
        
        # Call the Calendar API
        now = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
        
        for calendar in calendars:
            calendar_id = calendar["id"]
                
            if calendar_id not in CALENDAR_NEEDED:
                continue
            
            while True:
                events_result = (
                    service.events().list(
                        calendarId=calendar_id,
                        timeMin=now,
                        singleEvents=True,
                        pageToken=page_token,
                    ).execute()
                )
                
                events = events_result.get("items", [])

                if not events:
                    logger.info("No upcoming events found.")
                    continue

                for event in events:
                
                    # Get only events that are zoom meetings by checking the description and location for zoom keywords
                    description = event.get("description", "")
                    location = event.get("location", "")
                    zoom_pattern = re.compile(r"(zoom\.us|meeting id|join zoom meeting|meeting chat link)", re.IGNORECASE)
                    is_zoom = bool(zoom_pattern.search(f"{description} {location}"))
                    
                    if not is_zoom:
                        continue
                
                    # Extract relevant information from the event
                    # Event title
                    event_title = event.get("summary", "Title Unavailable") 
                    
                    # Event ID
                    event_id = event.get("id", "Event ID Unavailable") 
                    
                    # Start time
                    start_datetime = event["start"].get("dateTime", event["start"].get("date"))
                    
                    # End time
                    end_datetime = event["end"].get("dateTime", event["end"].get("date"))
                    
                    # Meeting ID
                    meeting_id_pattern = re.search(r"meeting id:\s*([\d\s]+)", description, re.IGNORECASE)
                    meeting_id = meeting_id_pattern.group(1).strip() if meeting_id_pattern else None
                    
                    # Meeting Link
                    meeting_link_pattern = re.search(r"(https?://(?:[a-z0-9-]+\.)*zoom\.us/[^\s]+)", description, re.IGNORECASE)
                    meeting_link = meeting_link_pattern.group(1).strip() if meeting_link_pattern else None
                    
                    # Passcode
                    passcode_pattern = re.search(r"passcode[:\s]*([^\n\r<]+)", description, re.IGNORECASE)
                    passcode = passcode_pattern.group(1).strip() if passcode_pattern else None
                    
                    # Organizer Email
                    organizer = event.get("organizer", {})
                    organizer_email = organizer.get("email", "Email Unavailable") 
                    
                    # Attendees list
                    attendees = event.get("attendees", [])
                    if attendees:
                        attendee_list = [a.get("email", "Unknown") for a in attendees]
                    else:
                        attendee_list = []
                    
                    event_data = {
                        "event_title": event_title,
                        "event_id": event_id,
                        "meeting_id": meeting_id,
                        "start_timestamp": start_datetime,
                        "end_timestamp": end_datetime,
                        "meeting_link": meeting_link,
                        "passcode": passcode,
                        "organizer_email": organizer_email,
                        "attendees_email": attendee_list,
                    }

                    all_events_data.append(event_data)
                
                page_token = events_result.get("nextPageToken")

                if not page_token:
                    break
            
        return all_events_data

    except HttpError as error:
        logger.error(f"An error occurred: {error}")