from __future__ import annotations

# Import process_request at the top so the patch path
# "src.interface.cli.process_request" is valid in tests.
from src.engine.engine import process_request

_WELCOME_BANNER = """
========================================
  Patient Registration Assistant
  Type 'quit' or 'exit' to stop.
========================================
"""

_HELP_TEXT = (
    "I can help you:\n"
    "  - Register a new patient\n"
    "  - List all registered patients\n"
    "  - Delete a patient record\n"
    "  - Book an appointment\n"
    "  - List all bookings\n"
    "  - Cancel an appointment\n"
    "  - Answer questions about patient records\n"
    "Just describe what you want in plain English."
)


def format_response(result: dict) -> str:
    """Convert an engine result dict to a human-readable string.

    Expected result shapes (from engine.process_request):
        {"status": "success",    "message": str, "data": list | None}
        {"status": "exists",     "message": str, "data": None}
        {"status": "incomplete", "message": str, "missing": list}
        {"status": "unknown",    "message": str, "data": None}
        {"status": "error",      "message": str, "data": None}

    Always returns a plain string - never raises.
    """
    status = result.get("status")
    message = result.get("message", "Unexpected response.")

    if status == "success":
        response_str = message
        data = result.get("data")
        if isinstance(data, list) and data:
            for item in data:
                if "name" in item:  # Assume it's a patient
                    name = item.get("name", "Unknown Name")
                    patient_id = item.get("patient_id", "Unknown ID")
                    response_str += f"\n  - {name} (ID: {patient_id})"
                else:  # Assume it's a booking
                    patient_id = item.get("patient_id", "Unknown Patient ID")
                    date = item.get("date", "Unknown Date")
                    time = item.get("time", "Unknown Time")
                    response_str += f"\n  - Appointment for {patient_id} on {date} at {time}."
        return response_str
    elif status == "exists":
        return message
    elif status == "incomplete":
        missing_fields = result.get("missing", [])
        return message + "\n  Missing: " + ", ".join(missing_fields)
    elif status == "unknown":
        return message + "\n\n" + _HELP_TEXT
    else:  # "error" and all other statuses
        return message


def run_session(process_fn=None):
    """Run a REPL session: read input, call engine, print formatted response.

    Parameters
    ----------
    process_fn:
        Callable that accepts a str and returns a dict.  Defaults to
        process_request from the engine layer.  Pass a mock here in tests
        so the session runs without a live AI or Google Sheets connection.
    """
    if process_fn is None:
        process_fn = process_request

    print(_WELCOME_BANNER)

    while True:
        try:
            user_input = input("You: ")
            stripped_input = user_input.strip()

            if not stripped_input:
                continue

            if stripped_input.lower() in ("quit", "exit"):
                print("Goodbye!")
                return

            result = process_fn(stripped_input)
            print("Assistant: " + format_response(result))
            print() # Blank line for readability

        except EOFError:
            print("Goodbye!")
            return


if __name__ == "__main__":
    run_session()
