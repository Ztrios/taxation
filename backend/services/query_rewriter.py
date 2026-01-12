"""
Query Rewriter Agent using LangGraph.

Transforms vague user queries into precise tax-specific search terms
before RAG retrieval to improve document matching.
"""

from typing import TypedDict, Annotated, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
import operator

from config import settings


# Define the agent state
class AgentState(TypedDict):
    """State for the query rewriter agent."""
    original_query: str
    rewritten_queries: Annotated[List[str], operator.add]
    context_history: str  # Optional: last few messages for context
    final_output: List[str]


class QueryRewriterAgent:
    """
    LangGraph-based agent that rewrites user queries into better search terms.
    
    Workflow:
    1. Analyze user query for vagueness/ambiguity
    2. Generate 2-3 alternative phrasings with tax-specific terminology
    3. Return list of rewritten queries for RAG search
    """
    
    def __init__(self):
        """Initialize the query rewriter agent."""
        # Model fallback chain - same as chat service
        self.model_candidates = [
            settings.model_name,
            "qwen/qwen-2.5-7b-instruct",
            "qwen/qwen3-4b:free",
        ]
        
        # Try to initialize with first available model
        self.llm = None
        self._init_llm()
        
        # System prompt for query expansion - optimized for RAG accuracy
        self.system_prompt = """You are an expert tax query expansion specialist. Your task is to transform user questions into detailed, comprehensive queries that will effectively retrieve relevant tax documents from a vector database.

CRITICAL REQUIREMENTS:
1. Generate exactly 3 alternative expansions - no more, no less
2. Each expansion must be a complete, grammatically correct question
3. Cover different aspects and interpretations of the user's intent
4. Include specific tax terminology and legal concepts
5. Make all implicit assumptions explicit
6. Add relevant context about eligibility, documentation, calculations, and limits

EXPANSION STRATEGY:
- Query 1: Focus on WHAT can be claimed/deducted and the basic requirements
- Query 2: Focus on HOW to calculate, document, and report it
- Query 3: Focus on ELIGIBILITY criteria, limits, and special conditions

FORMAT RULES:
- Return ONLY numbered questions (1., 2., 3.)
- Each question should be 20-40 words long
- Use proper punctuation and capitalization
- Include specific examples in parentheses when relevant
- Avoid vague terms - be explicit and precise

EXAMPLES:

Input: "Can I deduct my car?"
1. What vehicle-related expenses (fuel, maintenance, insurance, depreciation, registration fees) can I deduct on my tax return if I use my car for business purposes, and what percentage of business use is required?
2. How do I calculate and document the vehicle expense deduction using either the standard mileage rate or actual expense method, and what records (mileage logs, receipts) must I maintain for IRS compliance?
3. Am I eligible to claim automobile deductions if I am self-employed versus an employee, and what are the annual limits or restrictions on luxury vehicle depreciation under Section 280F?

Input: "What about donations?"
1. What types of charitable donations (cash, property, securities, goods) can I deduct from my taxable income, and what is the maximum percentage of my adjusted gross income (AGI) that qualifies for deduction?
2. How do I properly document charitable contributions for tax purposes, including what receipts, acknowledgment letters, and appraisals are required for different donation amounts and types?
3. Am I eligible to deduct charitable contributions if I take the standard deduction versus itemizing, and are there carryover provisions if my donations exceed the annual AGI limit?

Input: "Home office deduction"
1. What expenses related to my home office (rent, mortgage interest, utilities, internet, insurance, repairs) can I deduct if I use a portion of my home exclusively and regularly for business activities?
2. How do I calculate the home office deduction using either the simplified method ($5 per square foot) or the actual expense method, and what percentage of my home qualifies as dedicated business space?
3. Am I eligible for the home office deduction if I am an employee working remotely versus self-employed, and what IRS rules determine whether my home office meets the "principal place of business" requirement?

Input: "Mortgage interest"
1. What types of mortgage interest (primary residence, second home, refinanced loans, home equity loans) are tax-deductible, and what is the maximum loan amount ($750,000 for loans after 2017) that qualifies for the deduction?
2. How do I claim the mortgage interest deduction on my tax return using Form 1040 Schedule A, and what documentation (Form 1098 from lender) do I need to substantiate the deduction amount?
3. Am I required to itemize deductions to claim mortgage interest, and does it make financial sense compared to taking the standard deduction ($13,850 for single filers in 2023)?

NOW PROCESS THE USER'S QUERY:
Return exactly 3 numbered questions following the format above."""

        # Build the LangGraph workflow
        self.graph = self._build_graph()
    
    def _init_llm(self):
        """Initialize LLM with fallback support and optimized settings."""
        default_headers = {
            "HTTP-Referer": "http://localhost",
            "X-Title": "taxation-chatbot-rewriter",
        }
        
        for model in self.model_candidates:
            try:
                self.llm = ChatOpenAI(
                    model=model,
                    api_key=settings.openai_api_key,
                    base_url=settings.openai_base_url,
                    temperature=0.2,  # Lower temp for more consistent, accurate rewrites
                    max_tokens=500,   # Limit token usage per rewrite
                    default_headers=default_headers,
                )
                # Test the model with a simple call
                self.llm.invoke([HumanMessage(content="test")])
                print(f"Query rewriter initialized with model: {model}")
                break
            except Exception as e:
                if "No endpoints found for" in str(e):
                    print(f"Model {model} not available, trying next...")
                    continue
                # For other errors, still try to use this model
                self.llm = ChatOpenAI(
                    model=model,
                    api_key=settings.openai_api_key,
                    base_url=settings.openai_base_url,
                    temperature=0.2,
                    max_tokens=500,
                    default_headers=default_headers,
                )
                break
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state graph for query rewriting."""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("rewrite", self._rewrite_query)
        workflow.add_node("format_output", self._format_output)
        
        # Define edges
        workflow.set_entry_point("rewrite")
        workflow.add_edge("rewrite", "format_output")
        workflow.add_edge("format_output", END)
        
        return workflow.compile()
    
    def _rewrite_query(self, state: AgentState) -> AgentState:
        """Rewrite the user query using the LLM with improved accuracy."""
        original = state["original_query"]
        context = state.get("context_history", "")
        
        # Skip rewriting for very short or single-word queries
        if len(original.split()) <= 2:
            print(f"Query too short for rewriting: '{original}'")
            state["rewritten_queries"] = [original]
            return state
        
        # Build prompt with context if available
        user_prompt = f"User query: {original}"
        if context:
            user_prompt = f"Conversation context:\n{context}\n\nCurrent query: {original}"
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=user_prompt),
        ]
        
        try:
            response = self.llm.invoke(messages)
            content = response.content.strip()
            
            # Parse the numbered list into separate queries
            queries = self._parse_queries(content)
            
            # Validation: Ensure we got quality results
            if not queries or len(queries) < 2:
                print(f"Query rewriting produced insufficient results. Using original.")
                state["rewritten_queries"] = [original]
            else:
                # Add original query as fallback if we only got 1-2 rewrites
                if len(queries) < 3:
                    queries.append(original)
                state["rewritten_queries"] = queries[:3]  # Ensure max 3
            
        except Exception as e:
            print(f"Query rewriter error: {e}")
            # Fallback: use original query
            state["rewritten_queries"] = [original]
        
        return state
    
    def _parse_queries(self, content: str) -> List[str]:
        """Parse LLM response into a list of queries with improved accuracy."""
        queries = []
        lines = content.strip().split("\n")
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Remove numbering patterns: "1.", "1)", "1 -", "1:", etc.
            # Also handles: "Query 1:", "Question 1.", etc.
            import re
            cleaned = re.sub(r'^(Query\s*|Question\s*|Expansion\s*)?[\d]+[\.\)\:\-]\s*', '', line, flags=re.IGNORECASE)
            cleaned = cleaned.strip()
            
            # Only accept substantial questions (at least 15 words)
            word_count = len(cleaned.split())
            if cleaned and word_count >= 15 and cleaned.endswith('?'):
                queries.append(cleaned)
        
        # Quality check: Ensure we have exactly 3 queries
        if len(queries) < 3:
            print(f"Warning: Only {len(queries)} queries parsed. Expected 3.")
            # If we got fewer than 3, pad with the original or use what we have
            if len(queries) == 0:
                return []  # Will fallback to original query
        elif len(queries) > 3:
            # Take only the first 3 best ones
            queries = queries[:3]
        
        return queries
    
    def _format_output(self, state: AgentState) -> AgentState:
        """Format final output."""
        state["final_output"] = state["rewritten_queries"]
        return state
    
    def rewrite(self, query: str, context_history: str = "") -> List[str]:
        """
        Rewrite a user query into better search terms.
        
        Args:
            query: The original user query
            context_history: Optional conversation context for better rewriting
            
        Returns:
            List of rewritten queries (2-3 alternatives)
        """
        initial_state: AgentState = {
            "original_query": query,
            "rewritten_queries": [],
            "context_history": context_history,
            "final_output": [],
        }
        
        try:
            result = self.graph.invoke(initial_state)
            return result["final_output"]
        except Exception as e:
            print(f"Query rewriting failed: {e}")
            # Fallback: return original query
            return [query]


# Singleton instance
query_rewriter = QueryRewriterAgent()
