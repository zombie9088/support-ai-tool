"""
SupportAI - Customer Support AI Ticket Categorization & Response Suggestion Tool
Main Streamlit entry point with 6-agent pipeline orchestration.
"""

import os
import time
import random
import json
import re
from datetime import datetime

import streamlit as st
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import agents
from agents.preprocessor import preprocess_ticket
from agents.classifier import classify_ticket
from agents.priority import assign_priority
from agents.emotion import analyze_emotion
from agents.drafter import draft_response
from agents.quality_checker import check_quality

# Import utils
from utils.synthetic_data import generate_and_save
from utils.exporter import export_json, export_csv, simulate_ticketing_push
from utils.metrics import MetricsTracker

# Import components
from components.single_ticket_view import render_single_ticket_view
from components.batch_view import render_batch_results
from components.analytics_view import render_analytics_dashboard

# Page config
st.set_page_config(
    page_title="SupportAI — Ticket Intelligence",
    page_icon="🎫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        padding: 20px;
        color: white;
    }
    .priority-p1 { color: #FF4444; font-weight: bold; }
    .priority-p2 { color: #FFA500; font-weight: bold; }
    .priority-p3 { color: #FFD700; font-weight: bold; }
    .priority-p4 { color: #44AA44; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "results" not in st.session_state:
    st.session_state.results = None
if "batch_results" not in st.session_state:
    st.session_state.batch_results = []
if "metrics_tracker" not in st.session_state:
    st.session_state.metrics_tracker = MetricsTracker()
if "approved_result" not in st.session_state:
    st.session_state.approved_result = None


def run_pipeline(ticket_text: str, ticket_metadata: dict = None) -> dict:
    """
    Run the full 6-agent pipeline on a ticket.

    Args:
        ticket_text: Raw ticket text
        ticket_metadata: Optional metadata dict

    Returns:
        Complete results dict with all agent outputs and trace log
    """
    if ticket_metadata is None:
        ticket_metadata = {}

    trace_log = []
    results = {
        "ticket_id": ticket_metadata.get("ticket_id", f"MANUAL-{random.randint(10000, 99999)}"),
        "raw_text": ticket_text,
        "metadata": ticket_metadata
    }

    pipeline_start = time.time()

    try:
        # Agent 1: Preprocessor
        step_start = time.time()
        with st.status("🔍 Agent 1: Preprocessing...", expanded=True) as status:
            preprocessor_result = preprocess_ticket(ticket_text, ticket_metadata)
            step_duration = int((time.time() - step_start) * 1000)
            trace_log.append({
                "step": "Agent 1 - Preprocessor",
                "status": "complete" if "error" not in preprocessor_result else "error",
                "duration_ms": step_duration,
                "output_summary": f"PII: {preprocessor_result.get('pii_detected', False)}, Tone: {preprocessor_result.get('customer_tone', 'unknown')}"
            })
            results["preprocessor"] = preprocessor_result
            status.update(label=f"✅ Agent 1 Complete ({step_duration}ms)", state="complete")

        # Agent 2: Classifier
        step_start = time.time()
        with st.status("🏷️ Agent 2: Classifying...", expanded=True) as status:
            classifier_result = classify_ticket(preprocessor_result)
            step_duration = int((time.time() - step_start) * 1000)
            trace_log.append({
                "step": "Agent 2 - Classifier",
                "status": "complete" if "error" not in classifier_result else "error",
                "duration_ms": step_duration,
                "output_summary": f"Category: {classifier_result.get('category', 'Unknown')} ({classifier_result.get('confidence', 0)}%)"
            })
            results["classifier"] = classifier_result
            status.update(label=f"✅ Agent 2 Complete ({step_duration}ms)", state="complete")

        # Agent 3: Priority Scorer
        step_start = time.time()
        with st.status("⚡ Agent 3: Assigning Priority...", expanded=True) as status:
            priority_result = assign_priority(preprocessor_result, classifier_result)
            step_duration = int((time.time() - step_start) * 1000)
            trace_log.append({
                "step": "Agent 3 - Priority",
                "status": "complete" if "error" not in priority_result else "error",
                "duration_ms": step_duration,
                "output_summary": f"{priority_result.get('priority', 'Unknown')}, SLA: {priority_result.get('sla_hours')}hr"
            })
            results["priority"] = priority_result
            status.update(label=f"✅ Agent 3 Complete ({step_duration}ms)", state="complete")

        # Agent 4: Emotion Analyzer
        step_start = time.time()
        with st.status("💭 Agent 4: Analyzing Emotion...", expanded=True) as status:
            emotion_result = analyze_emotion(preprocessor_result, classifier_result, priority_result)
            step_duration = int((time.time() - step_start) * 1000)
            trace_log.append({
                "step": "Agent 4 - Emotion",
                "status": "complete" if "error" not in emotion_result else "error",
                "duration_ms": step_duration,
                "output_summary": f"Sentiment: {emotion_result.get('sentiment', 'unknown')}, Churn: {emotion_result.get('churn_risk_label', 'Low')}"
            })
            results["emotion"] = emotion_result
            status.update(label=f"✅ Agent 4 Complete ({step_duration}ms)", state="complete")

        # Agent 5: Response Drafter
        step_start = time.time()
        with st.status("📝 Agent 5: Drafting Response...", expanded=True) as status:
            all_outputs = {
                "preprocessor": preprocessor_result,
                "classifier": classifier_result,
                "priority": priority_result,
                "emotion": emotion_result
            }
            drafter_result = draft_response(all_outputs)
            step_duration = int((time.time() - step_start) * 1000)
            trace_log.append({
                "step": "Agent 5 - Drafter",
                "status": "complete" if "error" not in drafter_result else "error",
                "duration_ms": step_duration,
                "output_summary": f"Drafted {len(drafter_result.get('formal_draft', ''))} chars formal, {len(drafter_result.get('friendly_draft', ''))} chars friendly"
            })
            results["drafter"] = drafter_result
            status.update(label=f"✅ Agent 5 Complete ({step_duration}ms)", state="complete")

        # Agent 6: Quality Checker
        step_start = time.time()
        with st.status("✅ Agent 6: Checking Quality...", expanded=True) as status:
            quality_result = check_quality(all_outputs, drafter_result)
            step_duration = int((time.time() - step_start) * 1000)
            trace_log.append({
                "step": "Agent 6 - Quality Checker",
                "status": "complete" if "error" not in quality_result else "error",
                "duration_ms": step_duration,
                "output_summary": f"Approved: {quality_result.get('approved_draft', 'unknown')}, Flags: {len(quality_result.get('quality_flags', []))}"
            })
            results["quality_checker"] = quality_result
            status.update(label=f"✅ Agent 6 Complete ({step_duration}ms)", state="complete")

    except Exception as e:
        st.error(f"Pipeline error: {str(e)}")
        results["pipeline_error"] = str(e)

    pipeline_end = time.time()
    results["trace_log"] = trace_log
    results["total_time_ms"] = int((pipeline_end - pipeline_start) * 1000)
    results["completed_at"] = datetime.now().isoformat()

    return results


def load_demo_ticket() -> dict:
    """Load a random demo ticket from synthetic data."""
    synthetic_path = "data/synthetic_tickets.csv"

    if not os.path.exists(synthetic_path):
        generate_and_save(synthetic_path)

    df = pd.read_csv(synthetic_path)

    # Prioritize high churn risk tickets for demo
    high_churn = df[df["churn_risk_hint"] == "high"]
    if len(high_churn) > 0:
        row = high_churn.sample(1).iloc[0]
    else:
        row = df.sample(1).iloc[0]

    return {
        "ticket_id": row["ticket_id"],
        "customer_id": row["customer_id"],
        "channel": row["channel"],
        "text": f"{row['subject']}\n\n{row['body']}"
    }


# Sidebar
with st.sidebar:
    st.title("🎫 SupportAI")
    st.markdown("AI-Powered Support Operations")
    st.divider()

    # Model info
    st.markdown("**Model Configuration:**")
    st.code(f"Model: {os.getenv('model', 'Not configured')}")
    st.caption(f"Endpoint: {os.getenv('api_endpoint', 'Not configured')[:50]}...")

    st.divider()

    # Mode selector
    mode = st.radio(
        "Select Mode",
        ["Single Ticket", "Batch Upload", "Analytics Dashboard"],
        index=0
    )

    st.divider()

    # Confidence threshold slider
    confidence_threshold = st.slider(
        "Confidence Threshold",
        min_value=50,
        max_value=100,
        value=70,
        help="Tickets below this threshold will be flagged for human review"
    )

    st.divider()

    # Demo buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📋 Load Demo Ticket", use_container_width=True):
            demo = load_demo_ticket()
            st.session_state.demo_ticket = demo
            st.success("Demo ticket loaded!")
    with col2:
        if st.button("🔄 Generate New Data", use_container_width=True):
            generate_and_save("data/synthetic_tickets.csv")
            st.success("Synthetic data regenerated!")

    st.divider()

    # Export options (only shown if results exist)
    if st.session_state.results or st.session_state.batch_results:
        st.markdown("**Export:**")
        if st.session_state.results:
            json_export = export_json(st.session_state.results)
            st.download_button(
                "📥 Export JSON",
                json_export,
                f"ticket_{st.session_state.results.get('ticket_id', 'result')}.json",
                "application/json"
            )

        if st.session_state.batch_results:
            csv_export = export_csv(st.session_state.batch_results)
            st.download_button(
                "📥 Export CSV",
                csv_export,
                "batch_results.csv",
                "text/csv"
            )

        if st.button("🚀 Simulate Ticketing Push"):
            result_to_push = st.session_state.results if st.session_state.results else st.session_state.batch_results[-1]
            push_result = simulate_ticketing_push(result_to_push)
            st.success(f"✅ Pushed to {push_result['simulated_system']}: {push_result['ticket_number']}")


# Main content area
if mode == "Single Ticket":
    st.title("🎫 Single Ticket Analysis")
    st.markdown("Analyze individual support tickets with AI-powered triage")

    # Input section
    st.subheader("📥 Ticket Input")

    ticket_text = st.text_area(
        "Paste ticket text here...",
        height=150,
        placeholder="Paste the customer's support ticket here...",
        key="ticket_input"
    )

    # Optional fields (collapsible)
    with st.expander("📋 Optional Metadata"):
        col_meta1, col_meta2, col_meta3 = st.columns(3)
        with col_meta1:
            ticket_id = st.text_input("Ticket ID", placeholder="TKT-12345")
        with col_meta2:
            customer_id = st.text_input("Customer ID", placeholder="CUST-1234")
        with col_meta3:
            channel = st.selectbox("Channel", ["email", "chat", "web", "phone"])

    metadata = {}
    if ticket_id:
        metadata["ticket_id"] = ticket_id
    if customer_id:
        metadata["customer_id"] = customer_id
    if channel:
        metadata["channel"] = channel

    # Load demo ticket if available
    if "demo_ticket" in st.session_state and st.session_state.demo_ticket:
        demo = st.session_state.demo_ticket
        if not ticket_text:
            st.session_state.ticket_input = demo["text"]
            if "ticket_id" not in metadata:
                metadata["ticket_id"] = demo.get("ticket_id", "")
            st.rerun()

    # Analyze button
    col_analyze, col_space = st.columns([1, 4])
    with col_analyze:
        analyze_button = st.button("🚀 Analyze Ticket", type="primary", use_container_width=True)

    if analyze_button and ticket_text:
        # Initialize metrics tracker for session
        if "metrics_tracker" not in st.session_state:
            st.session_state.metrics_tracker = MetricsTracker()
            st.session_state.metrics_tracker.start_session()

        # Run pipeline
        with st.spinner("Running AI pipeline..."):
            result = run_pipeline(ticket_text, metadata)

        st.session_state.results = result
        st.session_state.metrics_tracker.record_ticket(result)

        # Show results
        render_single_ticket_view(result)

    elif st.session_state.results:
        # Show previous results
        render_single_ticket_view(st.session_state.results)

    elif not ticket_text:
        st.info("👆 Paste a ticket above or click 'Load Demo Ticket' in the sidebar")


elif mode == "Batch Upload":
    st.title("📦 Batch Processing")
    st.markdown("Process multiple tickets at once")

    # Initialize metrics if needed
    if "metrics_tracker" not in st.session_state:
        st.session_state.metrics_tracker = MetricsTracker()
        st.session_state.metrics_tracker.start_session()

    # Input section
    uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

    col_synthetic, col_process = st.columns(2)
    with col_synthetic:
        if st.button("📊 Use Synthetic Data (100 tickets)", use_container_width=True):
            st.session_state.use_synthetic = True
            st.success("Synthetic data selected!")

    if uploaded_file or st.session_state.get("use_synthetic"):
        if st.session_state.get("use_synthetic"):
            # Load synthetic data
            synthetic_path = "data/synthetic_tickets.csv"
            if not os.path.exists(synthetic_path):
                generate_and_save(synthetic_path)

            df = pd.read_csv(synthetic_path)
            st.session_state.current_df = df
        else:
            df = pd.read_csv(uploaded_file)
            st.session_state.current_df = df

        # Show preview
        st.markdown("**Preview (first 5 rows):**")
        st.dataframe(df.head())

        if st.button("⚡ Process All Tickets", type="primary"):
            st.session_state.batch_results = []
            progress_bar = st.progress(0)
            status_text = st.empty()

            total = len(df)

            for i, row in df.iterrows():
                ticket_text = f"{row.get('subject', '')}\n\n{row.get('body', '')}"
                metadata = {
                    "ticket_id": row.get("ticket_id", f"BATCH-{i}"),
                    "customer_id": row.get("customer_id", ""),
                    "channel": row.get("channel", "unknown")
                }

                result = run_pipeline(ticket_text, metadata)
                st.session_state.batch_results.append(result)
                st.session_state.metrics_tracker.record_ticket(result)

                progress_bar.progress((i + 1) / total)
                status_text.text(f"Processed {i + 1}/{total} tickets...")

            status_text.text("✅ All tickets processed!")
            st.success(f"Processed {total} tickets successfully!")

            # Render batch results
            render_batch_results(st.session_state.batch_results)

    elif st.session_state.batch_results:
        # Show previous results
        render_batch_results(st.session_state.batch_results)

    else:
        st.info("👆 Upload a CSV file or use synthetic data to begin batch processing")


elif mode == "Analytics Dashboard":
    st.title("📊 Analytics Dashboard")
    st.markdown("View aggregated metrics and insights")

    # Initialize metrics if needed
    if "metrics_tracker" not in st.session_state:
        st.session_state.metrics_tracker = MetricsTracker()
        st.session_state.metrics_tracker.start_session()

    # If we have batch results, add them to metrics
    if st.session_state.batch_results:
        for result in st.session_state.batch_results:
            st.session_state.metrics_tracker.record_ticket(result)

    render_analytics_dashboard(st.session_state.metrics_tracker)


# Footer
st.divider()
st.caption(f"SupportAI v1.0 | Model: {os.getenv('model', 'Not configured')} | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
