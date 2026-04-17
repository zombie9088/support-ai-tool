"""
Agent 5: Response Drafter
Generate formal and friendly response drafts
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


def draft_response(all_outputs: dict) -> dict:
    """
    Generate two response drafts: formal and friendly.

    Args:
        all_outputs: Combined outputs from all previous agents

    Returns:
        Draft dict with formal_draft, friendly_draft, tone recommendation
    """
    system_prompt = """You are a support response drafter. Generate TWO distinct response drafts:

FORMAL: Professional, empathetic, concise. Uses "Dear [Customer]", structured paragraphs.
FRIENDLY: Warm, conversational, supportive. Uses first name greeting style.

Both must:
- Acknowledge the issue
- Address it directly
- Offer next steps
- Include relevant resolution timeline based on SLA

If churn_risk > 60: include retention language (acknowledge frustration, offer compensation hint)
If escalation_required: mention that a senior specialist will reach out
If is_vip: add priority handling acknowledgment
Tailor response to category (billing gets refund process info, technical gets troubleshooting steps, etc.)

Return ONLY valid JSON.

Output format:
{
  "formal_draft": str,
  "friendly_draft": str,
  "recommended_tone": str,  // "formal" | "friendly"
  "tone_recommendation_reason": str,
  "key_points_addressed": list[str]
}
"""

    # Extract relevant info from all outputs
    preprocessor = all_outputs.get("preprocessor", {})
    classifier = all_outputs.get("classifier", {})
    priority = all_outputs.get("priority", {})
    emotion = all_outputs.get("emotion", {})

    category = classifier.get("category", "General Inquiry")
    sla_hours = priority.get("sla_hours", 24)
    escalation_required = priority.get("escalation_required", False)
    churn_risk = emotion.get("churn_risk_score", 0)
    is_vip = emotion.get("is_vip", False)
    sentiment = emotion.get("sentiment", "neutral")
    cleaned_text = preprocessor.get("cleaned_text", "")
    key_issue = preprocessor.get("key_issue", "")

    user_prompt = f"""Draft responses for this support ticket:

Category: {category}
Key Issue: {key_issue}
SLA Target: {sla_hours} hours
Escalation Required: {escalation_required}
Churn Risk Score: {churn_risk}
VIP Customer: {is_vip}
Sentiment: {sentiment}

Original Ticket: {cleaned_text}

Generate both formal and friendly drafts with appropriate tone and content.
"""

    try:
        print(f"[Agent 5] Drafting responses...")

        response = llm.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.5,
            max_tokens=1500
        )

        result = parse_json(response.choices[0].message.content)

        # Ensure required fields with defaults
        if "formal_draft" not in result:
            result["formal_draft"] = "Dear Customer, Thank you for contacting support. We will look into this issue. Regards, Support Team"
        if "friendly_draft" not in result:
            result["friendly_draft"] = "Hi there! Thanks for reaching out. We're on it and will get this sorted for you! Cheers, Support Team"
        if "recommended_tone" not in result:
            result["recommended_tone"] = "formal" if sentiment in ["very_negative", "negative"] else "friendly"
        if "tone_recommendation_reason" not in result:
            result["tone_recommendation_reason"] = f"Recommended based on customer sentiment: {sentiment}"
        if "key_points_addressed" not in result:
            result["key_points_addressed"] = [key_issue] if key_issue else ["Issue acknowledged"]

        print(f"[Agent 5] Complete - Drafted {len(result['formal_draft'])} chars formal, {len(result['friendly_draft'])} chars friendly")

        return result

    except Exception as e:
        print(f"[Agent 5] Error: {str(e)}")
        return {
            "error": str(e),
            "formal_draft": "We apologize for the inconvenience. Our team will investigate this issue and respond within the SLA timeframe.",
            "friendly_draft": "Hey! So sorry about this. We're looking into it and will get back to you soon!",
            "recommended_tone": "formal",
            "tone_recommendation_reason": "Error occurred during drafting",
            "key_points_addressed": ["Issue acknowledged"]
        }


if __name__ == "__main__":
    # Test with sample combined outputs
    test_all_outputs = {
        "preprocessor": {"cleaned_text": "I was charged twice!", "key_issue": "Duplicate charge"},
        "classifier": {"category": "Billing"},
        "priority": {"sla_hours": 4, "escalation_required": False},
        "emotion": {"churn_risk_score": 45, "is_vip": False, "sentiment": "frustrated"}
    }

    result = draft_response(test_all_outputs)
    print(json.dumps(result, indent=2))
