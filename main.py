from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import asyncio
import logging

# Set up professional logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

from models.cloudmailin import CloudMailinPayload
from services.llm_service import LLMService
from services.salesforce_service import SalesforceService
from utils.extractors import extract_meeting_link, extract_sf_meeting_id

app = FastAPI(title="Salesforce Smart Email Sync Webhook")

llm_service = LLMService()
sf_service = SalesforceService()

def process_email_background(email_content: str, subject: str, combined_text: str, payload_html: str):
    """
    This function runs in the background so CloudMailin doesn't timeout!
    """
    try:
        logger.debug("--- Starting Background Process ---")
        # 1. Regex -> Extract Salesforce Meeting ID
        meeting_id = extract_sf_meeting_id(combined_text)
        logger.debug(f"Regex Extracted Meeting ID: {meeting_id}")
        previous_insights = None
        
        # 2. Use ID to fetch Previous SF Data
        if meeting_id:
            logger.debug(f"Found potential Salesforce ID: {meeting_id}")
            insights = sf_service.get_meeting_insights(meeting_id)
            logger.debug(f"Fetched notes from Salesforce: {insights}")
            if "Salesforce connection not established" not in insights and "No previous meeting notes found" not in insights and "Error" not in insights:
                previous_insights = insights
            elif "No previous meeting notes found" in insights:
                logger.info("Meeting ID found, but no previous notes exist.")
            else:
                meeting_id = None

        # 3. Regex -> Extract Meeting Link
        meeting_link = extract_meeting_link(combined_text)
        logger.debug(f"Regex Extracted Meeting Link: {meeting_link}")

        # 4. Call LLM for Summary and Overall Sentiment
        logger.info("Analyzing email with LLM...")
        llm_analysis = llm_service.analyze_email(email_content, previous_insights)
        logger.debug(f"Raw LLM Response dictionary: {llm_analysis}")
        summary = llm_analysis.get('summary', 'No summary generated.')
        sentiment = llm_analysis.get('overall_sentiment', 'Neutral')
        logger.info(f"LLM Analysis complete. \nSentiment: {sentiment}\nSummary: {summary}")

        # 5. Push to Salesforce
        if sf_service.is_connected():
            if not meeting_id:
                logger.info("No valid Meeting ID found. Creating new Meeting__c record...")
                meeting_id = sf_service.create_meeting(subject, summary, sentiment, meeting_link)
                logger.info(f"Created Meeting__c with ID: {meeting_id}")
            else:
                logger.info(f"Updating Meeting__c ({meeting_id}) summary and sentiment...")
                sf_service.update_meeting(meeting_id, summary, sentiment)

            if meeting_id:
                logger.info(f"Creating Meeting_Notes__c for Meeting {meeting_id}...")
                raw_body = payload_html if payload_html else email_content
                success = sf_service.create_meeting_notes(meeting_id, raw_body)
                if success:
                    logger.info("Successfully created Meeting Notes.")
                else:
                    logger.info("Failed to create Meeting Notes.")
            else:
                logger.info("Could not obtain a Meeting ID.")
    except Exception as e:
        logger.error(f"Error in background task: {e}")


@app.post("/webhook")
async def receive_email(payload: CloudMailinPayload, background_tasks: BackgroundTasks):
    try:
        logger.debug(f"Incoming Webhook Payload Headers: {payload.headers}")
        logger.debug(f"Incoming Webhook Payload Plain Text: {payload.plain}")
        logger.debug(f"Incoming Webhook Payload HTML: {payload.html}")
        email_content = payload.plain or payload.html or ""
        subject = payload.get_subject()
        
        if not email_content:
            return JSONResponse(status_code=400, content={"message": "No email content found"})

        logger.info(f"Received email: {subject}. Sending to background task...")
        combined_text = subject + " " + email_content

        # Instantly hand off the heavy lifting to the background task!
        background_tasks.add_task(
            process_email_background, 
            email_content, 
            subject, 
            combined_text, 
            payload.html
        )

        # Immediately return 200 OK to CloudMailin so it doesn't timeout!
        return {
            "status": "success",
            "message": "Email received and processing in background."
        }

    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def health_check():
    return {"status": "ok", "service": "Salesforce Smart Email Sync"}

