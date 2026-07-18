#!/usr/bin/env python3
import os
import sys
import pathlib
from dotenv import load_dotenv
from google import genai

load_dotenv()

def write_code_file(filename: str, code: str) -> str:
    """
    Creates a Python file at the specified path and writes the provided code into it. This file will
    only be created if it resolves to a path within the current project directory. If the file already exists, it will be overwritten.
    """
    safe_directory = pathlib.Path(__file__).parent.resolve()
    
    # Ensure the current project directory exists to prevent FileNotFoundError
    # safe_directory.mkdir(parents=True, exist_ok=True)
    
    target_path = pathlib.Path(safe_directory / filename).resolve()

    if not target_path.is_relative_to(safe_directory):
        raise ValueError("File path is outside the allowed directory.")
    
    # Ensure subdirectories exist
    target_path.parent.mkdir(parents=True, exist_ok=True)

    with open(target_path, "w") as f:
        f.write(code)

    return f"File '{filename}' created successfully at '{target_path}'."

def read_code_file(filename: str) -> str:
    """
    Reads and returns the contents of a Python file at the specified path.
    Use this tool to inspect existing code, check function signatures, or debug errors.
    """
    safe_directory = pathlib.Path(__file__).parent.resolve()
    target_path = pathlib.Path(safe_directory / filename).resolve()

    if not target_path.is_relative_to(safe_directory):
        raise ValueError("File path is outside the allowed directory.")
    
    if not target_path.exists():
        return f"Error: File '{filename}' does not exist at '{target_path}'."
    
    with open(target_path, "r", encoding="utf-8") as f:
        content = f.read()

    return f"--- Contents of {filename} ---\n{content}\n--- End of File"

def main() -> int:
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    model_name = os.getenv("MODEL_NAME", "gemini-2.5-flash")

    if not project_id:
        print("Error: GOOGLE_CLOUD_PROJECT environment variable is not set.", file=sys.stderr)
        return 1
    
    # Initialize the client for Vertex AI
    client = genai.Client(
        vertexai=True,
        project=project_id,
        location=location,
    )

    prompt = """
        I am implementing the Interface layer for patient-registration-assistant.
        Context: Read CONTRACT.md, FUNCTIONALITY.md, src/engine/engine.py, and tests/interface/test_interface.py.
        Goal: Implement format_response(result: dict) -> str and run_session(process_fn=None)
            in src/interface/cli.py.
        Requirements:
        1. format_response: Read result["status"] and return a formatted string for each case:
        - "success"    → start with result["message"]; if result.get("data") is a non-empty
                            list, append each patient's name and ID on an indented line,
                            e.g., "  - {name} ({patient_id})".
        - "exists"     → return result["message"].
        - "incomplete" → return result["message"] + "\n  Missing: " +
                            ", ".join(result["missing"]).
        - "unknown"    → return result["message"] + "\n\n" + _HELP_TEXT.
        - "error" and all other statuses → return result.get("message", "Unexpected response.").
        Do not raise; always return a string.
        2. run_session: Loop calling input("You: ") to read one line at a time.
        - Skip blank lines (after strip).
        - Exit cleanly (print a goodbye message and return) when the line equals "quit"
            or "exit" (case-insensitive), or when EOFError is raised.
        - For all other input, call process_fn(user_input) to get a result dict,
            then print "Assistant: " followed by format_response(result).
        - Print a blank line after each response for readability.
        3. process_fn defaults to process_request imported from src.engine.engine at the
        top of cli.py. Inside run_session, always call process_fn(user_input) —
        never call process_request directly — so tests can inject a mock.
        4. Import process_request at the top of cli.py:
            from src.engine.engine import process_request
        This ensures the patch path "src.interface.cli.process_request" is valid if needed.
        5. Do not modify or weaken any tests.
        6. Do not modify any base code that does not need to be modified. Simply add the required implementations
        """

    print("Starting agent reasoning loop to implement green state...")

    try:
        # Create an ongoing chat session
        agent_chat = client.chats.create(
            model=model_name,
            config={"tools": [read_code_file, write_code_file]}
        )

        response = agent_chat.send_message(prompt)

        print("Goal achieved.")
        print("Agent final response:\n", response.text)
        
        return 0

    except Exception as e:
        print(f"Error occurred: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())