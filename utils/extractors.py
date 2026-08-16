import re
from typing import Optional

def extract_meeting_link(text: str) -> Optional[str]:
    """
    Extracts common meeting links (Zoom, Google Meet, Teams, Webex) from text.
    """
    patterns = [
        # Zoom
        r"https:\/\/(?:[a-zA-Z0-9-]+\.)?zoom\.us\/j\/\d+(?:\?pwd=[a-zA-Z0-9]+)?",
        # Google Meet
        r"https:\/\/meet\.google\.com\/[a-z0-9-]+",
        # Microsoft Teams
        r"https:\/\/teams\.microsoft\.com\/l\/meetup-join\/[a-zA-Z0-9_%.-]+",
        # Webex
        r"https:\/\/[a-zA-Z0-9.-]+\.webex\.com\/meet\/[a-zA-Z0-9.-]+"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
            
    return None

def extract_sf_meeting_id(text: str) -> Optional[str]:
    """
    Extracts a potential Salesforce 15 or 18 character alphanumeric ID.
    Looks specifically for strings that are 15 or 18 chars, starting with 'a' 
    since custom objects like Meeting__c typically start with 'a'.
    """
    # Regex for 15 or 18 alphanumeric chars starting with 'a'
    pattern = r"\b(a[0-9A-Za-z]{14,17})\b"
    matches = re.findall(pattern, text)
    if matches:
        return matches[0]
    return None
