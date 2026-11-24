"""
Chapter 5: The Model Context Protocol (MCP) Architecture
File: chapter_05_mcp_client_server.py

Demonstrates:
1. The JSON-RPC 2.0 protocol standard powering the Model Context Protocol (MCP).
2. Building an MCP Tool Server exposing standardized capabilities.
3. Building an Autonomous Agent MCP Client that discovers and executes tools dynamically.
"""

import json
from typing import Dict, Any, List, Optional, Callable

# --- 1. MCP Standard JSON-RPC 2.0 Protocol Envelope ---

class JsonRpcMessage:
    @staticmethod
    def request(req_id: int, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params or {}
        }

    @staticmethod
    def response(req_id: int, result: Any) -> Dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": result
        }

    @staticmethod
    def error(req_id: int, code: int, message: str) -> Dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": code, "message": message}
        }


# --- 2. The MCP Tool Server ---

class ModelContextProtocolServer:
    """
    Standardized MCP Server exposing tools over JSON-RPC 2.0.
    In production, this communicates via stdio or Server-Sent Events (SSE).
    """
    def __init__(self, server_name: str, version: str = "1.0.0"):
        self.server_name = server_name
        self.version = version
        self.tools: Dict[str, Dict[str, Any]] = {}
        self.handlers: Dict[str, Callable[[Dict[str, Any]], Any]] = {}

    def register_tool(self, name: str, description: str, input_schema: Dict[str, Any], handler: Callable[[Dict[str, Any]], Any]):
        """Registers a capability according to the MCP specification."""
        self.tools[name] = {
            "name": name,
            "description": description,
            "inputSchema": input_schema
        }
        self.handlers[name] = handler

    def handle_message(self, raw_request: str) -> str:
        """Processes an incoming JSON-RPC 2.0 frame."""
        try:
            req = json.loads(raw_request)
            req_id = req.get("id", 1)
            method = req.get("method")
            params = req.get("params", {})

            # MCP Protocol Handshake & Tool Discovery
            if method == "tools/list":
                tool_list = list(self.tools.values())
                return json.dumps(JsonRpcMessage.response(req_id, {"tools": tool_list}))

            # MCP Tool Execution
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})

                if tool_name not in self.handlers:
                    return json.dumps(JsonRpcMessage.error(req_id, -32601, f"Method/Tool '{tool_name}' not found"))

                handler = self.handlers[tool_name]
                execution_result = handler(arguments)
                return json.dumps(JsonRpcMessage.response(req_id, {
                    "content": [{"type": "text", "text": str(execution_result)}],
                    "isError": False
                }))

            else:
                return json.dumps(JsonRpcMessage.error(req_id, -32600, f"Unsupported MCP method '{method}'"))

        except Exception as exc:
            return json.dumps(JsonRpcMessage.error(0, -32603, f"Internal JSON-RPC error: {str(exc)}"))


# --- 3. The Autonomous Agent MCP Client ---

class AgentMcpClient:
    """
    Client harness allowing an AI agent to connect to any standard MCP server,
    discover available tools dynamically, and invoke them safely.
    """
    def __init__(self, server: ModelContextProtocolServer):
        self.server = server
        self.msg_counter = 0

    def discover_tools(self) -> List[Dict[str, Any]]:
        """Queries the server via 'tools/list'."""
        self.msg_counter += 1
        req = JsonRpcMessage.request(self.msg_counter, "tools/list")
        res_str = self.server.handle_message(json.dumps(req))
        res = json.loads(res_str)
        return res["result"]["tools"]

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Executes a tool on the server via 'tools/call'."""
        self.msg_counter += 1
        req = JsonRpcMessage.request(self.msg_counter, "tools/call", {
            "name": tool_name,
            "arguments": arguments
        })
        res_str = self.server.handle_message(json.dumps(req))
        res = json.loads(res_str)

        if "error" in res:
            return f"MCP_ERROR: {res['error']['message']}"
        return res["result"]["content"][0]["text"]


# --- 4. Verification & Demonstration ---

def run_mcp_demo():
    print("=" * 65)
    print("🔌 CHAPTER 5: MODEL CONTEXT PROTOCOL (MCP) CLIENT-SERVER DEMO")
    print("=" * 65)

    # 1. Spin up an MCP Server for System Monitoring
    server = ModelContextProtocolServer("cluster-telemetry-server", version="2.0")

    # Define tools with standard MCP schemas
    server.register_tool(
        name="fetch_cluster_status",
        description="Retrieves live telemetry and health status of cloud worker nodes.",
        input_schema={
            "type": "object",
            "properties": {
                "region": {"type": "string", "description": "Cloud region e.g. 'us-east', 'eu-west'"}
            },
            "required": ["region"]
        },
        handler=lambda args: f"Cluster in region '{args.get('region')}': 18 nodes healthy, 0 degradation, CPU 31%."
    )

    # 2. Connect Agent Client
    client = AgentMcpClient(server)

    # 3. Step 1: Tool Discovery Handshake
    print("\n--- Step 1: Agent Discovers Tools via 'tools/list' ---")
    available_tools = client.discover_tools()
    print(f"Discovered {len(available_tools)} MCP tool(s):")
    print(json.dumps(available_tools, indent=2))

    # 4. Step 2: Agent Dispatches Tool Call via 'tools/call'
    print("\n--- Step 2: Agent Invokes Discovered Tool via 'tools/call' ---")
    execution_result = client.call_tool("fetch_cluster_status", {"region": "us-east"})
    print(f"Tool Execution Output:\n{execution_result}")

    # 5. Step 3: Error Handling for Non-existent Tool
    print("\n--- Step 3: MCP Error Boundary Check ---")
    error_result = client.call_tool("unregistered_tool", {})
    print(f"Response: {error_result}")

    print("\n" + "=" * 65)
    print("✅ Model Context Protocol (MCP) client-server cycle verified.")
    print("=" * 65)

if __name__ == "__main__":
    run_mcp_demo()
