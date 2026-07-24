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
    IMPORTANT: Provide the 'code' argument as a raw, unescaped string. Do not double-escape newlines or quotes.
    """
    safe_directory = pathlib.Path(__file__).parent.resolve()
    
    # Ensure the current project directory exists to prevent FileNotFoundError
    # safe_directory.mkdir(parents=True, exist_ok=True)
    
    target_path = pathlib.Path(safe_directory / filename).resolve()

    if not target_path.is_relative_to(safe_directory):
        raise ValueError("File path is outside the allowed directory.")
    
    # Ensure subdirectories exist
    target_path.parent.mkdir(parents=True, exist_ok=True)

    with open(target_path, "w", encoding="utf-8") as f:
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
        Now, please update tests/interface/test_interface.py to validate the new interface logic.
        1. Add a test for formatting bookings:
        - Create a new test named test_format_success_with_booking_list_shows_details().
        - Create a mock result dictionary with "status": "success", a "message", and "data" containing a list of two booking dictionaries (they 
            should have "patient_id", "date", and "time" keys, but no "name key).
        - Pass this result to format_response().
        - Assert that the expected patient_id, date, and time strings for both mock bookings appear in the output string.
        2. Update the unknown intent test:
        - In test_format_unknown_includes_help_text(), add an assertion to verify that the work "book" or "cancel" or "appointment" appears in the output, ensuring 
            the new help text is being properly rendered.
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