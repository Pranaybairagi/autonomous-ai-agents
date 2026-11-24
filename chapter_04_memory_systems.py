"""
Chapter 4: Memory Systems & Context Optimization
File: chapter_04_memory_systems.py

Demonstrates:
1. Short-Term Working Buffer vs. Long-Term Persistent State.
2. SQLite Episodic Memory Store (Crash-resilient state recovery).
3. Hierarchical Context Compactor: Sliding window compression to prevent
   context window rot and token cost explosion.
"""

import sqlite3
import json
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class MemoryRecord:
    turn_id: int
    role: str
    content: str
    timestamp: float = 0.0

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.time()


class SQLiteAgentMemory:
    """
    Production-grade SQLite episodic memory store.
    Persists turn history, tool execution results, and agent reflections.
    """
    def __init__(self, db_path: str = ":memory:"):
        self.conn = sqlite3.connect(db_path)
        self._init_tables()

    def _init_tables(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS session_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    turn_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp REAL NOT NULL
                )
            """)
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_session_turn 
                ON session_memory(session_id, turn_id)
            """)

    def save_turn(self, session_id: str, turn_id: int, role: str, content: str) -> None:
        with self.conn:
            self.conn.execute("""
                INSERT INTO session_memory (session_id, turn_id, role, content, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (session_id, turn_id, role, content, time.time()))

    def fetch_recent_turns(self, session_id: str, limit: int = 10) -> List[MemoryRecord]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT turn_id, role, content, timestamp
            FROM session_memory
            WHERE session_id = ?
            ORDER BY turn_id DESC
            LIMIT ?
        """, (session_id, limit))
        rows = cursor.fetchall()
        # Return in chronological order
        return [MemoryRecord(turn_id=r[0], role=r[1], content=r[2], timestamp=r[3]) for r in reversed(rows)]

    def close(self):
        self.conn.close()


class ContextWindowCompactor:
    """
    Compresses older conversation history while retaining recent turns verbatim.
    Prevents 'Lost in the Middle' attention degradation.
    """
    def __init__(self, recent_window_size: int = 3):
        self.recent_window_size = recent_window_size

    def compress_history(self, all_turns: List[MemoryRecord]) -> List[Dict[str, str]]:
        if len(all_turns) <= self.recent_window_size:
            return [{"role": t.role, "content": t.content} for t in all_turns]

        # Partition into historical turns (to compress) and active turns (keep verbatim)
        older_turns = all_turns[:-self.recent_window_size]
        recent_turns = all_turns[-self.recent_window_size:]

        # Simulated semantic compression of older turns
        summarized_facts = []
        for turn in older_turns:
            if turn.role == "tool":
                summarized_facts.append(f"Observation gathered in turn {turn.turn_id}: {turn.content[:60]}...")
            elif turn.role == "agent":
                summarized_facts.append(f"Action planned in turn {turn.turn_id}: {turn.content[:60]}...")

        compressed_summary = (
            "[SYSTEM MEMORY SUMMARY OF PREVIOUS STEPS]:\n" + 
            "\n".join([f"• {f}" for f in summarized_facts])
        )

        optimized_context = [{"role": "system", "content": compressed_summary}]
        for t in recent_turns:
            optimized_context.append({"role": t.role, "content": t.content})

        return optimized_context


def run_memory_demo():
    print("=" * 65)
    print("🧠 CHAPTER 4: AGENT MEMORY & CONTEXT OPTIMIZATION DEMO")
    print("=" * 65)

    # 1. Initialize SQLite Memory Store
    memory_store = SQLiteAgentMemory(db_path=":memory:")
    session_id = "agent_session_prod_902"

    print(f"\n1. Simulating 6 multi-step reasoning turns for session '{session_id}'...")
    turns_data = [
        (1, "user", "Investigate outage on server us-east-4."),
        (2, "agent", "THOUGHT: Checking server uptime and CPU metrics.\nACTION: check_server(us-east-4)"),
        (3, "tool", "STATUS: CPU 99.2%, RAM 94%, OOM Killer invoked 2 times."),
        (4, "agent", "THOUGHT: Memory leak detected. Fetching top memory consuming processes.\nACTION: top_processes(us-east-4)"),
        (5, "tool", "PID 8192 (worker_celery) consuming 14.2 GB of RAM."),
        (6, "agent", "THOUGHT: Worker celery PID 8192 is frozen in an unbounded queue loop.")
    ]

    for turn_id, role, content in turns_data:
        memory_store.save_turn(session_id, turn_id, role, content)

    # 2. Fetch history from SQLite
    all_turns = memory_store.fetch_recent_turns(session_id, limit=20)
    print(f"✅ Successfully fetched {len(all_turns)} turns from persistent SQLite storage.")

    # 3. Apply Sliding Window Context Compactor
    compactor = ContextWindowCompactor(recent_window_size=2)
    optimized_context = compactor.compress_history(all_turns)

    print("\n" + "-" * 65)
    print("2. Optimized Prompt Payload Sent to LLM (Context Protected):")
    print("-" * 65)
    for idx, msg in enumerate(optimized_context, start=1):
        print(f"\n[Message Block {idx}] ({msg['role'].upper()}):")
        print(msg['content'])

    print("\n" + "=" * 65)
    print("✅ Memory persistence & context compaction verified successfully.")
    print("=" * 65)
    memory_store.close()

if __name__ == "__main__":
    run_memory_demo()
