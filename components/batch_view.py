"""
Batch View Component
Displays batch processing results with table, heatmap, and leaderboard.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict


def get_priority_color(priority: str) -> str:
    """Get background color for priority."""
    colors = {
        "P1 Critical": "rgba(255, 0, 0, 0.2)",
        "P2 High": "rgba(255, 165, 0, 0.2)",
        "P3 Medium": "rgba(255, 255, 0, 0.2)",
        "P4 Low": "rgba(0, 255, 0, 0.2)"
    }
    return colors.get(priority, "rgba(128, 128, 128, 0.2)")


def render_batch_results(results_list: List[dict]):
    """
    Render batch processing results with table, heatmap, and leaderboard.

    Args:
        results_list: List of pipeline results
    """
    st.header("📊 Batch Processing Results")

    if not results_list:
        st.info("No batch results available. Upload a CSV or use synthetic data to process tickets.")
        return

    # Flatten results for display
    flat_data = []
    for result in results_list:
        classifier = result.get("classifier", {})
        priority = result.get("priority", {})
        emotion = result.get("emotion", {})
        quality = result.get("quality_checker", {})

        flat_data.append({
            "ticket_id": result.get("ticket_id", "Unknown"),
            "category": classifier.get("category", "Unknown"),
            "priority": priority.get("priority", "Unknown"),
            "priority_level": priority.get("priority_level", 3),
            "churn_risk_label": emotion.get("churn_risk_label", "Low"),
            "churn_risk_score": emotion.get("churn_risk_score", 0),
            "confidence": classifier.get("confidence", 0),
            "sentiment": emotion.get("sentiment", "neutral"),
            "processing_time_ms": result.get("total_time_ms", 0),
            "quality_score": max(
                quality.get("formal_scores", {}).get("overall", 0),
                quality.get("friendly_scores", {}).get("overall", 0)
            )
        })

    df = pd.DataFrame(flat_data)

    # Results table with styling
    st.subheader("📋 Results Table")

    # Apply background gradient by priority
    def priority_style(val):
        colors = {
            "P1 Critical": "background-color: rgba(255, 0, 0, 0.15)",
            "P2 High": "background-color: rgba(255, 165, 0, 0.15)",
            "P3 Medium": "background-color: rgba(255, 255, 0, 0.15)",
            "P4 Low": "background-color: rgba(0, 255, 0, 0.15)"
        }
        return colors.get(val, "")

    styled_df = df.style.applymap(priority_style, subset=["priority"])
    st.dataframe(styled_df, use_container_width=True, height=300)

    st.divider()

    # Sentiment Heatmap
    st.subheader("🔥 Sentiment Heatmap")

    # Prepare data for heatmap
    heatmap_data = df.groupby(["category", "churn_risk_label"]).agg({
        "frustration_score" if "frustration_score" in df.columns else "churn_risk_score": "mean",
        "ticket_id": "count"
    }).reset_index()

    if len(heatmap_data) > 0:
        fig = px.density_heatmap(
            df,
            x="category",
            y="churn_risk_score",
            z="churn_risk_score",
            color_continuous_scale="RdYlGn_r",
            title="Churn Risk by Category",
            height=400
        )
        fig.update_layout(xaxis_title="Category", yaxis_title="Churn Risk Score")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Not enough data for heatmap visualization.")

    st.divider()

    # Churn Risk Leaderboard
    st.subheader("⚠️ Top Churn Risks")

    top_churn = df.nlargest(5, "churn_risk_score")

    for _, row in top_churn.iterrows():
        with st.container():
            col_id, col_score, col_signals, col_action = st.columns([2, 1, 2, 2])

            with col_id:
                st.markdown(f"**{row['ticket_id']}**")
                st.caption(f"Category: {row['category']}")

            with col_score:
                risk_color = "red" if row["churn_risk_score"] > 70 else ("orange" if row["churn_risk_score"] > 40 else "green")
                st.markdown(f"<span style='color: {risk_color}; font-size: 1.2em;'>{row['churn_risk_score']}/100</span>", unsafe_allow_html=True)
                st.caption("Churn Score")

            with col_signals:
                st.caption("Risk Factors:")
                st.caption(f"Sentiment: {row['sentiment']}")
                st.caption(f"Confidence: {row['confidence']}%")

            with col_action:
                if row["churn_risk_score"] > 60:
                    st.warning("💡 Retention action recommended")
                else:
                    st.success("✅ Standard handling OK")

            st.divider()

    st.divider()

    # Batch Summary Metrics
    st.subheader("📈 Batch Summary")

    col1, col2, col3, col4, col5 = st.columns(5)

    total_tickets = len(results_list)
    avg_confidence = df["confidence"].mean()
    avg_quality = df["quality_score"].mean()
    avg_processing_time = df["processing_time_ms"].mean()
    estimated_time_saved = total_tickets * 8 - (sum(df["processing_time_ms"]) / 1000 / 60)

    col1.metric("Total Processed", total_tickets)
    col2.metric("Avg Confidence", f"{avg_confidence:.1f}%")
    col3.metric("Avg Quality", f"{avg_quality:.1f}%")
    col4.metric("Avg Processing", f"{avg_processing_time:.0f}ms")
    col5.metric("Time Saved", f"{estimated_time_saved:.1f} min")

    # Distribution charts
    col_cat, col_pri = st.columns(2)

    with col_cat:
        # Category distribution (donut chart)
        category_counts = df["category"].value_counts().reset_index()
        category_counts.columns = ["Category", "Count"]

        fig = px.pie(
            category_counts,
            values="Count",
            names="Category",
            title="Category Distribution",
            hole=0.4
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_pri:
        # Priority distribution (bar chart)
        priority_counts = df["priority"].value_counts().reset_index()
        priority_counts.columns = ["Priority", "Count"]

        # Sort by priority level
        priority_order = ["P1 Critical", "P2 High", "P3 Medium", "P4 Low"]
        priority_counts["Priority"] = pd.Categorical(priority_counts["Priority"], categories=priority_order, ordered=True)
        priority_counts = priority_counts.sort_values("Priority")

        fig = px.bar(
            priority_counts,
            x="Priority",
            y="Count",
            title="Priority Distribution",
            color="Priority",
            color_discrete_map={
                "P1 Critical": "red",
                "P2 High": "orange",
                "P3 Medium": "yellow",
                "P4 Low": "green"
            }
        )
        st.plotly_chart(fig, use_container_width=True)

    # Confidence histogram
    st.subheader("📊 Confidence Score Distribution")
    fig = px.histogram(
        df,
        x="confidence",
        nbins=20,
        title="Confidence Score Histogram",
        labels={"confidence": "Confidence Score"}
    )
    fig.update_layout(xaxis_title="Confidence Score", yaxis_title="Number of Tickets")
    st.plotly_chart(fig, use_container_width=True)
