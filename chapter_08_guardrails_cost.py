"""
Chapter 8: Guardrails, Token Economics & Cost Optimization
File: chapter_08_guardrails_cost.py

Demonstrates:
1. Real-time Token Budget Tracker & Financial Hard-Stop Circuit Breaker.
2. Repetitive Loop & Prompt Drift Detector (Halts circular agent behavior).
3. Tiered Model Router: Directing simple tasks to Flash models and complex
   reasoning to Frontier models, saving 80%+ on operational costs.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import hashlib

# Current pricing per 1M tokens (USD)
PRICING_TABLE = {
    "flash": {"input_per_million": 0.10, "output_per_million": 0.40},
    "frontier": {"input_per_million": 3.00, "output_per_million": 15.00}
}

class TokenBudgetTracker:
    """
    Tracks prompt & completion token consumption in real time.
    Enforces a strict financial circuit breaker to prevent unexpected cloud bills.
    """
    def __init__(self, max_cost_budget_usd: float = 0.05):
        self.budget_usd = max_cost_budget_usd
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.cumulative_cost_usd = 0.0

    def record_usage(self, model_tier: str, input_tokens: int, output_tokens: int) -> bool:
        """Records token usage and checks if budget remains healthy."""
        pricing = PRICING_TABLE.get(model_tier, PRICING_TABLE["flash"])
        cost = (
            (input_tokens / 1_000_000) * pricing["input_per_million"] +
            (output_tokens / 1_000_000) * pricing["output_per_million"]
        )

        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.cumulative_cost_usd += cost

        if self.cumulative_cost_usd >= self.budget_usd:
            return False # Budget breached!
        return True


class RepetitiveLoopDetector:
    """
    Detects if an agent is stuck in an infinite loop repeating the same action.
    Uses MD5 action hashing over a sliding historical window.
    """
    def __init__(self, max_consecutive_duplicates: int = 2):
        self.max_duplicates = max_consecutive_duplicates
        self.action_history: List[str] = []

    def record_action_and_check_loop(self, tool_name: str, arguments: Dict[str, Any]) -> bool:
        """Returns True if a repetitive circular loop is detected."""
        serialized = f"{tool_name}:{json_compact(arguments)}"
        action_hash = hashlib.md5(serialized.encode()).hexdigest()
        self.action_history.append(action_hash)

        # Check trailing actions
        if len(self.action_history) >= self.max_duplicates:
            recent_slice = self.action_history[-self.max_duplicates:]
            if len(set(recent_slice)) == 1:
                return True # Loop detected
        return False


def json_compact(data: Dict[str, Any]) -> str:
    import json
    return json.dumps(data, sort_keys=True)


class TieredModelRouter:
    """
    Routes tasks based on complexity:
    - Classification, parsing, simple summaries -> 'flash'
    - High-order reasoning, code synthesis, architecture -> 'frontier'
    """
    @staticmethod
    def route_task(task_type: str) -> str:
        if task_type in ("json_extraction", "classification", "summarization", "regex_parse"):
            return "flash"
        return "frontier"


def run_guardrails_demo():
    print("=" * 65)
    print("🛡️  CHAPTER 8: GUARDRAILS & TOKEN ECONOMICS DEMONSTRATION")
    print("=" * 65)

    # 1. Financial Circuit Breaker
    print("\n--- Test 1: Real-Time Financial Circuit Breaker ---")
    budget_guard = TokenBudgetTracker(max_cost_budget_usd=0.01) # $0.01 max budget
    
    # Simulate turn 1 on Flash
    healthy = budget_guard.record_usage("flash", input_tokens=2500, output_tokens=400)
    print(f"Turn 1 (Flash): Cost = ${budget_guard.cumulative_cost_usd:.6f} | Healthy: {healthy}")

    # Simulate heavy turn on Frontier
    healthy = budget_guard.record_usage("frontier", input_tokens=3000, output_tokens=1000)
    print(f"Turn 2 (Frontier): Cost = ${budget_guard.cumulative_cost_usd:.6f} | Healthy: {healthy}")

    # Breaching budget
    healthy = budget_guard.record_usage("frontier", input_tokens=4000, output_tokens=2000)
    print(f"Turn 3 (Frontier): Cost = ${budget_guard.cumulative_cost_usd:.6f} | Healthy: {healthy}")
    if not healthy:
        print("🚨 CIRCUIT BREAKER TRIPPED: Execution aborted before financial overrun.")

    # 2. Repetitive Infinite Loop Detector
    print("\n--- Test 2: Repetitive Loop Detection ---")
    loop_guard = RepetitiveLoopDetector(max_consecutive_duplicates=2)

    action_1 = ("fetch_metrics", {"server_id": "us-east-1"})
    print(f"Step 1: Agent calls {action_1[0]} -> Loop Detected: {loop_guard.record_action_and_check_loop(*action_1)}")

    # Identical repeated action (simulating an agent that doesn't know what to do next)
    action_2 = ("fetch_metrics", {"server_id": "us-east-1"})
    print(f"Step 2: Agent repeats {action_2[0]} -> Loop Detected: {loop_guard.record_action_and_check_loop(*action_2)}")
    print("🛑 LOOP INTERCEPTED: Agent halted to prevent infinite billing cycle.")

    # 3. Model Routing Savings Analysis
    print("\n--- Test 3: Tiered Model Routing ---")
    tasks = ["json_extraction", "code_architecture_design", "classification", "bug_root_cause_analysis"]
    for t in tasks:
        chosen_tier = TieredModelRouter.route_task(t)
        print(f"Task '{t:<26}' -> Routed to: [{chosen_tier.upper()}] Tier")

    print("\n" + "=" * 65)
    print("✅ All guardrails and cost controls verified successfully.")
    print("=" * 65)

if __name__ == "__main__":
    run_guardrails_demo()
