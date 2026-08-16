from dotenv import load_dotenv
load_dotenv()

from services.salesforce_service import SalesforceService

print("Testing Salesforce Connection...")
sf_service = SalesforceService()

if sf_service.is_connected():
    print("✅ SUCCESS! Connected to Salesforce.")
else:
    print("❌ FAILED! Could not connect to Salesforce. Please check the error message above.")
