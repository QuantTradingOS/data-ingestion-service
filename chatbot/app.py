"""
QuantTradingOS Chatbot — Streamlit UI + LangGraph ReAct agent with MCP tools.

Run: streamlit run app.py

Requires: OPENAI_API_KEY in env or config/.env.
Orchestrator and data-ingestion-service (and optionally MCP server URL if using SSE)
must be running for the MCP tools to work. The app spawns the MCP server via stdio by default.
"""

from __future__ import annotations

import asyncio
import os
import sys
import traceback
from pathlib import Path


def _unwrap_error(e: BaseException) -> str:
    """Get the root cause message and type for clearer errors."""
    chain = []
    current = e
    while current:
        chain.append(f"{type(current).__name__}: {current}")
        current = getattr(current, "__cause__", None) or getattr(current, "__context__", None)
    if len(chain) > 1:
        return chain[-1]  # root cause last
    return str(e)

# Load .env from config/
_config_dir = Path(__file__).resolve().parent / "config"
_env_file = _config_dir / ".env"
if _env_file.exists():
    from dotenv import load_dotenv
    load_dotenv(_env_file)

import streamlit as st
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage

# MCP client (async) — we'll call it from sync context
def get_mcp_tools():
    """Load tools from QuantTradingOS MCP server via stdio. Runs async in sync context."""
    async def _get():
        from langchain_mcp_adapters.client import MultiServerMCPClient
        mcp_server_dir = Path(__file__).resolve().parent.parent / "mcp-server"
        from langchain_mcp_adapters.sessions import StdioConnection
        args_str = os.environ.get("MCP_SERVER_ARGS", "-m,qtos_mcp.server")
        args_list = [a.strip() for a in args_str.split(",") if a.strip()]
        # Use same Python as this process so MCP server gets 3.10+ (mcp package requirement)
        conn: StdioConnection = {
            "command": os.environ.get("MCP_SERVER_COMMAND", sys.executable),
            "args": args_list if args_list else ["-m", "qtos_mcp.server"],
            "transport": "stdio",
            "cwd": str(os.environ.get("MCP_SERVER_CWD", mcp_server_dir)),
        }
        client = MultiServerMCPClient({
            "quant-trading-os": conn,
        })
        return await client.get_tools()
    return asyncio.run(_get())


def get_agent():
    """Build LangGraph ReAct agent with MCP tools."""
    if "agent" in st.session_state:
        return st.session_state.agent
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        st.error("Set OPENAI_API_KEY in config/.env or Streamlit secrets.")
        return None
    try:
        tools = get_mcp_tools()
    except BaseExceptionGroup as e:
        sub = e.exceptions[0] if e.exceptions else e
        detail = _unwrap_error(sub) if isinstance(sub, BaseException) else str(sub)
        st.error(f"Failed to load MCP tools: {detail}")
        return None
    except Exception as e:
        detail = _unwrap_error(e)
        st.error(f"Failed to load MCP tools: {detail}")
        with st.expander("Full traceback"):
            st.code(traceback.format_exc())
        return None
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=api_key)
    system = """You are a helpful assistant for QuantTradingOS. You can run backtests, fetch prices, news, and insider data, and run the pipeline (run_decision). Use the tools when the user asks for data or actions. Be concise and accurate."""
    graph = create_react_agent(llm, tools, prompt=system)
    st.session_state.agent = graph
    return graph


def main():
    st.set_page_config(page_title="QuantTradingOS Chatbot", page_icon="📈")
    st.title("QuantTradingOS Chatbot")
    st.caption("Ask for backtests, prices, news, insider data, or to run the pipeline. Uses MCP tools.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask about backtests, prices, news, or run the pipeline..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        graph = get_agent()
        if graph is None:
            with st.chat_message("assistant"):
                st.markdown("Configure OPENAI_API_KEY and ensure MCP tools load. See README.")
            st.session_state.messages.append({"role": "assistant", "content": "Configuration error."})
            return

        # Build message list for LangGraph (full history + new user message)
        messages = []
        for m in st.session_state.messages:
            if m["role"] == "user":
                messages.append(HumanMessage(content=m["content"]))
            else:
                messages.append(AIMessage(content=m["content"]))

        with st.chat_message("assistant"):
            try:
                # Use ainvoke so MCP tools (async-only) are supported
                result = asyncio.run(graph.ainvoke({"messages": messages}))
                # Last message is the final AI response
                out_messages = result.get("messages", [])
                if not out_messages:
                    reply = str(result)
                else:
                    last = out_messages[-1].content
                    if isinstance(last, list):
                        reply = last[0].get("text", str(last)) if last else str(result)
                    else:
                        reply = last or str(result)
            except Exception as e:
                reply = f"Error: {e}"
            st.markdown(reply)

        st.session_state.messages.append({"role": "assistant", "content": reply})

    if st.sidebar.button("Clear chat"):
        st.session_state.messages = []
        if "agent" in st.session_state:
            del st.session_state.agent
        st.rerun()


if __name__ == "__main__":
    main()
