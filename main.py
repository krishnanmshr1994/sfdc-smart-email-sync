from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from models.cloudmailin import CloudMailinPayload
from services.llm_service import LLMService
from services.salesforce_service import SalesforceService
from utils.extractors import extract_meeting_link, extract_sf_meeting_id

app = FastAPI(title="Salesforce Smart Email Sync Webhook")

llm_service = LLMService()
sf_service = SalesforceService()

@app.post("/webhook")
async def receive_email(payload: CloudMailinPayload):
    try:
        email_content = payload.plain or payload.html or ""
        subject = payload.get_subject()
        
        if not email_content:
            return JSONResponse(status_code=400, content={"message": "No email content found"})

        print(f"Received email: {subject}")
        combined_text = subject + " " + email_content

        # 1. Regex -> Extract Salesforce Meeting ID
        meeting_id = extract_sf_meeting_id(combined_text)
        previous_insights = None
        
        # 2. Use ID to fetch Previous SF Data
        if meeting_id:
            print(f"Found potential Salesforce ID: {meeting_id}")
            insights = sf_service.get_meeting_insights(meeting_id)
            if "Salesforce connection not established" not in insights and "No previous meeting notes found" not in insights and "Error" not in insights:
                previous_insights = insights
            elif "No previous meeting notes found" in insights:
                print("Meeting ID found, but no previous notes exist.")
            else:
                # If there was an error, the meeting ID might be invalid or we can't connect.
                # We'll just set it to None to create a new one.
                meeting_id = None

        # 3. Regex -> Extract Meeting Link
        meeting_link = extract_meeting_link(combined_text)

        # 4. Call LLM for Summary and Overall Sentiment
        print("Analyzing email with LLM...")
        llm_analysis = llm_service.analyze_email(email_content, previous_insights)
        summary = llm_analysis.get('summary', 'No summary generated.')
        sentiment = llm_analysis.get('overall_sentiment', 'Neutral')
        print(f"LLM Analysis complete. \nSentiment: {sentiment}\nSummary: {summary}")

        # 5. Push to Salesforce
        if sf_service.is_connected():
            if not meeting_id:
                # Create new meeting since we couldn't find one
                print("No valid Meeting ID found. Creating new Meeting__c record...")
                meeting_id = sf_service.create_meeting(subject, sentiment)
                print(f"Created Meeting__c with ID: {meeting_id}")
            else:
                # Update existing meeting with the new overall sentiment
                print(f"Updating Meeting__c ({meeting_id}) overall sentiment to: {sentiment}")
                sf_service.update_meeting_sentiment(meeting_id, sentiment)

            if meeting_id:
                print(f"Creating Meeting_Notes__c for Meeting {meeting_id}...")
                success = sf_service.create_meeting_notes(meeting_id, summary, meeting_link)
                if success:
                    print("Successfully created Meeting Notes.")
                else:
                    print("Failed to create Meeting Notes.")
            else:
                print("Could not obtain a Meeting ID.")

        return {
            "status": "success",
            "message": "Email processed successfully",
            "meeting_id": meeting_id,
            "sentiment": sentiment
        }

    except Exception as e:
        print(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def health_check():
    return {"status": "ok", "service": "Salesforce Smart Email Sync"}
