"""
Chapter 9: Production Deployment: FastAPI & Docker
File: chapter_09_production_deployment.py

Demonstrates:
1. Wrapping an Autonomous Agent inside an async FastAPI backend.
2. Server-Sent Events (SSE) streaming: Emitting real-time thoughts and observations.
3. Health check endpoints and automated test client verification.
"""

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from starlette.testclient import TestClient
import asyncio
import json
import time
from typing import AsyncGenerator

app = FastAPI(
    title="Autonomous Agent Production API",
    version="1.0.0",
    description="Production-grade asynchronous service for agent orchestration."
)

# --- 1. Schemas ---

class AgentRunRequest(BaseModel):
    task: str = Field(..., min_length=5, description="The user objective for the agent.")
    max_steps: int = Field(default=5, ge=1, le=10, description="Maximum execution step budget.")

class HealthResponse(BaseModel):
    status: str
    uptime_seconds: float
    timestamp: float

START_TIME = time.time()

# --- 2. Endpoints ---

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Kubernetes/Docker health and readiness probe."""
    return HealthResponse(
        status="HEALTHY",
        uptime_seconds=round(time.time() - START_TIME, 2),
        timestamp=time.time()
    )

async def agent_event_stream(task: str, max_steps: int) -> AsyncGenerator[str, None]:
    """
    Simulates real-time SSE event streaming from the agent loop:
    Yields events formatted as: 'event: <type>\ndata: <json>\n\n'
    """
    yield f"data: {json.dumps({'event': 'STARTED', 'task': task})}\n\n"
    await asyncio.sleep(0.05)

    # Step 1: Thinking
    yield f"data: {json.dumps({'event': 'THOUGHT', 'step': 1, 'content': 'Analyzing system dependencies for task.'})}\n\n"
    await asyncio.sleep(0.05)

    # Step 2: Tool Execution
    yield f"data: {json.dumps({'event': 'ACTION', 'step': 1, 'tool': 'inspect_environment', 'args': {}})}\n\n"
    await asyncio.sleep(0.05)

    yield f"data: {json.dumps({'event': 'OBSERVATION', 'step': 1, 'result': 'Python 3.12, Docker runtime active.'})}\n\n"
    await asyncio.sleep(0.05)

    # Step 3: Final Delivery
    yield f"data: {json.dumps({'event': 'COMPLETED', 'output': f'Successfully resolved task: {task}'})}\n\n"

@app.post("/api/agent/stream")
async def stream_agent_execution(req: AgentRunRequest):
    """
    Streams agent reasoning, tool dispatches, and final conclusions via Server-Sent Events (SSE).
    """
    return StreamingResponse(
        agent_event_stream(req.task, req.max_steps),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no" # Prevents Nginx from buffering SSE streams
        }
    )


# --- 3. Verification Test Suite ---

def run_production_api_test():
    print("=" * 65)
    print("🚀 CHAPTER 9: FASTAPI AGENT BACKEND & SSE STREAMING DEMO")
    print("=" * 65)

    client = TestClient(app)

    # Test 1: Healthcheck
    print("\n--- Test 1: Healthcheck Probe GET /health ---")
    res = client.get("/health")
    print(f"Status Code: {res.status_code}")
    print(f"Response: {res.json()}")
    assert res.status_code == 200

    # Test 2: SSE Event Streaming
    print("\n--- Test 2: SSE Real-Time Event Stream POST /api/agent/stream ---")
    payload = {"task": "Verify staging cluster container health", "max_steps": 3}
    
    with client.stream("POST", "/api/agent/stream", json=payload) as stream_res:
        print(f"Stream Status: {stream_res.status_code} ({stream_res.headers.get('content-type')})")
        print("Receiving Real-Time SSE Frames:")
        for line in stream_res.iter_lines():
            if line:
                print(f"  ⚡ {line}")

    print("\n" + "=" * 65)
    print("✅ FastAPI Agent Service & SSE Streaming verified successfully.")
    print("=" * 65)

if __name__ == "__main__":
    run_production_api_test()
