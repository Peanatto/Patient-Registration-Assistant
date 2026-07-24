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
        I need to add appointment booking functionality to my JSON-extracting engine. src/engine/engine.py is done. ONLY implement tests.
        1. Update src/engine/engine.py:
        - Import save_booking and verify_patient from src.storage.storage_handler.
        - Update _EXTRACTION_PROMPT to include a new intent: "book". Instruct it to extract date (MM-DD-YYYY) and time into the data dictionary.
        - Update _REFLECTION_PROMPT to add a fule: "The "book" intent requires exactly three fields: patient_id, date, and time.
        - In the Step 3 Dispatch block, add an elif intent == "book": path.
        - Crucial Logic: Before calling save_booking, use verify_patient(patient_id). If it returns false, return a "not_found" status with a message 
            that the patient ID was not found. If True, proceed to save_booking and return the appropriate "success" or "error" status dicts.
        2. Look into src/engine/engine.py and update tests/engine/test_engine.py:
        Add four new tests using @patch:
        - Test 1: Booking success (patch verify_patient to return True, patch save_booking to return "success").
        - Test 2: Booking patient not found (patch verify_patient to return False—ensure save_booking is NOT called).
        - Test 3: Booking incomplete (prompt the engine to "book an appointment for PT-12345432" without a date/time. Expect an "incomplete" status from the reflection step).
        - Test 4: Booking storage error (patch verify_patient to return True, patch save_booking to return "error").
        Ensure all patches use the correct usage path: src.engine.engine.<function_name>.
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