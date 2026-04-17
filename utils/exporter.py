"""
Export utilities for support ticket results.
JSON export, CSV export, simulated ticketing system push.
"""

import json
import csv
import io
import random
from datetime import datetime
from typing import Dict, List


def export_json(results: dict) -> str:
    """
    Export pipeline results as formatted JSON string.

    Args:
        results: Complete pipeline results dict

    Returns:
        Formatted JSON string
    """
    return json.dumps(results, indent=2, default=str)


def export_csv(results_list: List[dict]) -> bytes:
    """
    Export batch results as CSV bytes for download.

    Args:
        results_list: List of pipeline results

    Returns:
        CSV as bytes
    """
    output = io.StringIO()

    if not results_list:
        return b""

    # Flatten results for CSV
    fieldnames = [
        "ticket_id", "category", "subcategory", "confidence",
        "priority", "priority_level", "sla_hours", "escalation_required",
        "sentiment", "frustration_score", "churn_risk_score", "churn_risk_label",
        "is_vip", "approved_draft", "quality_score", "processing_time_ms"
    ]

    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()

    for result in results_list:
        row = {
            "ticket_id": result.get("ticket_id", ""),
            "category": result.get("classifier", {}).get("category", ""),
            "subcategory": result.get("classifier", {}).get("subcategory", ""),
            "confidence": result.get("classifier", {}).get("confidence", 0),
            "priority": result.get("priority", {}).get("priority", ""),
            "priority_level": result.get("priority", {}).get("priority_level", 0),
            "sla_hours": result.get("priority", {}).get("sla_hours", 0),
            "escalation_required": result.get("priority", {}).get("escalation_required", False),
            "sentiment": result.get("emotion", {}).get("sentiment", ""),
            "frustration_score": result.get("emotion", {}).get("frustration_score", 0),
            "churn_risk_score": result.get("emotion", {}).get("churn_risk_score", 0),
            "churn_risk_label": result.get("emotion", {}).get("churn_risk_label", ""),
            "is_vip": result.get("emotion", {}).get("is_vip", False),
            "approved_draft": result.get("quality_checker", {}).get("approved_draft", ""),
            "quality_score": result.get("quality_checker", {}).get("formal_scores", {}).get("overall", 0),
            "processing_time_ms": result.get("processing_time_ms", 0),
        }
        writer.writerow(row)

    return output.getvalue().encode('utf-8')


def simulate_ticketing_push(result: dict) -> dict:
    """
    Simulate pushing a ticket to a ticketing system (e.g., Zendesk).

    Args:
        result: Pipeline result dict

    Returns:
        Simulated push result with ticket number
    """
    systems = ["Zendesk", "Freshdesk", "ServiceNow", "Jira Service Desk"]
    selected_system = random.choice(systems)

    ticket_number = f"ZD-{random.randint(10000, 99999)}"

    return {
        "status": "success",
        "simulated_system": selected_system,
        "ticket_number": ticket_number,
        "assigned_to": "AI-Triage-Queue",
        "priority_mapped": result.get("priority", {}).get("priority", "P3 Medium"),
        "timestamp": datetime.now().isoformat(),
        "category": result.get("classifier", {}).get("category", "Unknown"),
        "sla_hours": result.get("priority", {}).get("sla_hours", 24)
    }


def format_for_ticketing_system(result: dict, system: str = "zendesk") -> dict:
    """
    Format pipeline result for specific ticketing system API.

    Args:
        result: Pipeline result dict
        system: Target system (zendesk, freshdesk, servicenow)

    Returns:
        Formatted payload for the specific system
    """
    classifier = result.get("classifier", {})
    priority = result.get("priority", {})
    emotion = result.get("emotion", {})
    quality = result.get("quality_checker", {})

    approved_draft = quality.get("approved_draft", "formal")
    drafts = result.get("drafter", {})
    response_body = drafts.get(f"{approved_draft}_draft", "Response pending")

    if system == "zendesk":
        return {
            "ticket": {
                "subject": f"[{classifier.get('category', 'General')}] {result.get('ticket_id', 'Unknown')}",
                "comment": {"body": response_body},
                "priority": {
                    "P1 Critical": "urgent",
                    "P2 High": "high",
                    "P3 Medium": "normal",
                    "P4 Low": "low"
                }.get(priority.get("priority", "P3 Medium"), "normal"),
                "tags": [
                    classifier.get("category", "").lower().replace(" ", "_"),
                    f"churn_{emotion.get('churn_risk_label', 'Low').lower()}",
                    "ai-triaged"
                ],
                "custom_fields": [
                    {"id": 360001, "value": emotion.get("churn_risk_score", 0)},
                    {"id": 360002, "value": priority.get("sla_hours", 24)}
                ]
            }
        }
    elif system == "freshdesk":
        return {
            "subject": f"[{classifier.get('category', 'General')}] {result.get('ticket_id', 'Unknown')}",
            "description": response_body,
            "priority": {
                "P1 Critical": 1,
                "P2 High": 2,
                "P3 Medium": 3,
                "P4 Low": 4
            }.get(priority.get("priority", "P3 Medium"), 3),
            "tags": [classifier.get("category", "").lower().replace(" ", "_")]
        }
    else:  # servicenow
        return {
            "short_description": classifier.get("subcategory", classifier.get("category", "Support Request")),
            "description": result.get("raw_text", ""),
            "urgency": priority.get("priority_level", 3),
            "comments": response_body
        }


if __name__ == "__main__":
    # Test with sample result
    test_result = {
        "ticket_id": "TKT-12345",
        "classifier": {"category": "Billing", "subcategory": "Billing > Duplicate Charge", "confidence": 92},
        "priority": {"priority": "P2 High", "priority_level": 2, "sla_hours": 4, "escalation_required": False},
        "emotion": {"sentiment": "frustrated", "churn_risk_score": 65, "churn_risk_label": "Medium", "is_vip": False},
        "quality_checker": {"approved_draft": "formal", "formal_scores": {"overall": 85}},
        "drafter": {"formal_draft": "Dear Customer...", "friendly_draft": "Hey there..."}
    }

    print("JSON Export:")
    print(export_json(test_result))

    print("\nCSV Export:")
    csv_bytes = export_csv([test_result])
    print(csv_bytes.decode('utf-8'))

    print("\nSimulated Push:")
    push_result = simulate_ticketing_push(test_result)
    print(json.dumps(push_result, indent=2))
