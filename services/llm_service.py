import os
import json
from openai import OpenAI
from typing import Dict, Any, Optional

class LLMService:
    def __init__(self):
        api_key = os.getenv("NVIDIA_API_KEY")
        if not api_key:
            raise ValueError("NVIDIA_API_KEY environment variable is missing")
            
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=api_key
        )
        self.model = "meta/llama-3.3-70b-instruct"

    def analyze_email(self, email_text: str, previous_summary: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyzes the email content to extract meeting link, summarize content,
        and provide sentiment analysis.
        """
        system_prompt = (
            "You are an AI assistant that analyzes emails and maintains a running summary in JSON format.\n"
            "You must respond ONLY with a valid JSON object, containing EXACTLY the following two keys:\n"
            "  - 'summary': (string) An updated, highly detailed running summary of the ENTIRE conversation thread. You MUST retain ALL key points, dates, decisions, and issues from the existing summary. Do NOT drop any historical details. Integrate the existing summary with the new email content to produce a single cohesive and comprehensive summary.\n"
            "  - 'overall_sentiment': (string) The CURRENT sentiment or status of the project based on the latest email. Weight the most recent email heavily. If a previous crisis has been stabilized or mitigated by the latest email, mark the sentiment as 'Neutral'. "
            "Must be exactly one of: 'Positive', 'Neutral', or 'Negative'.\n"
        )
        
        user_prompt = f"Analyze the following CURRENT email content:\n\n{email_text}\n\n"
        
        if previous_summary:
            user_prompt += f"EXISTING RUNNING SUMMARY of the thread so far:\n{previous_summary}\n\n"
            user_prompt += "Please integrate the existing running summary with the current email. CRITICAL: You must preserve all key points and factual details from the EXISTING RUNNING SUMMARY. Do not summarize away important historical context. Generate an updated 'summary' and evaluate the 'overall_sentiment' based heavily on the trajectory of this latest email.\n"

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            top_p=0.7,
            max_tokens=1024,
            stream=False,
            response_format={"type": "json_object"}
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Clean up in case Llama adds markdown code blocks
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
            
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON from LLM: {response_text}")
            return {
                "summary": "Error parsing summary from LLM response.",
                "overall_sentiment": "Neutral"
            }
