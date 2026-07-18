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
        I am implementing the Engine layer for ucr-club-assistant.
        Context: Read CONTRACT.md, FUNCTIONALITY.md, src/storage/storage_handler.py 
                and tests/engine/test_engine.py.
        Goal: Implement process_request(user_input: str) -> dict in src/engine/engine.py.
        Requirements:
        1. Step 1 — Tool Use: Initialize an AI model client using _API_KEY and _MODEL from
        engine.py. Call the model with _EXTRACTION_PROMPT as the system instruction and
        user_input as the user message. Enforce JSON output. Parse the response to extract:
        {"intent": "register"|"list"|"delete"|"unknown", "data": {field: value, ...}}
        Load _API_KEY from os.getenv() only; never hardcode it.
        2. Step 2 — Reflection: Call the model again with _REFLECTION_PROMPT formatted with
        the extraction result. Enforce JSON output. Parse the response to get
        {"complete": bool, "missing": [...]}.
        If complete is False, return {"status": "incomplete", "message": ..., "missing": [...]}
        immediately — do NOT call any storage function.
        3. Step 3 — Dispatch: Based on intent, call:
        - "register" → save_patient(data)              returns "success" | "exists" | "error"
        - "list"     → get_patients()                  returns list of dicts
        - "delete"   → delete_patient(data.get("patient_id")) returns "success" | "not_found" | "error"
        - "unknown"  → return {"status": "unknown", "message": "...", "data": None}
        4. Return contract: every code path returns a dict with at least "status" and "message" keys.
        5. Import save_patient, get_patients, delete_patient at the top of engine.py
        so the patch paths in tests (src.engine.engine.*) resolve correctly.
        6. Wrap all logic in try/except; return {"status": "error", "message": str(e), "data": None}.
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