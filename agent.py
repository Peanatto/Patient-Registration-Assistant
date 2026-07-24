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
        I need a user-facing README.md for my project.

        Context: Read FUNCTIONALITY.md, CONTRACT.md, cli.py, and requirements.txt.
        Goal: Write README.md at the project root.

        Sections to include:

        1. Project name & Description: A one-paragraph description of what the Patient Registration Assistant does.

        2. Setup: List every dependency and one-time configuration step. CRITICAL: You must explicitly instruct the user to create a .env file in the root directory and add GEMINI_API_KEY=your_api_key_here.

        3. How to run: Provide the exact command to start the app (python -m src.interface.cli).

        4. Usage examples: Provide 3-4 example inputs with their expected outputs, covering the core functionalities in FUNCTIONALITY.md (Registration, Inquiry, Booking).

        - Constraint 1: Any example referencing a Patient ID MUST strictly use the format PT-XXXXXXXX (e.g., PT-85858585).

        - Constraint 2: The "Expected Output" in these examples must visually match the exact formatting logic found in the format_response function in src/interface/cli.py (e.g., list items must be formatted as   - Name (ID: PT-XXXXXXXX)).

        5. Project structure: A brief directory tree, list, or table explaining the layout of src/ and tests/. Include design docs and any other important branches.

        6. Demo Video: Include a placeholder header and text for a 10-minute project demo video link.

        Tone: Keep the tone practical, professional, and clean. Do not include lab instructions, assignment details, or academic context.
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