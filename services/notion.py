"""
This module contains functions to interact with the Notion API and create/update pages in a Notion database.
"""
from core.logger import logger
import requests
from fastapi import APIRouter
from core.config import settings

router = APIRouter()

def upsert_notion_page(event_data):
    """
    Check if a page with the given event ID exists. 

    - If it does, update only the changed fields. 
    - If not, create a new page.
    """
    event_id = event_data["event_id"]
    existing_page = find_page_by_event_id(event_id)

    if existing_page:
        updated_fields = get_updated_fields(existing_page, event_data)

        if updated_fields:
            update_notion_page(existing_page["id"], updated_fields)
            logger.info("Updated existing Notion page (Event ID: %s)", event_id)

    else:
        create_notion_page(event_data)
        logger.info("Created new Notion page (Event ID: %s)", event_id)

def _error_response(response):
    """
    Helper function to log error responses from Notion API requests.
    """
    if response.status_code != 200:
        logger.error("Error:", response.text)

def _get_notion_headers() -> dict:
    """
    Helper function to construct the headers needed for Notion API requests.
    """
    headers = {
        "Authorization": f"Bearer {settings.notion_token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    return headers

def _get_notion_base_url() -> str:
    """
    Helper function to return the base URL for Notion API requests.
    """
    return "https://api.notion.com/v1"

def create_notion_page(event_data):
    """
    Create a new page in the Notion database with the provided event data.
    """
    url = f"{_get_notion_base_url()}/pages"
    headers = _get_notion_headers()

    # Construct the payload with the event data
    payload = {
        "parent": {"database_id": settings.notion_database_id},
        "properties": {
            "Event Title": {
                "title": [
                    {"text": {"content": event_data["event_title"]}}
                ]
            },
            "Event ID": {
                "rich_text": [
                    {"text": {"content": event_data["event_id"]}}
                ]
            },
            "Meeting ID": {
                "rich_text": [
                    {"text": {"content": str(event_data.get("meeting_id") or "")}}
                ]
            },
            "Start Timestamp": {
                "date": {"start": event_data["start_timestamp"]}
            },
            "End Timestamp": {
                "date": {"start": event_data["end_timestamp"]}
            },
            "Meeting Link": {
                "url": event_data.get("meeting_link")
            },
            "Passcode": {
                "rich_text": [
                    {"text": {"content": str(event_data.get("passcode") or "")}}
                ]
            },
            "Organizer Email": {
                "email": event_data.get("organizer_email")
            },
            "Attendees Email": {
                "rich_text": [
                    {"text": {"content": ", ".join(event_data.get("attendees_email", []))}}
                ]
            }
        }
    }

    response = requests.post(url, headers=headers, json=payload, timeout=30)

        

def update_notion_page(page_id, updated_properties):
    """
    Update an existing Notion page with the provided properties.
    """
    url = f"{_get_notion_base_url()}/pages/{page_id}"
    headers = _get_notion_headers()
    
    payload = {
        "properties": updated_properties
    }

    response = requests.patch(url, headers=headers, json=payload, timeout=30)

    _error_response(response)

def find_page_by_event_id(event_id):
    """
    Search the Notion database for a page with the given event ID.
    """
    url = f"{_get_notion_base_url()}/databases/{settings.notion_database_id}/query"
    headers = _get_notion_headers()
    
    payload = {
        "filter": {
            "property": "Event ID",
            "rich_text": {
                "equals": event_id
            }
        }
    }

    response = requests.post(url, headers=headers, json=payload, timeout=30)
    data = response.json()

    results = data.get("results", [])
    
    return results[0] if results else None

def get_updated_fields(existing_page, new_data):
    """
    Compare existing page properties with new event data and return only the fields that have changed.
    """
    properties = existing_page["properties"]
    updated = {}

    # Normalizers
    def norm_text(v):
        return (v or "").strip()

    def norm_datetime(v):
        if not v:
            return ""
        return v.replace(".000", "")

    def norm_list(v):
        if not v:
            return []
        return sorted([x.strip().lower() for x in v])

    # Helper functions to safely extract property values
    def get_rich_text(prop_name):
        try:
            return properties[prop_name]["rich_text"][0]["plain_text"]
        except (KeyError, IndexError, TypeError):
            return ""

    def get_title(prop_name):
        try:
            return properties[prop_name]["title"][0]["plain_text"]
        except (KeyError, IndexError, TypeError):
            return ""

    def get_date(prop_name):
        try:
            return properties[prop_name]["date"]["start"]
        except (KeyError, TypeError):
            return ""

    def get_email(prop_name):
        try:
            return properties[prop_name]["email"]
        except KeyError:
            return ""

    def get_url(prop_name):
        try:
            return properties[prop_name]["url"]
        except KeyError:
            return ""

    # Event Title
    existing_title = get_title("Event Title")
    new_title = norm_text(new_data["event_title"])

    if norm_text(existing_title) != new_title:
        updated["Event Title"] = {
            "title": [{"text": {"content": new_title}}]
        }

    # Meeting ID
    existing_meeting_id = get_rich_text("Meeting ID")
    new_meeting_id = norm_text(new_data.get("meeting_id"))

    if norm_text(existing_meeting_id) != new_meeting_id:
        updated["Meeting ID"] = {
            "rich_text": [{"text": {"content": new_meeting_id}}]
        }

    # Start Timestamp
    existing_start = get_date("Start Timestamp")
    new_start = norm_datetime(new_data.get("start_timestamp"))

    if norm_datetime(existing_start) != new_start:
        updated["Start Timestamp"] = {
            "date": {"start": new_start}
        }

    # End Timestamp
    existing_end = get_date("End Timestamp")
    new_end = norm_datetime(new_data.get("end_timestamp"))

    if norm_datetime(existing_end) != new_end:
        updated["End Timestamp"] = {
            "date": {"start": new_end}
        }

    # Meeting Link
    existing_link = get_url("Meeting Link")
    new_link = norm_text(new_data.get("meeting_link"))

    if norm_text(existing_link) != new_link:
        updated["Meeting Link"] = {
            "url": new_link
        }

    # Passcode
    existing_passcode = get_rich_text("Passcode")
    new_passcode = norm_text(new_data.get("passcode"))

    if norm_text(existing_passcode) != new_passcode:
        updated["Passcode"] = {
            "rich_text": [{"text": {"content": new_passcode}}]
        }

    # Organizer Email
    existing_email = get_email("Organizer Email")
    new_email = norm_text(new_data.get("organizer_email"))

    if norm_text(existing_email) != new_email:
        updated["Organizer Email"] = {
            "email": new_email
        }

    # Attendees Email
    existing_attendees_raw = get_rich_text("Attendees Email")
    new_attendees_list = norm_list(new_data.get("attendees_email", []))

    existing_attendees_list = norm_list(
        existing_attendees_raw.split(",") if existing_attendees_raw else []
    )

    if existing_attendees_list != new_attendees_list:
        updated["Attendees Email"] = {
            "rich_text": [
                {"text": {"content": ", ".join(new_attendees_list)}} 
            ]
        }

    return updated