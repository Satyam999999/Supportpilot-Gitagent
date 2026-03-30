from __future__ import annotations

from pathlib import Path

import streamlit as st

from support_agent import SupportPilotAgent


@st.cache_resource
def get_agent() -> SupportPilotAgent:
    project_root = Path(__file__).resolve().parents[1]
    return SupportPilotAgent(kb_path=project_root / "data" / "faq_kb.md")


st.set_page_config(page_title="SupportPilot Demo", page_icon="SP", layout="centered")
st.title("SupportPilot: Reliability and Safety Layer")
st.caption("Grounded support responses with confidence and escalation safeguards")

user_id = st.selectbox("User", ["demo-user", "trial-user", "unknown-user"], index=0)
query = st.text_input("Ask something")

if query:
    agent = get_agent()
    result = agent.ask(query, user_id=user_id)

    st.subheader("Response")
    st.write(result["answer"])

    st.subheader("Reliability")
    st.write(f"Confidence: {result['confidence']}")
    st.write(f"Reason: {result['confidence_reason']}")

    st.subheader("Safety")
    st.write(f"Escalate: {result['escalate']}")
    if result["escalation_summary"]:
        st.warning(result["escalation_summary"])

    st.subheader("Trace")
    st.write(f"Rewritten query: {result['rewritten_query']}")
    if result["citations"]:
        st.write("Citations:")
        for citation in result["citations"]:
            st.write(f"- {citation}")

    if result["tool_data"]:
        st.info(f"Tool output: {result['tool_data']}")
