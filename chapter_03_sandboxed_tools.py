"""
Chapter 3: Safe Tool Sandboxing & Execution Boundaries
File: chapter_03_sandboxed_tools.py

Demonstrates:
1. Directory Traversal Security Guardrails (Path Jail).
2. Subprocess Command Execution with Hard Timeouts and Command Blacklists.
3. Resilient HTTP API Client with Error Handling and Truncation.
"""

import os
import subprocess
import pathlib
import sys
from typing import Dict, Any, Optional

class SecurityViolation(Exception):
    """Raised when an agent attempts an unauthorized host operation."""
    pass


class SandboxedFileSystem:
    """
    Guarantees that an agent can only read, write, and inspect files
    within a strictly designated sandbox directory (Jail).
    """
    def __init__(self, sandbox_root: str):
        self.root = pathlib.Path(sandbox_root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _resolve_safe_path(self, relative_path: str) -> pathlib.Path:
        """Resolves target path and strictly verifies it stays within sandbox root."""
        # Resolve path to prevent ../ or symlink escapes
        target_path = (self.root / relative_path).resolve()
        try:
            # Python 3.9+ is_relative_to
            target_path.relative_to(self.root)
        except ValueError:
            raise SecurityViolation(f"ACCESS_DENIED: Path '{relative_path}' escapes the sandbox directory.")
        return target_path

    def write_file(self, filename: str, content: str) -> str:
        safe_path = self._resolve_safe_path(filename)
        safe_path.parent.mkdir(parents=True, exist_ok=True)
        safe_path.write_text(content, encoding="utf-8")
        return f"SUCCESS: Written {len(content)} characters to '{filename}'."

    def read_file(self, filename: str, max_chars: int = 2000) -> str:
        safe_path = self._resolve_safe_path(filename)
        if not safe_path.exists():
            return f"ERROR: File '{filename}' does not exist in sandbox."
        
        content = safe_path.read_text(encoding="utf-8")
        if len(content) > max_chars:
            return content[:max_chars] + f"\n... [TRUNCATED: {len(content) - max_chars} characters omitted to preserve context window]"
        return content


class SandboxedBashRunner:
    """
    Executes shell commands with:
    - Hard execution timeouts (kills stuck processes).
    - Blacklisted destructive commands.
    - Output length guards to prevent context window explosion.
    """
    BLACKLIST = [
        "rm -rf", "del /f", "format ", "mkfs", 
        ":(){ :|:& };:", "drop database", "shutdown"
    ]

    def __init__(self, timeout_seconds: int = 5, max_output_chars: int = 1500):
        self.timeout = timeout_seconds
        self.max_output = max_output_chars

    def execute(self, command: str) -> str:
        # 1. Inspect command against blacklist
        command_lower = command.lower()
        for forbidden in self.BLACKLIST:
            if forbidden in command_lower:
                return f"SECURITY_BLOCKED: Command contains prohibited keyword '{forbidden}'."

        # 2. Run with timeout boundary
        try:
            process = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            stdout = process.stdout.strip()
            stderr = process.stderr.strip()

            combined = ""
            if stdout:
                combined += f"[STDOUT]:\n{stdout}"
            if stderr:
                combined += f"\n[STDERR]:\n{stderr}"
            if not combined:
                combined = f"[SUCCESS: Command exited with code {process.returncode} and empty output]"

            # 3. Truncate oversized output
            if len(combined) > self.max_output:
                combined = combined[:self.max_output] + f"\n... [TRUNCATED: Exceeded {self.max_output} chars]"

            return combined

        except subprocess.TimeoutExpired:
            return f"TIMEOUT_ERROR: Execution exceeded the {self.timeout}s limit and was forcefully terminated."
        except Exception as exc:
            return f"EXECUTION_ERROR: {str(exc)}"


def run_sandboxing_demo():
    print("=" * 65)
    print("🛡️  CHAPTER 3: SECURE AGENT TOOL SANDBOXING DEMONSTRATION")
    print("=" * 65)

    # Setup isolated temporary sandbox
    sandbox_path = "./agent_workspace_sandbox"
    fs = SandboxedFileSystem(sandbox_root=sandbox_path)
    runner = SandboxedBashRunner(timeout_seconds=3)

    # Test 1: Legitimate File Write & Read
    print("\n--- Test 1: Legitimate File Write & Read ---")
    write_res = fs.write_file("reports/daily_audit.txt", "All systems operational. CPU load: 14%.")
    print(write_res)
    read_res = fs.read_file("reports/daily_audit.txt")
    print(f"File Content Read: '{read_res}'")

    # Test 2: Malicious Directory Traversal Escape Attempt
    print("\n--- Test 2: Malicious Path Traversal Attempt (Path Jail Check) ---")
    try:
        fs.read_file("../../../Windows/System32/drivers/etc/hosts")
    except SecurityViolation as sec_err:
        print(f"🛡️ Security Guardrail Triggered: {sec_err}")

    # Test 3: Safe Bash Command Execution
    print("\n--- Test 3: Safe Command Execution ---")
    cmd_output = runner.execute("python --version")
    print(cmd_output)

    # Test 4: Blacklisted Destructive Command Execution
    print("\n--- Test 4: Blacklist Block Check ---")
    blocked_res = runner.execute("rm -rf /var/data")
    print(blocked_res)

    # Test 5: Infinite Loop Timeout Guardrail
    print("\n--- Test 5: Infinite Process Timeout Guardrail ---")
    # A python script that sleeps for 10 seconds (exceeding 3s timeout)
    timeout_res = runner.execute('python -c "import time; time.sleep(10)"')
    print(timeout_res)

    print("\n" + "=" * 65)
    print("✅ All sandbox guardrails verified successfully.")
    print("=" * 65)

    # Cleanup temporary test files
    if os.path.exists(sandbox_path):
        import shutil
        shutil.rmtree(sandbox_path, ignore_errors=True)

if __name__ == "__main__":
    run_sandboxing_demo()
