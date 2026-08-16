import logging
logger = logging.getLogger(__name__)
import os
import requests
from simple_salesforce import Salesforce, SalesforceAuthenticationFailed
from typing import Optional, Dict, Any, List

class SalesforceService:
    def __init__(self):
        # Prefer Client Credentials if provided
        client_id = os.getenv("SF_CLIENT_ID")
        client_secret = os.getenv("SF_CLIENT_SECRET")
        
        # Fallbacks
        session_id = os.getenv("SF_SESSION_ID")
        instance_url = os.getenv("SF_INSTANCE_URL")
        
        username = os.getenv("SF_USERNAME")
        password = os.getenv("SF_PASSWORD")
        security_token = os.getenv("SF_SECURITY_TOKEN")
        domain = os.getenv("SF_DOMAIN", "login")
        
        self.sf = None
        
        try:
            if client_id and client_secret:
                logger.info("Using OAuth 2.0 Client Credentials Flow for Salesforce.")
                
                # If a custom instance URL is provided, use it. Otherwise, fallback to the generic domain.
                base_url = instance_url.rstrip('/') if instance_url else f"https://{domain}.salesforce.com"
                auth_url = f"{base_url}/services/oauth2/token"
                
                payload = {
                    'grant_type': 'client_credentials',
                    'client_id': client_id,
                    'client_secret': client_secret
                }
                response = requests.post(auth_url, data=payload)
                
                if response.status_code != 200:
                    logger.info(f"Salesforce OAuth Error: {response.text}")
                    response.raise_for_status()
                
                auth_data = response.json()
                self.sf = Salesforce(
                    session_id=auth_data['access_token'],
                    instance_url=auth_data['instance_url']
                )
            elif session_id and instance_url:
                logger.info("Using Session ID authentication for Salesforce.")
                self.sf = Salesforce(session_id=session_id, instance_url=instance_url)
            elif username and password:
                logger.info("Using Username/Password authentication for Salesforce.")
                self.sf = Salesforce(
                    username=username, 
                    password=password, 
                    security_token=security_token if security_token else '', 
                    domain=domain
                )
            else:
                logger.info("Warning: Salesforce credentials missing from environment variables.")
        except Exception as e:
            logger.error(f"Failed to connect to Salesforce: {e}")

    def is_connected(self) -> bool:
        return self.sf is not None

    def get_meeting_summary(self, meeting_id: str) -> Optional[str]:
        """
        Queries the existing Summary__c field for the given Meeting__c Id.
        Returns the existing summary string if available, or None.
        """
        if not self.is_connected():
            return "Salesforce connection not established."

        query = f"SELECT Summary__c FROM Meeting__c WHERE Id = '{meeting_id}'"
        try:
            result = self.sf.query(query)
            records = result.get('records', [])
            
            if not records:
                return "No previous meeting found."
                
            return records[0].get('Summary__c')
        except Exception as e:
            logger.error(f"Error querying Salesforce for Meeting__c: {e}")
            return f"Error retrieving summary: {e}"

    def create_meeting(self, subject: str, summary: str, sentiment: str, meeting_link: Optional[str]) -> Optional[str]:
        """
        Creates a new Meeting__c record.
        """
        if not self.is_connected():
            return None

        try:
            data = {
                'Name': subject[:80],
                'Subject__c': subject,
                'Summary__c': summary,
                'Sentiment__c': sentiment
            }
            if meeting_link:
                data['Meeting_Link__c'] = meeting_link
                
            result = self.sf.Meeting__c.create(data)
            return result.get('id')
        except Exception as e:
            logger.error(f"Error creating Meeting__c: {e}")
            return None
            
    def update_meeting(self, meeting_id: str, summary: str, sentiment: str) -> bool:
        """
        Updates the Summary__c and Sentiment__c on the parent Meeting__c.
        """
        if not self.is_connected():
            return False
            
        try:
            self.sf.Meeting__c.update(meeting_id, {
                'Summary__c': summary,
                'Sentiment__c': sentiment
            })
            return True
        except Exception as e:
            logger.error(f"Error updating Meeting__c sentiment: {e}")
            return False

    def create_meeting_notes(self, meeting_id: str, raw_body: str) -> bool:
        """
        Creates a new child Meeting_Notes__c record attached to the Meeting__c.
        """
        if not self.is_connected():
            return False

        try:
            data = {
                'Meeting__c': meeting_id,
                'Notes__c': raw_body,
            }

            self.sf.Meeting_Notes__c.create(data)
            return True
        except Exception as e:
            logger.error(f"Error creating Meeting_Notes__c: {e}")
            return False

