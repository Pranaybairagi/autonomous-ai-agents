"""
Production ReAct Agent Implementation from Scratch
Demonstrates the foundational loop: Thought -> Action -> Observation -> Final Answer.
"""

import os
import json
import re
from typing import Dict, Any, Callable

# Simple mock calculator & search tools for demonstration
def search_database(query: str) -> str:
    """Simulates querying an internal database or web search."""
    mock_db = {
        "revenue": "Q3 2026 revenue was $4.2M, representing a 28% YoY growth.",
        "top_product": "LeadPulse Chrome Extension generated $180,000 in license sales.",
        "churn": "Monthly churn rate dropped to 1.8%."
    }
    for key, val in mock_db.items():
        if key in query.lower():
            return val
    return f"No exact record found for '{query}'. Available topics: revenue, top_product, churn."

def calculate(expression: str) -> str:
    """Safely evaluates a basic mathematical expression."""
    allowed = set("0123456789+-*/(). ")
    if not all(char in allowed for char in expression):
        return "Error: Unsupported characters in calculation."
    try:
        return str(eval(expression, {"__builtins__": None}, {}))
    except Exception as e:
        return f"Calculation error: {e}"

# Tool registry
TOOLS: Dict[str, Callable[[str], str]] = {
    "search": search_database,
    "calculate": calculate
}

def simulate_react_step(prompt: str, user_query: str) -> None:
    """
    Demonstrates the ReAct execution trace:
    1. Agent receives Goal
    2. Generates Thought & Action
    3. Host executes Action and returns Observation
    4. Agent synthesizes Final Answer
    """
    print(f"\n[USER QUERY]: {user_query}")
    print("-" * 50)
    
    # Step 1: Simulated Model Thought & Action
    thought_1 = "I need to find the Q3 2026 revenue and calculate the expected annual run rate."
    action_1 = 'search: revenue'
    print(f"[THOUGHT 1]: {thought_1}")
    print(f"[ACTION 1]:  {action_1}")
    
    # Step 2: Tool Execution (Observation)
    tool_name, tool_arg = action_1.split(":", 1)
    observation_1 = TOOLS[tool_name.strip()](tool_arg.strip())
    print(f"[OBSERVATION 1]: {observation_1}")
    
    # Step 3: Thought 2 & Next Action
    thought_2 = "Revenue was $4.2M for one quarter. Annualized run rate is approximately 4.2 * 4."
    action_2 = 'calculate: 4.2 * 4'
    print(f"[THOUGHT 2]: {thought_2}")
    print(f"[ACTION 2]:  {action_2}")
    
    # Step 4: Tool Execution (Observation 2)
    tool_name, tool_arg = action_2.split(":", 1)
    observation_2 = TOOLS[tool_name.strip()](tool_arg.strip())
    print(f"[OBSERVATION 2]: {observation_2}")
    
    # Step 5: Final Answer
    final_thought = "I have the Q3 revenue figures and the calculated annual run rate."
    final_answer = f"Q3 2026 revenue was $4.2M (28% YoY growth). The estimated annualized run rate is ${observation_2}M."
    print(f"[THOUGHT 3]: {final_thought}")
    print(f"\n[FINAL ANSWER]:\n{final_answer}\n" + "=" * 50)

if __name__ == "__main__":
    simulate_react_step("", "What was our Q3 2026 revenue and what is the annual run rate?")
