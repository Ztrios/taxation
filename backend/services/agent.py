from typing import TypedDict, Optional, Literal

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from config import settings
from services.chat import chat_service


class AgentState(TypedDict, total=False):
    user_query: str
    session_id: str
    is_relevant: bool
    final_response: str
    include_rag: bool


def _build_filter_llm() -> ChatOpenAI:
    """
    Build the LLM client for the filter step using the existing OpenAI-compatible
    (vLLM) endpoint configuration.
    """
    return ChatOpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        model=settings.filter_model_name,
        temperature=0,
        # Constrain output to keep cost tiny on OpenRouter and avoid 402 errors.
        max_tokens=8,
    )


def filter_node(state: AgentState) -> AgentState:
    """
    Classify whether the query is strictly about tax-related topics.
    Returns state with `is_relevant` set to True/False.
    """
    llm = _build_filter_llm()
    system_prompt = (
        "You are a strict classifier for TAX-related questions.\n"
        "Answer with EXACTLY one token: YES or NO. No punctuation or extra text.\n"
        "If the question mentions tax/taxes/taxation/tax credit/tax deduction/"
        "tax filing/tax compliance/tax policy, respond YES even if the wording is short.\n\n"
        "Examples:\n"
        "Q: How do I file my federal tax return? -> YES\n"
        "Q: What is a tax credit for education expenses? -> YES\n"
        "Q: Tell me about income tax deductions. -> YES\n"
        "Q: what is tax? -> YES\n"
        "Q: Define taxation. -> YES\n"
        "Q: What is the weather today? -> NO\n"
        "Q: Explain quantum mechanics. -> NO\n"
    )
    user_prompt = state["user_query"]
    try:
        print(f"[Filter] invoking model={settings.filter_model_name}")
        result = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
        verdict = (result.content or "").strip().upper()
        is_relevant = verdict.startswith("Y")
    except Exception as exc:
        # Log and default to refusal path on errors to avoid crashing the graph.
        print(f"[Filter] error during filter call: {exc}")
        verdict = "ERROR"
        is_relevant = False

    print(f"[Filter] verdict={verdict!r}, is_relevant={is_relevant}")
    return {**state, "is_relevant": is_relevant}


def chat_node(state: AgentState) -> AgentState:
    """
    Pass the query to the existing chat service (which handles RAG + history).
    """
    response = chat_service.chat(
        session_id=state["session_id"],
        user_message=state["user_query"],
        include_rag=state.get("include_rag", True),
    )
    return {**state, "final_response": response}


def refusal_node(state: AgentState) -> AgentState:
    """
    Return a polite refusal when the query is not tax-related.
    """
    refusal = (
        "I’m designed to answer tax-related questions only. "
        "Please ask a question about taxes."
    )
    return {**state, "final_response": refusal}


def build_agent_graph():
    """
    Construct the LangGraph workflow:
    START -> filter -> (chat or refusal) -> END
    """
    workflow = StateGraph(AgentState)
    workflow.add_node("filter", filter_node)
    workflow.add_node("chat", chat_node)
    workflow.add_node("refusal", refusal_node)

    def route_decision(state: AgentState) -> Literal["chat", "refusal"]:
        return "chat" if state.get("is_relevant") else "refusal"

    workflow.set_entry_point("filter")
    workflow.add_conditional_edges(
        "filter",
        route_decision,
        {
            "chat": "chat",
            "refusal": "refusal",
        },
    )
    workflow.add_edge("chat", END)
    workflow.add_edge("refusal", END)
    return workflow.compile()


# Singleton compiled graph for reuse
tax_agent_graph = build_agent_graph()

