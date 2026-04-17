"""
Agent 6: Quality Checker
Score drafts on relevance, empathy, completeness, professionalism
Implement redraft loop (max 2 attempts)
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

MAX_REDRAFT_ATTEMPTS = 2


def parse_json(text: str) -> dict:
    """Parse JSON from LLM response, stripping markdown fences."""
    text = re.sub(r'```json|```', '', text).strip()
    return json.loads(text)


def check_quality(all_outputs: dict, draft_outputs: dict, redraft_reason: str = None, attempt: int = 0) -> dict:
    """
    Score both drafts on quality metrics and optionally trigger redraft.

    Scoring dimensions:
    - relevance (0-100): How well does it address the customer's issue?
    - empathy (0-100): Does it acknowledge feelings and show understanding?
    - completeness (0-100): Are all aspects addressed with clear next steps?
    - professionalism (0-100): Is tone appropriate and error-free?

    Flags:
    - missing_apology: No apology or acknowledgment of inconvenience
    - too_long: >300 words
    - too_short: <50 words
    - off_topic: Doesn't address the main issue
    - missing_next_steps: No clear action items or timeline

    Args:
        all_outputs: Combined outputs from all previous agents
        draft_outputs: Output from Agent 5 (drafter)
        redraft_reason: If provided, include in redraft request
        attempt: Current redraft attempt number (0 = first pass)

    Returns:
        Quality dict with scores, flags, approval decision
    """
    system_prompt = """You are a quality checker for support response drafts.

Score each draft on:
- relevance (0-100): How well does it address the customer's issue?
- empathy (0-100): Does it acknowledge feelings and show understanding?
- completeness (0-100): Are all aspects addressed with clear next steps?
- professionalism (0-100): Is tone appropriate and error-free?

Calculate overall_quality_score = average of the 4 scores.

If overall_quality_score < 70: set needs_redraft=true with redraft_reason explaining what needs improvement.

Flag issues:
- missing_apology: No apology or acknowledgment of inconvenience
- too_long: >300 words
- too_short: <50 words
- off_topic: Doesn't address the main issue
- missing_next_steps: No clear action items or timeline

Approve the better draft: set approved_draft="formal" | "friendly" based on higher overall score.

Return ONLY valid JSON.

Output format:
{
  "formal_scores": {"relevance": int, "empathy": int, "completeness": int, "professionalism": int, "overall": int},
  "friendly_scores": {"relevance": int, "empathy": int, "completeness": int, "professionalism": int, "overall": int},
  "needs_redraft": bool,
  "redraft_reason": str | null,
  "approved_draft": str,
  "quality_flags": list[str],
  "quality_summary": str
}
"""

    # Extract relevant info
    preprocessor = all_outputs.get("preprocessor", {})
    classifier = all_outputs.get("classifier", {})
    priority = all_outputs.get("priority", {})
    emotion = all_outputs.get("emotion", {})

    key_issue = preprocessor.get("key_issue", "")
    category = classifier.get("category", "General Inquiry")
    sentiment = emotion.get("sentiment", "neutral")
    is_vip = emotion.get("is_vip", False)

    formal_draft = draft_outputs.get("formal_draft", "")
    friendly_draft = draft_outputs.get("friendly_draft", "")
    recommended_tone = draft_outputs.get("recommended_tone", "formal")

    redraft_context = ""
    if redraft_reason:
        redraft_context = f"\n\nPrevious redraft reason: {redraft_reason}\nPlease address this issue in the new drafts."

    user_prompt = f"""Quality check these response drafts:

Category: {category}
Key Issue: {key_issue}
Customer Sentiment: {sentiment}
VIP Customer: {is_vip}
Recommended Tone: {recommended_tone}

FORMAL DRAFT:
{formal_draft}

FRIENDLY DRAFT:
{friendly_draft}
{redraft_context}

Score both drafts and recommend the better one.
"""

    try:
        print(f"[Agent 6] Checking quality (attempt {attempt + 1})...")

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

        # Ensure required fields with defaults
        if "formal_scores" not in result:
            result["formal_scores"] = {"relevance": 70, "empathy": 70, "completeness": 70, "professionalism": 70, "overall": 70}
        if "friendly_scores" not in result:
            result["friendly_scores"] = {"relevance": 70, "empathy": 70, "completeness": 70, "professionalism": 70, "overall": 70}
        if "needs_redraft" not in result:
            formal_overall = result.get("formal_scores", {}).get("overall", 70)
            friendly_overall = result.get("friendly_scores", {}).get("overall", 70)
            result["needs_redraft"] = max(formal_overall, friendly_overall) < 70
        if "redraft_reason" not in result:
            result["redraft_reason"] = "Quality scores below threshold" if result.get("needs_redraft") else None
        if "approved_draft" not in result:
            formal_overall = result.get("formal_scores", {}).get("overall", 70)
            friendly_overall = result.get("friendly_scores", {}).get("overall", 70)
            result["approved_draft"] = "formal" if formal_overall >= friendly_overall else "friendly"
        if "quality_flags" not in result:
            result["quality_flags"] = []
        if "quality_summary" not in result:
            result["quality_summary"] = ""

        # Handle redraft loop
        if result["needs_redraft"] and attempt < MAX_REDRAFT_ATTEMPTS:
            print(f"[Agent 6] Quality below threshold, requesting redraft: {result['redraft_reason']}")

            # Call drafter again with redraft reason
            from agents.drafter import draft_response

            # Modify the drafter input to include redraft feedback
            modified_draft_input = all_outputs.copy()
            modified_draft_input["redraft_feedback"] = result["redraft_reason"]

            new_drafts = draft_response(modified_draft_input)

            # Re-check quality with incremented attempt
            return check_quality(all_outputs, new_drafts, result["redraft_reason"], attempt + 1)

        print(f"[Agent 6] Complete - Approved: {result['approved_draft']}, Flags: {len(result['quality_flags'])}")

        return result

    except Exception as e:
        print(f"[Agent 6] Error: {str(e)}")
        return {
            "error": str(e),
            "formal_scores": {"relevance": 50, "empathy": 50, "completeness": 50, "professionalism": 50, "overall": 50},
            "friendly_scores": {"relevance": 50, "empathy": 50, "completeness": 50, "professionalism": 50, "overall": 50},
            "needs_redraft": True,
            "redraft_reason": "Error during quality check",
            "approved_draft": "formal",
            "quality_flags": ["error_occurred"],
            "quality_summary": "Quality check failed due to error"
        }


if __name__ == "__main__":
    # Test with sample outputs
    test_all_outputs = {
        "preprocessor": {"key_issue": "Duplicate charge"},
        "classifier": {"category": "Billing"},
        "priority": {"sla_hours": 4},
        "emotion": {"sentiment": "frustrated", "is_vip": False}
    }
    test_drafts = {
        "formal_draft": "Dear Customer, We apologize for the duplicate charge. We will investigate and refund within 24 hours.",
        "friendly_draft": "Hey! So sorry about the double charge. We're on it and you'll get your refund tomorrow!",
        "recommended_tone": "friendly"
    }

    result = check_quality(test_all_outputs, test_drafts)
    print(json.dumps(result, indent=2))
