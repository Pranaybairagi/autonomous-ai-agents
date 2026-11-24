"""
Chapter 6: Multi-Agent Orchestration & Communication
File: chapter_06_multi_agent_swarm.py

Demonstrates:
1. The Coordinator-Worker Topology.
2. Structured Message Dispatching via a Shared Communication Board.
3. Sub-task Decomposition, Parallel Specialization, and Executive Synthesis.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import json
import time

@dataclass
class SwarmMessage:
    sender: str
    recipient: str
    content: str
    step: int
    timestamp: float = field(default_factory=time.time)

class SharedMessageBoard:
    """Central blackboard where autonomous agents exchange task requests and findings."""
    def __init__(self):
        self.messages: List[SwarmMessage] = []

    def post(self, sender: str, recipient: str, content: str, step: int) -> None:
        msg = SwarmMessage(sender=sender, recipient=recipient, content=content, step=step)
        self.messages.append(msg)

    def get_messages_for(self, recipient: str) -> List[SwarmMessage]:
        return [m for m in self.messages if m.recipient in (recipient, "all")]


class SpecializedWorkerAgent:
    """Specialized worker role (e.g. Security Auditor, Performance Engineer)."""
    def __init__(self, name: str, domain: str, board: SharedMessageBoard):
        self.name = name
        self.domain = domain
        self.board = board

    def process_task(self, task_description: str, step: int) -> str:
        # Simulated specialized domain analysis
        if "security" in self.domain.lower():
            finding = (
                "[SECURITY AUDIT COMPLETE]: Scanned 14 API endpoints.\n"
                "• CRITICAL: Found exposed Stripe test secret in payment_worker.py:L14\n"
                "• PASS: SQL queries are fully parameterized via SQLAlchemy ORM."
            )
        elif "performance" in self.domain.lower():
            finding = (
                "[PERFORMANCE PROFILE COMPLETE]: Analyzed database query latency.\n"
                "• WARNING: Detected N+1 query pattern on /orders endpoint (p95 = 480ms)\n"
                "• RECOMMENDATION: Add Redis caching layer for merchant metadata."
            )
        else:
            finding = f"Task completed for domain '{self.domain}'."

        self.board.post(sender=self.name, recipient="coordinator", content=finding, step=step)
        return finding


class CoordinatorAgent:
    """
    Central orchestration agent:
    1. Receives complex goal
    2. Decomposes into specialized sub-tasks
    3. Delegates to workers
    4. Synthesizes findings into final unified deliverable
    """
    def __init__(self, name: str, board: SharedMessageBoard):
        self.name = name
        self.board = board
        self.workers: Dict[str, SpecializedWorkerAgent] = {}

    def register_worker(self, worker: SpecializedWorkerAgent):
        self.workers[worker.name] = worker

    def orchestrate(self, overarching_goal: str) -> str:
        print("=" * 65)
        print(f"👑 COORDINATOR AGENT: Initializing Multi-Agent Swarm")
        print(f"🎯 Objective: {overarching_goal}")
        print("=" * 65)

        # Step 1: Goal Decomposition
        print("\n--- Step 1: Coordinator Decomposes Objective into Workstreams ---")
        tasks = {
            "sec_auditor": "Audit codebase for credentials, hardcoded keys, and injection vulnerabilities.",
            "perf_engineer": "Analyze query performance, API latency bottlenecks, and caching coverage."
        }

        # Step 2: Delegate to Specialized Workers
        for worker_name, task in tasks.items():
            print(f"📨 Dispatching task to [@{worker_name}]: '{task}'")
            self.board.post(sender=self.name, recipient=worker_name, content=task, step=1)
            
            # Worker processes assignment
            worker = self.workers[worker_name]
            print(f"⚙️  Worker [@{worker_name}] analyzing domain: {worker.domain}...")
            worker.process_task(task, step=2)

        # Step 3: Synthesis of Multi-Agent Reports
        print("\n--- Step 2: Coordinator Harvests & Synthesizes Worker Reports ---")
        worker_reports = self.board.get_messages_for("coordinator")
        print(f"Received {len(worker_reports)} domain reports from the board.\n")

        synthesis_body = []
        for rep in worker_reports:
            synthesis_body.append(f"--- From {rep.sender.upper()} ---\n{rep.content}\n")

        final_synthesis = (
            "=================================================================\n"
            "📋 EXECUTIVE UNIFIED SYSTEM AUDIT REPORT\n"
            "=================================================================\n"
            + "\n".join(synthesis_body) +
            "=================================================================\n"
            "FINAL REMEDIATION ACTION PLAN:\n"
            "1. Revoke and rotate exposed Stripe API key immediately.\n"
            "2. Implement eager-loading on /orders queries to eliminate N+1 latency.\n"
            "================================================================="
        )
        return final_synthesis


def run_multi_agent_demo():
    # Setup shared blackboard
    board = SharedMessageBoard()

    # Instantiate coordinator and workers
    coordinator = CoordinatorAgent("coordinator", board)
    sec_worker = SpecializedWorkerAgent("sec_auditor", "Application Security", board)
    perf_worker = SpecializedWorkerAgent("perf_engineer", "System Performance", board)

    coordinator.register_worker(sec_worker)
    coordinator.register_worker(perf_worker)

    # Run orchestration workflow
    result = coordinator.orchestrate(
        overarching_goal="Conduct complete pre-launch readiness review of the Payments SaaS Service."
    )
    print(result)

if __name__ == "__main__":
    run_multi_agent_demo()
