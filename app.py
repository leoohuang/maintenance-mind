"""Streamlit UI for MaintenanceMind."""
from __future__ import annotations

import streamlit as st

from agent.core import Agent, AgentStep
from agent.llm import client as llm_client
from agent.memory import load_memory, save_memory

st.set_page_config(
    page_title="MaintenanceMind",
    layout="wide",
    initial_sidebar_state="expanded",
)


def get_agent() -> Agent:
    if "agent" not in st.session_state:
        st.session_state.agent = Agent(verbose=False)
    return st.session_state.agent


def get_runs() -> list:
    if "runs" not in st.session_state:
        st.session_state.runs = []
    return st.session_state.runs


def render_step(step: AgentStep):
    """Render one agent trace step."""
    if step.kind == "thought":
        with st.chat_message("assistant"):
            st.markdown(f"*{step.content}*")
    elif step.kind == "tool_call":
        content = step.content
        with st.chat_message("assistant"):
            st.markdown(f"**Tool call:** `{content['name']}`")
            with st.expander("Arguments", expanded=False):
                st.json(content["arguments"])
    elif step.kind == "tool_result":
        tool_name = step.metadata.get("tool_name", "tool")
        result = step.content
        with st.chat_message("assistant"):
            if isinstance(result, dict) and "results" in result:
                count = result.get("count", len(result.get("results", [])))
                st.markdown(f"**Result from `{tool_name}`:** {count} items")
                with st.expander("Show details", expanded=False):
                    st.json(result)
            elif isinstance(result, dict) and "error" in result:
                st.error(f"Tool error: {result['error']}")
            else:
                with st.expander(f"Result from {tool_name}", expanded=False):
                    st.json(result)
    elif step.kind == "reflection":
        sufficiency = step.metadata.get("sufficiency", "?")
        confidence = step.metadata.get("confidence", 0.0)
        with st.chat_message("assistant"):
            st.markdown(
                f"**Reflection**: `{sufficiency}`, confidence `{confidence:.2f}`"
            )
            with st.expander("Reflection details", expanded=False):
                st.json(step.content)
    elif step.kind == "final":
        with st.chat_message("assistant"):
            st.markdown(step.content)


agent = get_agent()
with st.sidebar:
    st.title("MaintenanceMind")
    st.caption("Industrial maintenance investigation agent.")
    st.markdown(f"**LLM endpoint:** `{llm_client.base_url}`")
    st.markdown(f"**Model:** `{llm_client.model}`")
    st.divider()

    left, right = st.columns(2)
    if left.button("New session", use_container_width=True):
        agent.reset()
        st.session_state.runs = []
        st.rerun()
    if right.button("Clear memory", use_container_width=True):
        save_memory({"facts": [], "recent_issues": [], "preferences": {}})
        st.session_state.agent = Agent(verbose=False)
        st.session_state.runs = []
        st.rerun()

    with st.expander("Persistent memory", expanded=False):
        memory = load_memory()
        facts = memory.get("facts", [])
        if facts:
            st.markdown("**Facts**")
            for fact in facts:
                st.markdown(f"- {fact}")
        else:
            st.caption("No facts remembered yet.")
        recent_issues = memory.get("recent_issues", [])
        if recent_issues:
            st.markdown("**Recent issues**")
            for issue in recent_issues[-5:]:
                st.markdown(f"- {issue.get('date', '?')}: {issue.get('summary', '')}")

    with st.expander("Available tools", expanded=False):
        for name in agent.registry.names():
            tool = agent.registry.get(name)
            st.markdown(f"**`{name}`**")
            st.caption(tool.description)

st.title("MaintenanceMind")
st.caption(
    "Ask a maintenance question. The agent retrieves evidence from work orders, "
    "equipment manuals, and the web, then reflects on evidence sufficiency."
)

for previous_run in get_runs():
    with st.chat_message("user"):
        st.markdown(previous_run.question)
    for previous_step in previous_run.steps:
        render_step(previous_step)

if prompt := st.chat_input("Describe a maintenance issue..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.spinner("Investigating..."):
        run = agent.run(prompt)
    for step in run.steps:
        render_step(step)
    get_runs().append(run)
