"""
Chapter 7: Graph-Based Workflows & Cyclical State Graphs
File: chapter_07_graph_workflows.py

Demonstrates:
1. The Computational StateGraph architecture (Nodes, Edges, State).
2. Cyclical Loops & Conditional Routing (Iterative Code-Review-Refine).
3. Human-in-the-Loop Checkpoints (Approval Gate before production deployment).
"""

from typing import Dict, Any, Callable, List, Optional
from dataclasses import dataclass, field
import json

@dataclass
class GraphState:
    code_draft: str
    review_feedback: Optional[str] = None
    iteration_count: int = 0
    max_iterations: int = 3
    is_approved_by_human: bool = False
    is_deployed: bool = False

# --- Node Handlers ---

def node_draft_code(state: GraphState) -> GraphState:
    """Node A: Generates or refines code based on review feedback."""
    state.iteration_count += 1
    print(f"\n[NODE: DRAFT_CODE] (Iteration {state.iteration_count})")
    
    if not state.review_feedback:
        state.code_draft = "def process_payment(amount):\n    # v1 draft\n    return stripe.charge(amount)"
        print("  Created initial code draft.")
    else:
        state.code_draft = "def process_payment(amount, idempotency_key):\n    # v2 with review fixes\n    return stripe.charge(amount, key=idempotency_key)"
        print(f"  Applied review feedback: '{state.review_feedback}'")
    return state

def node_review_code(state: GraphState) -> GraphState:
    """Node B: Inspects code draft for missing parameters or vulnerabilities."""
    print("\n[NODE: REVIEW_CODE]")
    if "idempotency_key" not in state.code_draft:
        state.review_feedback = "CRITICAL: Missing idempotency_key parameter for Stripe payment."
        print(f"  Review Status: REJECTED ({state.review_feedback})")
    else:
        state.review_feedback = None
        print("  Review Status: APPROVED (Code meets engineering standards).")
    return state

def node_human_approval(state: GraphState) -> GraphState:
    """Node C: Human-in-the-Loop approval gate."""
    print("\n[NODE: HUMAN_APPROVAL_GATE]")
    print(f"  Requesting human sign-off for code deployment:\n'''\n{state.code_draft}\n'''")
    # Simulated human approval gate
    state.is_approved_by_human = True
    print("  Human Decision: [APPROVED BY USER]")
    return state

def node_deploy(state: GraphState) -> GraphState:
    """Node D: Final deployment node."""
    print("\n[NODE: PRODUCTION_DEPLOY]")
    state.is_deployed = True
    print("  🚀 Code deployed to production cluster successfully.")
    return state


# --- Conditional Routing Edge ---

def conditional_review_edge(state: GraphState) -> str:
    """Decides next node based on state values (Cyclical Loop or Forward)."""
    if state.review_feedback is not None:
        if state.iteration_count >= state.max_iterations:
            print("  Route: Max iterations reached. Halting loop.")
            return "END"
        print("  Route: Feedback detected -> Routing back to [DRAFT_CODE] (Cyclic Edge).")
        return "draft_code"
    
    print("  Route: Code passed review -> Routing to [HUMAN_APPROVAL].")
    return "human_approval"


# --- Minimalist StateGraph Engine ---

class StateGraphEngine:
    def __init__(self):
        self.nodes: Dict[str, Callable[[GraphState], GraphState]] = {}
        self.conditional_edges: Dict[str, Callable[[GraphState], str]] = {}

    def add_node(self, name: str, func: Callable[[GraphState], GraphState]):
        self.nodes[name] = func

    def add_conditional_edge(self, source_node: str, router_func: Callable[[GraphState], str]):
        self.conditional_edges[source_node] = router_func

    def run(self, initial_state: GraphState) -> GraphState:
        print("=" * 65)
        print("🕸️  GRAPH WORKFLOW: Starting Cyclic Execution Pipeline")
        print("=" * 65)

        state = initial_state
        current_node = "draft_code"

        while current_node != "END":
            # Execute node logic
            node_fn = self.nodes[current_node]
            state = node_fn(state)

            # Determine next transition
            if current_node in self.conditional_edges:
                current_node = self.conditional_edges[current_node](state)
            elif current_node == "draft_code":
                current_node = "review_code"
            elif current_node == "human_approval":
                if state.is_approved_by_human:
                    current_node = "deploy"
                else:
                    current_node = "END"
            elif current_node == "deploy":
                current_node = "END"

        print("\n" + "=" * 65)
        print("🏁 GRAPH WORKFLOW FINISHED: Final State Reached")
        print(f"Iterations: {state.iteration_count} | Deployed: {state.is_deployed}")
        print("=" * 65)
        return state


def run_graph_demo():
    graph = StateGraphEngine()
    graph.add_node("draft_code", node_draft_code)
    graph.add_node("review_code", node_review_code)
    graph.add_node("human_approval", node_human_approval)
    graph.add_node("deploy", node_deploy)

    graph.add_conditional_edge("review_code", conditional_review_edge)

    init_state = GraphState(code_draft="", max_iterations=3)
    final_state = graph.run(init_state)

if __name__ == "__main__":
    run_graph_demo()
