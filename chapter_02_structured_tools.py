"""
Chapter 2: Type-Safe Structured Tool Calling with Pydantic
File: chapter_02_structured_tools.py

Demonstrates:
1. Defining strict, self-documenting Tool schemas using Pydantic V2.
2. Generating JSON Schema tool definitions for LLMs automatically.
3. Robust runtime argument validation (catching hallucinated or malformed types).
4. Self-Correcting Error Feedback Loop: Returning validation errors to the agent
   so it can fix its own mistakes autonomously.
"""

from typing import Dict, Any, Callable, Optional, Type
from pydantic import BaseModel, Field, ValidationError
import json

# --- 1. Define Strict Pydantic Tool Schemas ---

class DatabaseQuerySchema(BaseModel):
    table_name: str = Field(
        ..., 
        description="The target table to query. Allowed: 'users', 'transactions', 'servers'."
    )
    limit: int = Field(
        default=5, 
        ge=1, 
        le=50, 
        description="Number of records to return. Must be between 1 and 50."
    )
    filter_status: Optional[str] = Field(
        default="active", 
        description="Optional status filter, e.g. 'active', 'failed', 'pending'."
    )

class EmailAlertSchema(BaseModel):
    recipient_email: str = Field(
        ..., 
        pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$", 
        description="A valid corporate email address."
    )
    severity: str = Field(
        ..., 
        description="Alert severity level: 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'."
    )
    message: str = Field(
        ..., 
        min_length=10, 
        description="Alert body text containing at least 10 characters."
    )


# --- 2. Tool Implementations (Pure Business Logic) ---

def execute_db_query(args: DatabaseQuerySchema) -> str:
    """Executes a simulated validated database read."""
    mock_data = {
        "users": [f"User_{i}@enterprise.com (status: {args.filter_status})" for i in range(1, args.limit + 1)],
        "transactions": [f"Txn_#{9000+i}: $249.00 (status: {args.filter_status})" for i in range(1, args.limit + 1)],
        "servers": [f"us-east-{i}.cloud.internal (status: {args.filter_status})" for i in range(1, args.limit + 1)]
    }
    records = mock_data.get(args.table_name.lower())
    if not records:
        return f"Error: Table '{args.table_name}' does not exist."
    return json.dumps({"table": args.table_name, "count": len(records), "data": records}, indent=2)

def execute_email_alert(args: EmailAlertSchema) -> str:
    """Dispatches a simulated high-priority notification."""
    return f"SUCCESS: Dispatched [{args.severity}] alert to <{args.recipient_email}> with body: '{args.message}'"


# --- 3. The Type-Safe Tool Dispatcher with Auto-Correction ---

class ToolDefinition:
    def __init__(self, name: str, description: str, schema: Type[BaseModel], handler: Callable[[Any], str]):
        self.name = name
        self.description = description
        self.schema = schema
        self.handler = handler

    def get_json_schema(self) -> Dict[str, Any]:
        """Exports clean JSON schema compatible with OpenAI, Gemini, and Ollama function calling."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.schema.model_json_schema()
        }

    def execute(self, raw_arguments: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validates arguments against the Pydantic schema.
        Returns: (success_boolean, output_or_error_message)
        """
        try:
            validated_args = self.schema(**raw_arguments)
            result = self.handler(validated_args)
            return True, result
        except ValidationError as val_err:
            # Format errors into actionable instructions for the model
            formatted_errors = []
            for err in val_err.errors():
                loc = " -> ".join([str(p) for p in err["loc"]])
                formatted_errors.append(f"Field '{loc}': {err['msg']} (Input was: {err.get('input')})")
            error_message = "VALIDATION_FAILED:\n" + "\n".join(formatted_errors)
            return False, error_message
        except Exception as exc:
            return False, f"RUNTIME_ERROR: {str(exc)}"


# --- 4. Demonstration: The Self-Healing Validation Loop ---

def run_type_safe_demo():
    print("=" * 65)
    print("🛡️  TYPE-SAFE STRUCTURED TOOL DISPATCHER (PYDANTIC V2)")
    print("=" * 65)

    # Register tools
    registry = {
        "query_database": ToolDefinition(
            name="query_database",
            description="Query enterprise tables with pagination and status filters.",
            schema=DatabaseQuerySchema,
            handler=execute_db_query
        ),
        "send_alert": ToolDefinition(
            name="send_alert",
            description="Send an operational alert email to system administrators.",
            schema=EmailAlertSchema,
            handler=execute_email_alert
        )
    }

    # Display generated JSON schemas (What the LLM receives)
    print("\n[SCHEMA EXPORT]: Tool schemas compiled for LLM function calling:")
    print(json.dumps(registry["query_database"].get_json_schema(), indent=2))

    # Scenario 1: Malformed LLM Tool Call (Invalid types & out of range values)
    print("\n" + "-" * 65)
    print("Scenario 1: Agent generates hallucinated/invalid parameters")
    print("-" * 65)
    
    bad_llm_payload = {
        "table_name": "servers",
        "limit": 999,  # Violates le=50 constraint
        "filter_status": "offline"
    }
    print(f"Incoming LLM Payload: {bad_llm_payload}")
    success, result = registry["query_database"].execute(bad_llm_payload)
    print(f"Validation Success: {success}")
    print(f"Host Response to Agent:\n{result}")

    # Scenario 2: Agent Self-Correction after receiving the feedback
    print("\n" + "-" * 65)
    print("Scenario 2: Agent corrects payload based on validation feedback")
    print("-" * 65)
    
    corrected_llm_payload = {
        "table_name": "servers",
        "limit": 3,   # Corrected within 1..50
        "filter_status": "active"
    }
    print(f"Incoming Corrected Payload: {corrected_llm_payload}")
    success, result = registry["query_database"].execute(corrected_llm_payload)
    print(f"Validation Success: {success}")
    print(f"Host Execution Result:\n{result}")

    # Scenario 3: Validation on Email Schema (Regex verification)
    print("\n" + "-" * 65)
    print("Scenario 3: Testing Strict Regex & String Length on Alert Tool")
    print("-" * 65)
    
    valid_alert_payload = {
        "recipient_email": "devops-oncall@startup.io",
        "severity": "HIGH",
        "message": "Cluster US-East-1 experiencing elevated API latency."
    }
    success, result = registry["send_alert"].execute(valid_alert_payload)
    print(f"Dispatch Result:\n{result}")
    print("=" * 65)

if __name__ == "__main__":
    run_type_safe_demo()
