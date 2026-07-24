"""Engine layer implementation for the Patient Registration Assistant.

The engine is the Logic Layer of the system.

Architecture position:
    interface -> engine -> storage

This module receives raw user input, uses the Tool Use pattern to determine
what clinical storage operation to perform, then uses the Reflection pattern to
validate its own interpretation (checking medical data completeness) before acting.

Replace every TODO with your implementation guided by the tests and your agent.py.
"""

from __future__ import annotations

import json
import os

from dotenv import load_dotenv

# Import unified storage functions at the top so tests can patch them via
# "src.engine.engine.save_patient" (the path where they are USED).
from src.storage.storage_handler import delete_patient, get_patients, save_patient, save_booking, verify_patient
from google import genai
from google.genai import types
from google.genai.types import HttpOptions

load_dotenv()

_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
_MODEL = os.getenv("MODEL_NAME", "gemini-2.5-flash")

# --- Prompts ---

_EXTRACTION_PROMPT = """
You are a Clinical Intake Engine for a Patient Registration Assistant. Analyze the user request and extract:
- intent: exactly one of "register", "list", "delete", "book", "unknown"
- data: a dict containing any fields mentioned (name, date_of_birth, patient_id, medications, date, time)
- date_of_birth must be output in MM-DD-YYYY format
- date for booking must be output in MM-DD-YYYY format
- medications must be separated by commas

Return strict JSON only - no extra text:
{"intent": "<intent>", "data": {}}
""".strip()

_REFLECTION_PROMPT = """
You are a clinical data completeness validator.

Extracted data and intent:
{extracted}

Validation rules:
- "register" intent requires all four fields: name, date_of_birth, patient_id, medications.
- The "book" intent requires exactly three fields: patient_id, date, and time.
- patient_id must be of the form PT-XXXXXXXX
- "list", "delete", and "unknown" intents have no required fields.

Return strict JSON only - no extra text:
{{"complete": <true|false>, "missing": ["<field>", ...]}}
""".strip()


def process_request(user_input: str) -> dict:
    """Process a patient intake request using Tool Use and Reflection patterns.

    Return contract (every path returns a dict with "status" and "message"):
    - {"status": "success",    "message": str, "data": list | None}
    - {"status": "exists",     "message": str, "data": None}
    - {"status": "incomplete", "message": str, "missing": list}
    - {"status": "unknown",    "message": str, "data": None}
    - {"status": "error",      "message": str, "data": None}
    - {"status": "not_found",  "message": str, "data": None}
    """
    try:
        # Initialize the client.
        client = genai.Client(api_key=_API_KEY, http_options=HttpOptions(api_version="v1"))

        # ----------------------------------------------------------------
        # Step 1 - Tool Use: extract clinical intent and patient data
        # ----------------------------------------------------------------
        extraction_response = client.models.generate_content(
            model=_MODEL,
            contents=user_input,
            config=types.GenerateContentConfig(
                system_instruction=_EXTRACTION_PROMPT,
                response_mime_type="application/json",
            ),
        )
        extraction_result = json.loads(extraction_response.text)
        intent = extraction_result.get("intent")
        data = extraction_result.get("data", {})

        # ----------------------------------------------------------------
        # Step 2 - Reflection: validate patient record completeness before acting
        # ----------------------------------------------------------------
        reflection_prompt_formatted = _REFLECTION_PROMPT.format(extracted=json.dumps(extraction_result))
        reflection_response = client.models.generate_content(
            model=_MODEL,
            contents=reflection_prompt_formatted,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        reflection_result = json.loads(reflection_response.text)

        if not reflection_result.get("complete"):
            return {
                "status": "incomplete",
                "message": "Missing required patient registration fields.",
                "missing": reflection_result.get("missing", []),
            }

        # ----------------------------------------------------------------
        # Step 3 - Dispatch: call the correct unified patient storage function
        # ----------------------------------------------------------------
        if intent == "register":
            storage_result = save_patient(data)
            if storage_result == "success":
                return {"status": "success", "message": "Patient registered successfully.", "data": None}
            elif storage_result == "exists":
                return {"status": "exists", "message": "Patient record already exists.", "data": None}
            else: # "error"
                return {"status": "error", "message": "Storage error while saving patient.", "data": None}

        elif intent == "list":
            patients = get_patients()
            return {"status": "success", "message": f"{len(patients)} patient record(s) found.", "data": patients}

        elif intent == "delete":
            patient_id_to_delete = data.get("patient_id")
            if not patient_id_to_delete:
                return {"status": "error", "message": "Patient ID not provided for deletion.", "data": None}

            storage_result = delete_patient(patient_id_to_delete)
            if storage_result == "success":
                return {"status": "success", "message": "Patient record deleted.", "data": None}
            elif storage_result == "not_found":
                return {"status": "not_found", "message": "Patient record not found.", "data": None}
            else: # "error"
                return {"status": "error", "message": "Storage error during deletion.", "data": None}
        
        elif intent == "book":
            patient_id = data.get("patient_id")
            date = data.get("date")
            time = data.get("time")

            if not verify_patient(patient_id):
                return {"status": "not_found", "message": "Patient ID not found.", "data": None}
            
            booking_result = save_booking(patient_id, date, time)
            if booking_result == "success":
                return {"status": "success", "message": "Appointment booked successfully.", "data": None}
            else: # "error"
                return {"status": "error", "message": "Storage error while booking appointment.", "data": None}


        else:  # unknown intent
            return {"status": "unknown", "message": "I can register patients, list records, delete patient files, or book appointments. Please specify your request.", "data": None}

    except Exception as exc:
        return {"status": "error", "message": str(exc), "data": None}
