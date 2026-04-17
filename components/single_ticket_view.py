"""
Single Ticket View Component
Displays detailed results for a single processed ticket.
"""

import streamlit as st
import json
from typing import Dict


def get_priority_color(priority: str) -> str:
    """Get color and emoji for priority level."""
    colors = {
        "P1 Critical": "🔴 red",
        "P2 High": "🟠 orange",
        "P3 Medium": "🟡 yellow",
        "P4 Low": "🟢 green"
    }
    return colors.get(priority, "⚪ gray")


def get_churn_color(label: str) -> str:
    """Get color for churn risk level."""
    colors = {
        "High": "red",
        "Medium": "orange",
        "Low": "green"
    }
    return colors.get(label, "gray")


def get_sentiment_emoji(sentiment: str) -> str:
    """Get emoji for sentiment."""
    emojis = {
        "very_positive": "😊",
        "positive": "🙂",
        "neutral": "😐",
        "negative": "😟",
        "very_negative": "😠"
    }
    return emojis.get(sentiment, "😐")


def render_single_ticket_view(result: dict):
    """
    Render the single ticket results view.

    Args:
        result: Complete pipeline result dict
    """
    st.header("🎫 Ticket Analysis Results")

    # Extract key data
    classifier = result.get("classifier", {})
    priority = result.get("priority", {})
    emotion = result.get("emotion", {})
    drafter = result.get("drafter", {})
    quality = result.get("quality_checker", {})
    preprocessor = result.get("preprocessor", {})

    # Row 1: 4 metric columns
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        category = classifier.get("category", "Unknown")
        confidence = classifier.get("confidence", 0)
        st.metric(
            label="Category",
            value=category,
            delta=f"{confidence}% confidence" if confidence >= 70 else f"⚠️ {confidence}%",
            delta_color="normal" if confidence >= 70 else "inverse"
        )

    with col2:
        priority_val = priority.get("priority", "Unknown")
        priority_color = get_priority_color(priority_val)
        st.markdown(f"**Priority**")
        st.markdown(f"<span style='color: {priority_color.split()[1]}; font-size: 1.2em;'>{priority_val}</span>", unsafe_allow_html=True)

    with col3:
        churn_label = emotion.get("churn_risk_label", "Low")
        churn_score = emotion.get("churn_risk_score", 0)
        st.metric(
            label="Churn Risk",
            value=churn_label,
            delta=f"{churn_score}/100",
            delta_color="inverse" if churn_label == "High" else "normal"
        )

    with col4:
        total_time = result.get("total_time_ms", 0)
        st.metric(
            label="Processing Time",
            value=f"{total_time}ms",
            delta=f"{total_time/1000:.2f}s",
            delta_color="normal"
        )

    st.divider()

    # Row 2: Churn, Emotion, SLA panels
    col_churn, col_emotion, col_sla = st.columns(3)

    with col_churn:
        st.subheader("📉 Churn Risk")
        churn_score = emotion.get("churn_risk_score", 0)
        churn_label = emotion.get("churn_risk_label", "Low")
        churn_color = get_churn_color(churn_label)

        # Progress bar for churn risk
        st.progress(churn_score / 100)
        st.caption(f"Score: {churn_score}/100")

        # Churn signals
        churn_signals = emotion.get("churn_signals", [])
        if churn_signals:
            st.markdown("**Detected Signals:**")
            for signal in churn_signals[:3]:
                st.markdown(f"⚠️ `{signal}`")

        # Retention action
        retention_action = emotion.get("retention_action")
        if retention_action:
            st.info(f"💡 Recommended: **{retention_action.replace('_', ' ').title()}**")

    with col_emotion:
        st.subheader("💭 Emotion Analysis")
        sentiment = emotion.get("sentiment", "neutral")
        frustration = emotion.get("frustration_score", 0)
        is_vip = emotion.get("is_vip", False)

        st.markdown(f"**Sentiment:** {get_sentiment_emoji(sentiment)} {sentiment.replace('_', ' ').title()}")

        # Frustration gauge (simple visualization)
        st.markdown(f"**Frustration Level:**")
        st.progress(frustration / 100)
        st.caption(f"{frustration}/100")

        if is_vip:
            st.success("🌟 **VIP Customer**")

    with col_sla:
        st.subheader("⏱️ SLA & Escalation")
        sla_hours = priority.get("sla_hours", 24)
        escalation = priority.get("escalation_required", False)
        escalation_reason = priority.get("escalation_reason")

        st.markdown(f"**SLA Target:** {sla_hours} hours")

        if escalation:
            st.error(f"🚨 **Escalation Required**")
            if escalation_reason:
                st.caption(f"Reason: {escalation_reason}")
        else:
            st.success("✅ Standard Handling")

        # Priority reasoning
        priority_reasoning = priority.get("priority_reasoning", "")
        if priority_reasoning:
            st.caption(f"_{priority_reasoning}_")

    st.divider()

    # Row 3: Response drafts
    st.header("📝 Response Drafts")

    tab_formal, tab_friendly = st.tabs(["📋 Formal Draft", "💬 Friendly Draft"])

    formal_draft = drafter.get("formal_draft", "")
    friendly_draft = drafter.get("friendly_draft", "")
    recommended_tone = drafter.get("recommended_tone", "formal")
    tone_reason = drafter.get("tone_recommendation_reason", "")
    approved_draft = quality.get("approved_draft", "formal")

    with tab_formal:
        st.markdown("**Formal Response:**")
        formal_edited = st.text_area(
            "Edit formal draft",
            value=formal_draft,
            height=200,
            key="formal_draft_edit",
            label_visibility="collapsed"
        )

        # Quality scores for formal
        formal_scores = quality.get("formal_scores", {})
        col_r, col_e, col_c, col_p = st.columns(4)
        col_r.metric("Relevance", formal_scores.get("relevance", 0))
        col_e.metric("Empathy", formal_scores.get("empathy", 0))
        col_c.metric("Completeness", formal_scores.get("completeness", 0))
        col_p.metric("Professionalism", formal_scores.get("professionalism", 0))

        if recommended_tone == "formal":
            st.success(f"⭐ Recommended Tone: {tone_reason}")

        st.code(formal_edited, language="text")

        if st.button("📋 Copy Formal", key="copy_formal"):
            st.toast("Formal draft copied to clipboard!")

    with tab_friendly:
        st.markdown("**Friendly Response:**")
        friendly_edited = st.text_area(
            "Edit friendly draft",
            value=friendly_draft,
            height=200,
            key="friendly_draft_edit",
            label_visibility="collapsed"
        )

        # Quality scores for friendly
        friendly_scores = quality.get("friendly_scores", {})
        col_r, col_e, col_c, col_p = st.columns(4)
        col_r.metric("Relevance", friendly_scores.get("relevance", 0))
        col_e.metric("Empathy", friendly_scores.get("empathy", 0))
        col_c.metric("Completeness", friendly_scores.get("completeness", 0))
        col_p.metric("Professionalism", friendly_scores.get("professionalism", 0))

        if recommended_tone == "friendly":
            st.success(f"⭐ Recommended Tone: {tone_reason}")

        st.code(friendly_edited, language="text")

        if st.button("📋 Copy Friendly", key="copy_friendly"):
            st.toast("Friendly draft copied to clipboard!")

    # Quality flags
    quality_flags = quality.get("quality_flags", [])
    if quality_flags:
        st.warning(f"⚠️ Quality Flags: {', '.join(quality_flags)}")

    # Approve button
    col_approve, col_space = st.columns([1, 4])
    with col_approve:
        if st.button("✅ Approve & Export", type="primary"):
            st.session_state["approved_result"] = result
            st.session_state["approved_draft_content"] = formal_edited if recommended_tone == "formal" else friendly_edited
            st.success("Draft approved! Ready for export.")

    st.divider()

    # Agent Reasoning Trace (expandable)
    with st.expander("🔍 View Agent Reasoning Trace"):
        trace_log = result.get("trace_log", [])

        for i, step in enumerate(trace_log):
            step_name = step.get("step", f"Step {i+1}")
            status = step.get("status", "unknown")
            duration = step.get("duration_ms", 0)

            col_icon, col_info = st.columns([0.1, 0.9])
            with col_icon:
                st.markdown("✅" if status == "complete" else "⚠️")
            with col_info:
                st.markdown(f"**{step_name}** - {duration}ms")

        # Show full JSON outputs per agent
        st.markdown("**Full Agent Outputs:**")

        tabs = st.tabs(["Preprocessor", "Classifier", "Priority", "Emotion", "Drafter", "Quality"])

        with tabs[0]:
            st.json(preprocessor)
        with tabs[1]:
            st.json(classifier)
        with tabs[2]:
            st.json(priority)
        with tabs[3]:
            st.json(emotion)
        with tabs[4]:
            st.json(drafter)
        with tabs[5]:
            st.json(quality)
