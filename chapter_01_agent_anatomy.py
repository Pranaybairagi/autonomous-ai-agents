"""
Chapter 1: The Anatomy of an Autonomous Agent
File: chapter_01_agent_anatomy.py

Demonstrates:
1. Strict Agent State representation (Dataclass / TypedDict).
2. The ReAct (Reasoning -> Action -> Observation -> Reflection) cycle.
3. Execution Budgets (Max Steps Guardrail to eliminate infinite loops).
4. Deterministic Tool Execution boundary.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Callable, Optional
import json
import re

@dataclass
class AgentStep:
    step_number: int
    thought: str
    action: Optional[str] = None
    observation: Optional[str] = None

@dataclass
class AgentState:
    goal: str
    max_steps: int = 5
    current_step: int = 0
    history: List[AgentStep] = field(default_factory=list)
    is_completed: bool = False
    final_output: Optional[str] = None

# --- Tool Registry ---
def tool_query_metrics(metric_name: str) -> str:
    """Mock database lookup for production system metrics."""
    metrics_db = {
        "active_users": "142,500 monthly active users (MAU)",
        "server_latency": "p99 latency is 42ms across US-East regions",
        "api_error_rate": "0.04% error rate over the last 24 hours"
    }
    return metrics_db.get(metric_name.strip().lower(), f"Metric '{metric_name}' not found.")

def tool_evaluate_threshold(expression: str) -> str:
    """Evaluates mathematical condition or ratio safely."""
    allowed = set("0123456789+-*/.<>= ")
    if not all(c in allowed for c in expression):
        return "Error: Disallowed characters in evaluation."
    try:
        # Safe evaluation of basic comparisons
        result = eval(expression, {"__builtins__": None}, {})
        return f"Condition ({expression}) evaluated to: {result}"
    except Exception as exc:
        return f"Evaluation error: {exc}"

AVAILABLE_TOOLS: Dict[str, Callable[[str], str]] = {
    "query_metrics": tool_query_metrics,
    "evaluate_threshold": tool_evaluate_threshold
}

class AutonomousAgentHarness:
    """
    Minimalist, framework-free Agent Harness demonstrating
    how an autonomous agent cycle operates under the hood.
    """
    def __init__(self, tools: Dict[str, Callable[[str], str]], max_steps: int = 5):
        self.tools = tools
        self.max_steps = max_steps

    def compile_system_prompt(self, state: AgentState) -> str:
        """Constructs an anti-hallucination, structured system prompt."""
        tools_description = "\n".join([f"- {name}: {fn.__doc__}" for name, fn in self.tools.items()])
        
        prompt = (
            "You are a Production Operations Autonomous Agent.\n"
            f"GOAL: {state.goal}\n\n"
            "AVAILABLE TOOLS:\n"
            f"{tools_description}\n\n"
            "STRICT PROTOCOL:\n"
            "1. Output a Thought explaining your reasoning.\n"
            "2. If an action is required, output: ACTION: <tool_name>(<argument>)\n"
            "3. If the goal is achieved, output: FINAL_ANSWER: <summary>\n"
            "4. Never hallucinate tool names. You have a maximum step budget.\n"
        )
        return prompt

    def parse_llm_response(self, text: str) -> tuple[str, Optional[str], Optional[str], Optional[str]]:
        """Parses thought, action tool, argument, and final answer from agent response."""
        thought_match = re.search(r"THOUGHT:\s*(.*?)(?=(?:ACTION:|FINAL_ANSWER:|$))", text, re.DOTALL | re.IGNORECASE)
        action_match = re.search(r"ACTION:\s*(\w+)\((.*?)\)", text, re.DOTALL | re.IGNORECASE)
        final_match = re.search(r"FINAL_ANSWER:\s*(.*)", text, re.DOTALL | re.IGNORECASE)

        thought = thought_match.group(1).strip() if thought_match else text.strip()
        tool_name = action_match.group(1).strip() if action_match else None
        tool_arg = action_match.group(2).strip() if action_match else None
        final_answer = final_match.group(1).strip() if final_match else None

        return thought, tool_name, tool_arg, final_answer

    def run(self, goal: str, simulated_responses: List[str]) -> AgentState:
        """
        Executes the autonomous loop up to max_steps or until final answer.
        Uses deterministic responses to illustrate the exact trace.
        """
        state = AgentState(goal=goal, max_steps=self.max_steps)
        print(f"\n" + "=" * 60)
        print(f"🚀 INITIALIZING AGENT RUN")
        print(f"🎯 GOAL: {state.goal}")
        print(f"🛡️  STEP BUDGET: {state.max_steps}")
        print("=" * 60)

        for step_idx, response in enumerate(simulated_responses, start=1):
            state.current_step = step_idx
            if state.current_step > state.max_steps:
                print(f"\n[ALERT] Step limit reached ({state.max_steps}). Terminating loop to prevent cost overrun.")
                break

            print(f"\n--- [CYCLE STEP {step_idx} of {state.max_steps}] ---")
            thought, tool_name, tool_arg, final_answer = self.parse_llm_response(response)
            
            step = AgentStep(step_number=step_idx, thought=thought)
            print(f"🧠 Thought: {thought}")

            if final_answer:
                state.is_completed = True
                state.final_output = final_answer
                state.history.append(step)
                print(f"\n✅ FINAL ANSWER REACHED:")
                print(f"   {final_answer}")
                break

            if tool_name:
                step.action = f"{tool_name}({tool_arg})"
                print(f"⚡ Action Invoked: {step.action}")

                # Tool execution with boundary protection
                if tool_name in self.tools:
                    try:
                        observation = self.tools[tool_name](tool_arg or "")
                    except Exception as err:
                        observation = f"Tool runtime error: {err}"
                else:
                    observation = f"Error: Tool '{tool_name}' does not exist in registry."

                step.observation = observation
                print(f"👁️ Observation: {observation}")
            
            state.history.append(step)

        print("\n" + "=" * 60)
        print(f"🏁 RUN FINISHED. Total Steps: {len(state.history)} | Success: {state.is_completed}")
        print("=" * 60)
        return state

if __name__ == "__main__":
    # Example Demonstration Trace
    agent_harness = AutonomousAgentHarness(tools=AVAILABLE_TOOLS, max_steps=4)
    
    # Trace of LLM outputs (in production, these come from your LLM API call)
    trace = [
        "THOUGHT: To evaluate system health, I must first inspect the current API error rate.\nACTION: query_metrics(api_error_rate)",
        "THOUGHT: The error rate is 0.04%. I need to verify whether this is safely below the SLA threshold of 0.05%.\nACTION: evaluate_threshold(0.04 < 0.05)",
        "THOUGHT: Both the error metric and SLA threshold conditions have been validated.\nFINAL_ANSWER: System health is nominal. Current API error rate is 0.04%, which remains compliant with the < 0.05% SLA threshold."
    ]

    agent_harness.run(
        goal="Audit production system reliability and verify SLA compliance.",
        simulated_responses=trace
    )
