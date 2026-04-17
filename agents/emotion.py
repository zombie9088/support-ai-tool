"""
Agent 4: Emotion & Churn Risk Analyzer
Sentiment scoring, churn detection, VIP identification
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


def analyze_emotion(preprocessor_output: dict, classifier_output: dict, priority_output: dict) -> dict:
    """
    Analyze sentiment, frustration, churn risk, and VIP status.

    Args:
        preprocessor_output: Output from Agent 1
        classifier_output: Output from Agent 2
        priority_output: Output from Agent 3

    Returns:
        Emotion dict with sentiment, churn scores, VIP status, retention recommendations
    """
    system_prompt = """You are an emotion and churn risk analyzer for support tickets.

Analyze the ticket and provide:
- sentiment: very_negative | negative | neutral | positive | very_positive
- frustration_score: 0-100 (higher = more frustrated)
- churn_risk_score: 0-100 based on: explicit cancel/leave signals, anger level, repeated complaints, competitor mentions
- churn_risk_label: "High" (>70) | "Medium" (40-70) | "Low" (<40)
- churn_signals: list of exact phrases from ticket indicating churn risk
- is_vip: true if enterprise/premium/business plan keywords found
- retention_action: if churn_risk > 60, recommend one of: "immediate_callback" | "discount_offer" | "escalate_to_retention" | "send_apology_voucher"
- emotion_summary: 1 sentence summary

Return ONLY valid JSON.

Output format:
{
  "sentiment": str,
  "frustration_score": int,
  "churn_risk_score": int,
  "churn_risk_label": str,
  "churn_signals": list[str],
  "is_vip": bool,
  "retention_action": str | null,
  "emotion_summary": str
}
"""

    cleaned_text = preprocessor_output.get("cleaned_text", "")
    tone = preprocessor_output.get("customer_tone", "neutral")

    user_prompt = f"""Analyze emotion and churn risk for this ticket:

Customer Tone: {tone}
Ticket Text: {cleaned_text}
"""

    try:
        print(f"[Agent 4] Analyzing emotion and churn risk...")

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

        # Ensure required fields with defaults
        if "sentiment" not in result:
            result["sentiment"] = "neutral"
        if "frustration_score" not in result:
            result["frustration_score"] = 50
        if "churn_risk_score" not in result:
            result["churn_risk_score"] = 30
        if "churn_risk_label" not in result:
            score = result.get("churn_risk_score", 30)
            if score > 70:
                result["churn_risk_label"] = "High"
            elif score >= 40:
                result["churn_risk_label"] = "Medium"
            else:
                result["churn_risk_label"] = "Low"
        if "churn_signals" not in result:
            result["churn_signals"] = []
        if "is_vip" not in result:
            result["is_vip"] = False
        if "retention_action" not in result:
            if result.get("churn_risk_score", 0) > 60:
                result["retention_action"] = "send_apology_voucher"
            else:
                result["retention_action"] = None
        if "emotion_summary" not in result:
            result["emotion_summary"] = ""

        print(f"[Agent 4] Complete - Sentiment: {result.get('sentiment', 'unknown')}, Churn: {result.get('churn_risk_label', 'Low')}, VIP: {result.get('is_vip')}")

        return result

    except Exception as e:
        print(f"[Agent 4] Error: {str(e)}")
        return {"error": str(e), "sentiment": "neutral", "churn_risk_score": 0, "churn_risk_label": "Low", "is_vip": False}


if __name__ == "__main__":
    # Test with sample inputs
    test_preprocessed = {
        "cleaned_text": "I'm seriously considering cancelling my subscription. This is the third time this month!",
        "customer_tone": "angry"
    }
    test_classified = {"category": "Billing"}
    test_priority = {"priority": "P2 High"}

    result = analyze_emotion(test_preprocessed, test_classified, test_priority)
    print(json.dumps(result, indent=2))
