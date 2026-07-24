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
        I need additional tests to cover the following gap in my test suite.
        Context: Read the relevant source file and its existing test file.
        Gap identified: in src/storage/storage_handler.py is not being tested (test file: tests/storage/test_storage.py). It involves testing "success", both "not_found", and "error" paths in delete_patient().
        Requirements:
        1. Write a pytest test function with a descriptive name (may need more than one).
        2. The test must exercise the specific uncovered path.
        3. Use ONLY the same mocking patterns already established in the test file (e.g., unittest.mock.patch for storage functions).
        4. Do not modify existing tests.
        5. The new test must pass.
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