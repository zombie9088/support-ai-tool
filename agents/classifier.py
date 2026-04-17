"""
Agent 2: Classifier
Category classification with confidence scores
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


def classify_ticket(preprocessor_output: dict) -> dict:
    """
    Classify a support ticket into categories with confidence scores.

    Args:
        preprocessor_output: Output from Agent 1 (preprocessor)

    Returns:
        Classification dict with category, subcategory, confidence, alternatives
    """
    system_prompt = """You are a support ticket classifier. Classify tickets into one of these categories:
- Billing (duplicate charge, wrong amount, refund request, subscription cancel)
- Technical (login issue, app crash, slow performance, feature not working)
- Account (password reset, account locked, email change, profile update)
- Shipping (delayed delivery, wrong item, damaged package, tracking issue)
- Refund (refund status, partial refund, refund denied)
- Feature Request (new feature ask, improvement suggestion, integration request)
- Security (suspicious activity, data breach concern, 2FA issue, account hacked)
- General Inquiry (misc)

Assign a confidence score 0-100. Provide top 3 alternative categories with scores.
If confidence < 60, set low_confidence_flag to true.
Return ONLY valid JSON.

Output format:
{
  "category": str,
  "subcategory": str,
  "confidence": int,
  "low_confidence_flag": bool,
  "alternative_categories": [{"category": str, "confidence": int}],
  "reasoning": str
}
"""

    cleaned_text = preprocessor_output.get("cleaned_text", "")
    key_issue = preprocessor_output.get("key_issue", "")

    user_prompt = f"""Classify this support ticket:

Key Issue: {key_issue}
Cleaned Text: {cleaned_text}
"""

    try:
        print(f"[Agent 2] Classifying ticket...")

        response = llm.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            max_tokens=800
        )

        result = parse_json(response.choices[0].message.content)

        # Ensure required fields
        if "category" not in result:
            result["category"] = "General Inquiry"
        if "confidence" not in result:
            result["confidence"] = 50
        if "low_confidence_flag" not in result:
            result["low_confidence_flag"] = result.get("confidence", 50) < 60
        if "alternative_categories" not in result:
            result["alternative_categories"] = []
        if "reasoning" not in result:
            result["reasoning"] = ""

        print(f"[Agent 2] Complete - Category: {result.get('category', 'Unknown')} (confidence: {result.get('confidence', 0)}%)")

        return result

    except Exception as e:
        print(f"[Agent 2] Error: {str(e)}")
        return {"error": str(e), "category": "Unknown", "confidence": 0}


if __name__ == "__main__":
    # Test with sample preprocessor output
    test_preprocessed = {
        "cleaned_text": "I was charged twice for my subscription this month.",
        "key_issue": "Duplicate charge on subscription",
        "customer_tone": "frustrated"
    }

    result = classify_ticket(test_preprocessed)
    print(json.dumps(result, indent=2))
