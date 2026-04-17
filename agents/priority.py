"""
Agent 3: Priority Scorer
Assign P1-P4 priority, SLA targets, escalation flags
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


def assign_priority(preprocessor_output: dict, classifier_output: dict) -> dict:
    """
    Assign priority level, SLA target, and escalation flag.

    Priority levels:
    - P1 Critical: data breach, account hacked, complete outage, legal threat
    - P2 High: billing fraud, service severely degraded, churn risk + angry
    - P3 Medium: standard issues, moderate frustration
    - P4 Low: feature requests, general inquiry, polite tone

    SLA targets: P1=1hr, P2=4hr, P3=24hr, P4=72hr

    Args:
        preprocessor_output: Output from Agent 1
        classifier_output: Output from Agent 2

    Returns:
        Priority dict with level, SLA, escalation info
    """
    system_prompt = """You are a support ticket priority scorer. Assign priority based on:

P1 Critical (1hr SLA): data breach, account hacked, complete outage, legal threat, security breach
P2 High (4hr SLA): billing fraud, service severely degraded, churn risk + angry customer, VIP with major issue
P3 Medium (24hr SLA): standard issues, moderate frustration, non-urgent billing
P4 Low (72hr SLA): feature requests, general inquiry, polite tone, no urgency

Set escalation_required=true for P1, or P2 with angry tone, or any ticket with legal/security implications.

Return ONLY valid JSON.

Output format:
{
  "priority": str,  // "P1 Critical" | "P2 High" | "P3 Medium" | "P4 Low"
  "priority_level": int,  // 1 | 2 | 3 | 4
  "sla_hours": int,
  "escalation_required": bool,
  "escalation_reason": str | null,
  "priority_reasoning": str
}
"""

    cleaned_text = preprocessor_output.get("cleaned_text", "")
    tone = preprocessor_output.get("customer_tone", "neutral")
    urgency_keywords = preprocessor_output.get("urgency_keywords", [])
    category = classifier_output.get("category", "General Inquiry")

    user_prompt = f"""Assign priority to this ticket:

Category: {category}
Customer Tone: {tone}
Urgency Keywords: {urgency_keywords}
Ticket Text: {cleaned_text}
"""

    try:
        print(f"[Agent 3] Assigning priority...")

        response = llm.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            max_tokens=600
        )

        result = parse_json(response.choices[0].message.content)

        # Ensure required fields with defaults
        if "priority" not in result:
            result["priority"] = "P3 Medium"
        if "priority_level" not in result:
            result["priority_level"] = 3
        if "sla_hours" not in result:
            sla_map = {"P1 Critical": 1, "P2 High": 4, "P3 Medium": 24, "P4 Low": 72}
            result["sla_hours"] = sla_map.get(result.get("priority", "P3 Medium"), 24)
        if "escalation_required" not in result:
            result["escalation_required"] = result.get("priority_level", 3) <= 2
        if "escalation_reason" not in result:
            result["escalation_reason"] = "High priority ticket" if result.get("escalation_required") else None
        if "priority_reasoning" not in result:
            result["priority_reasoning"] = ""

        print(f"[Agent 3] Complete - {result.get('priority', 'Unknown')}, SLA: {result.get('sla_hours')}hr, escalation: {result.get('escalation_required')}")

        return result

    except Exception as e:
        print(f"[Agent 3] Error: {str(e)}")
        return {"error": str(e), "priority": "P3 Medium", "priority_level": 3, "sla_hours": 24, "escalation_required": False}


if __name__ == "__main__":
    # Test with sample inputs
    test_preprocessed = {
        "cleaned_text": "My account was hacked and I lost all my data!",
        "customer_tone": "angry",
        "urgency_keywords": ["ASAP", "urgent", "immediately"]
    }
    test_classified = {
        "category": "Security"
    }

    result = assign_priority(test_preprocessed, test_classified)
    print(json.dumps(result, indent=2))
