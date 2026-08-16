# Salesforce Smart Email Sync Webhook

A Python web service that receives emails via CloudMailin, analyzes the content using Nvidia Llama 3.3, and integrates with Salesforce to extract insights, summarize meetings, and track sentiment.

## Architecture

- **FastAPI**: Receives webhook POST requests from CloudMailin.
- **Nvidia Llama 3.3**: Analyzes email text to extract a meeting link, create a summary, determine sentiment, and attempt to find a related Salesforce Meeting ID.
- **Salesforce (`simple-salesforce`)**: Queries previous `Meeting_Notes__c` for context, and inserts new records into `Meeting__c` and `Meeting_Notes__c`.

## Running Locally

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   Copy `.env.example` to `.env` and fill in the following required variables:
   - `NVIDIA_API_KEY`
   - `SF_CLIENT_ID` (Salesforce Connected App Consumer Key)
   - `SF_CLIENT_SECRET` (Salesforce Connected App Consumer Secret)
   - `SF_INSTANCE_URL` (Your Salesforce custom domain, e.g., `https://synechron-demo-dev-ed.develop.my.salesforce.com`)

4. Run the server:
   ```bash
   uvicorn main:app --reload
   ```

5. Test the webhook locally using the included test script:
   ```bash
   python test_webhook.py
   ```

## Deploying to Render

This project is configured to run easily on Render as a Web Service.
1. Commit all your code and push to your GitHub repository.
2. In the Render Dashboard, create a new **Web Service** connected to your GitHub repository.
3. Configure the service:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Under the **Environment** tab in Render, add the 4 environment variables listed in step 3 above.
5. Deploy! Render will give you a URL (e.g., `https://your-app.onrender.com`).
6. Finally, configure **CloudMailin** to send POST requests to `https://your-app.onrender.com/webhook`.
