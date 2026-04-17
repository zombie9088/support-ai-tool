"""
Metrics tracking for support ticket pipeline.
Handles time tracking, accuracy proxies, and efficiency calculations.
"""

import time
from datetime import datetime
from typing import Dict, List, Optional


class MetricsTracker:
    """Track pipeline metrics across multiple ticket processing runs."""

    def __init__(self):
        self.processing_times: List[float] = []
        self.confidence_scores: List[int] = []
        self.quality_scores: List[int] = []
        self.category_counts: Dict[str, int] = {}
        self.priority_counts: Dict[str, int] = {}
        self.churn_risk_counts: Dict[str, int] = {"High": 0, "Medium": 0, "Low": 0}
        self.sentiment_counts: Dict[str, int] = {}
        self.start_time: Optional[float] = None
        self.total_tickets: int = 0

    def start_session(self):
        """Mark session start time."""
        self.start_time = time.time()

    def record_ticket(self, result: dict):
        """
        Record metrics from a single processed ticket.

        Args:
            result: Complete pipeline result dict
        """
        self.total_tickets += 1

        # Processing time
        processing_time = result.get("total_time_ms", 0)
        self.processing_times.append(processing_time)

        # Confidence score
        confidence = result.get("classifier", {}).get("confidence", 0)
        self.confidence_scores.append(confidence)

        # Quality score
        quality = result.get("quality_checker", {})
        formal_overall = quality.get("formal_scores", {}).get("overall", 0)
        friendly_overall = quality.get("friendly_scores", {}).get("overall", 0)
        avg_quality = max(formal_overall, friendly_overall)
        self.quality_scores.append(avg_quality)

        # Category
        category = result.get("classifier", {}).get("category", "Unknown")
        self.category_counts[category] = self.category_counts.get(category, 0) + 1

        # Priority
        priority = result.get("priority", {}).get("priority", "Unknown")
        self.priority_counts[priority] = self.priority_counts.get(priority, 0) + 1

        # Churn risk
        churn_label = result.get("emotion", {}).get("churn_risk_label", "Low")
        if churn_label in self.churn_risk_counts:
            self.churn_risk_counts[churn_label] += 1

        # Sentiment
        sentiment = result.get("emotion", {}).get("sentiment", "unknown")
        self.sentiment_counts[sentiment] = self.sentiment_counts.get(sentiment, 0) + 1

    def get_summary(self) -> dict:
        """
        Get aggregated metrics summary.

        Returns:
            Summary dict with all aggregated metrics
        """
        session_duration = time.time() - self.start_time if self.start_time else 0

        # Calculate averages
        avg_processing_time = sum(self.processing_times) / len(self.processing_times) if self.processing_times else 0
        avg_confidence = sum(self.confidence_scores) / len(self.confidence_scores) if self.confidence_scores else 0
        avg_quality = sum(self.quality_scores) / len(self.quality_scores) if self.quality_scores else 0

        # Time saved calculation (assume 8 minutes manual per ticket)
        manual_time_minutes = self.total_tickets * 8
        actual_time_minutes = sum(self.processing_times) / 1000 / 60
        time_saved_minutes = manual_time_minutes - actual_time_minutes

        return {
            "total_tickets": self.total_tickets,
            "session_duration_seconds": round(session_duration, 2),
            "avg_processing_time_ms": round(avg_processing_time, 2),
            "avg_confidence_score": round(avg_confidence, 2),
            "avg_quality_score": round(avg_quality, 2),
            "category_distribution": self.category_counts,
            "priority_distribution": self.priority_counts,
            "churn_risk_distribution": self.churn_risk_counts,
            "sentiment_distribution": self.sentiment_counts,
            "estimated_manual_time_minutes": manual_time_minutes,
            "actual_processing_time_minutes": round(actual_time_minutes, 2),
            "time_saved_minutes": round(time_saved_minutes, 2),
            "efficiency_gain_percent": round((time_saved_minutes / manual_time_minutes * 100) if manual_time_minutes > 0 else 0, 1)
        }

    def reset(self):
        """Reset all metrics."""
        self.__init__()


def calculate_ticket_metrics(result: dict) -> dict:
    """
    Calculate derived metrics for a single ticket result.

    Args:
        result: Pipeline result dict

    Returns:
        Dict with calculated metrics
    """
    classifier = result.get("classifier", {})
    priority = result.get("priority", {})
    emotion = result.get("emotion", {})
    quality = result.get("quality_checker", {})

    # Classification accuracy proxy (based on confidence)
    confidence = classifier.get("confidence", 0)
    accuracy_proxy = "High" if confidence >= 80 else ("Medium" if confidence >= 60 else "Low")

    # Response relevance proxy (based on quality score)
    formal_overall = quality.get("formal_scores", {}).get("overall", 0)
    friendly_overall = quality.get("friendly_scores", {}).get("overall", 0)
    quality_score = max(formal_overall, friendly_overall)
    relevance_proxy = "High" if quality_score >= 80 else ("Medium" if quality_score >= 60 else "Low")

    # Handling time
    handling_time_ms = result.get("total_time_ms", 0)

    return {
        "classification_accuracy_proxy": accuracy_proxy,
        "response_relevance_proxy": relevance_proxy,
        "handling_time_ms": handling_time_ms,
        "confidence_score": confidence,
        "quality_score": quality_score,
        "needs_human_review": confidence < 60 or quality_score < 70
    }


def get_priority_color(priority: str) -> str:
    """Get color code for priority level."""
    colors = {
        "P1 Critical": "red",
        "P2 High": "orange",
        "P3 Medium": "yellow",
        "P4 Low": "green"
    }
    return colors.get(priority, "gray")


def get_churn_risk_color(label: str) -> str:
    """Get color code for churn risk level."""
    colors = {
        "High": "red",
        "Medium": "orange",
        "Low": "green"
    }
    return colors.get(label, "gray")


def get_sentiment_color(sentiment: str) -> str:
    """Get color code for sentiment."""
    colors = {
        "very_positive": "green",
        "positive": "lightgreen",
        "neutral": "gray",
        "negative": "orange",
        "very_negative": "red"
    }
    return colors.get(sentiment, "gray")


if __name__ == "__main__":
    # Test metrics tracker
    tracker = MetricsTracker()
    tracker.start_session()

    test_result = {
        "ticket_id": "TKT-12345",
        "total_time_ms": 2500,
        "classifier": {"category": "Billing", "confidence": 92},
        "priority": {"priority": "P2 High"},
        "emotion": {"churn_risk_label": "Medium", "sentiment": "frustrated"},
        "quality_checker": {"formal_scores": {"overall": 85}, "friendly_scores": {"overall": 78}}
    }

    tracker.record_ticket(test_result)
    print("Summary:", tracker.get_summary())

    ticket_metrics = calculate_ticket_metrics(test_result)
    print("Ticket Metrics:", ticket_metrics)
