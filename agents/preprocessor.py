"""
Agent 1: Preprocessor
PII masking, text cleaning, metadata extraction
"""

import os
import re
import json
import httpx
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = httpx.Client(verify=False)
llm = OpenAI(
    base_url=os.getenv("api_endpoint"),
    api_key=os.getenv("api_key"),
    http_client=client
)
model = os.getenv("model")


def parse_json(text: str) -> dict:
    """Parse JSON from LLM response, stripping markdown fences."""
    text = re.sub(r'```json|```', '', text).strip()
    return json.loads(text)


def preprocess_ticket(raw_text: str, metadata: dict = None) -> dict:
    """
    Preprocess a support ticket: mask PII, clean text, extract metadata.

    Args:
        raw_text: Raw ticket text
        metadata: Optional metadata dict

    Returns:
        Preprocessed ticket dict
    """
    system_prompt = """You are a support ticket preprocessor. Your task is to:
1. Anonymize PII: replace names with [NAME], emails with [EMAIL], phone numbers with [PHONE], account IDs with [ACCOUNT_ID]
2. Clean text: fix typos, normalize whitespace, remove profanity (replace with [REDACTED])
3. Extract: key_issue (1 sentence summary), product_mentioned (str or null), customer_tone (angry/frustrated/neutral/polite/demanding), urgency_keywords (list of strings found)
4. Return ONLY valid JSON, no preamble

Output format:
{
  "cleaned_text": str,
  "key_issue": str,
  "product_mentioned": str | null,
  "customer_tone": str,
  "urgency_keywords": list[str],
  "pii_detected": bool,
  "pii_types_found": list[str]
}
"""

    user_prompt = f"Process this support ticket:\n\n{raw_text}"

    try:
        print(f"[Agent 1] Preprocessing ticket...")

        response = llm.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )

        result = parse_json(response.choices[0].message.content)

        # Ensure all required fields exist
        required_fields = ["cleaned_text", "key_issue", "product_mentioned", "customer_tone", "urgency_keywords", "pii_detected", "pii_types_found"]
        for field in required_fields:
            if field not in result:
                result[field] = None if field in ["product_mentioned", "urgency_keywords", "pii_types_found"] else "" if field == "cleaned_text" else False

        print(f"[Agent 1] Complete - PII detected: {result.get('pii_detected', False)}, tone: {result.get('customer_tone', 'unknown')}")

        return result

    except Exception as e:
        print(f"[Agent 1] Error: {str(e)}")
        return {"error": str(e)}


if __name__ == "__main__":
    # Test with sample ticket
    test_ticket = """
    Hi, my name is John Smith and my email is john.smith@email.com.
    I've been charged twice for my subscription! My account ID is ACC-12345.
    This is urgent - I need this fixed ASAP!!! Call me at 555-123-4567.
    """

    result = preprocess_ticket(test_ticket)
    print(json.dumps(result, indent=2))
