"""Unified storage layer: CRUD operations for patient records via Google Sheets."""

from __future__ import annotations

import os
from pathlib import Path

import gspread

# --- Schema Definitions ---
# The exact keys required to successfully register a new patient.
REQUIRED_KEYS = {"name", "date_of_birth", "patient_id", "medications"}

# Sheet header order for "Patients" tab; must match the actual spreadsheet column layout exactly.
_PATIENTS_COLUMNS = ["name", "date_of_birth", "patient_id", "medications"]

# Column position (1-indexed) of the Patient ID field used for deduplication and deletion.
_PATIENT_ID_COL_INDEX = _PATIENTS_COLUMNS.index("patient_id") + 1

# Sheet header order for "Appointments" tab.
_APPOINTMENTS_COLUMNS = ["patient_id", "date", "time"]

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_SERVICE_ACCOUNT_PATH = _PROJECT_ROOT / "service_account.json"

SPREADSHEET_NAME = os.environ.get("SPREADSHEET_NAME", "patient-registration-assistant-records")


def _get_worksheet(tab_name: str) -> gspread.Worksheet:
    """Single standardized authentication helper to open a specific worksheet tab."""
    client = gspread.service_account(filename=str(_SERVICE_ACCOUNT_PATH))
    return client.open(SPREADSHEET_NAME).worksheet(tab_name)


def _existing_ids(worksheet: gspread.Worksheet, id_column_index: int) -> set[str]:
    """Fetch all existing patient IDs to prevent duplicate registrations."""
    all_values = worksheet.col_values(id_column_index)
    return {v.strip().lower() for v in all_values[1:] if v}  # skip header row


def save_patient(patient_data: dict) -> str:
    """Persist a patient record to Google Sheets.

    Returns:
        "success"  - record appended.
        "exists"   - patient_id already present; no write performed.
        "error"    - missing required fields or any unexpected exception.
    """
    if not REQUIRED_KEYS.issubset(patient_data):
        return "error"

    try:
        worksheet = _get_worksheet("Patients")

        # Check for duplicates using patient_id
        if patient_data["patient_id"].strip().lower() in _existing_ids(worksheet, _PATIENT_ID_COL_INDEX):
            return "exists"

        worksheet.append_row([patient_data[col] for col in _PATIENTS_COLUMNS])
        return "success"

    except Exception:
        return "error"


def get_patients() -> list[dict]:
    """Return all patient records as a list of dicts keyed by the header row.

    Returns [] when the sheet has no data rows or on any exception.
    """
    try:
        worksheet = _get_worksheet("Patients")
        return worksheet.get_all_records()
    except Exception:
        return []


def delete_patient(patient_id: str) -> str:
    """Delete the first row whose patient_id column matches the provided ID.

    Returns:
        "success"   - matching row found and deleted.
        "not_found" - no row contains that patient_id value.
        "error"     - any exception during the operation.
    """
    try:
        worksheet = _get_worksheet("Patients")
        # Find the patient by their ID in column _PATIENT_ID_COL_INDEX
        cell = worksheet.find(patient_id, in_column=_PATIENT_ID_COL_INDEX)
        if cell is None:
            return "not_found"
        # Guard against accidentally matching the header row.
        if cell.row == 1:
            return "not_found"
        worksheet.delete_rows(cell.row)
        return "success"
    except Exception:
        return "error"


def verify_patient(patient_id: str) -> bool:
    """Checks if a patient ID exists in the "Patients" tab."""
    try:
        worksheet = _get_worksheet("Patients")
        return patient_id.strip().lower() in _existing_ids(worksheet, _PATIENT_ID_COL_INDEX)
    except Exception:
        return False


def save_booking(patient_id: str, date: str, time: str) -> str:
    """Appends a row to the "Appointments" tab.

    Returns:
        "success" - record appended.
        "conflict" - date and time already taken.
        "error"   - any unexpected exception.
    """
    try:
        worksheet = _get_worksheet("Appointments")

        # Overlap check: ensure the date and time aren't already taken globally
        existing_bookings = worksheet.get_all_records()
        
        # Normalize the target date and time
        target_date = date.strip().lower()
        target_time = time.strip().lower()
        
        for booking in existing_bookings:
            # 1. Cast sheet values to strings
            # 2. Provide a fallback to avoid NoneType errors
            # 3. Normalize casing and whitespace
            sheet_date = str(booking.get("date", "")).strip().lower()
            sheet_time = str(booking.get("time", "")).strip().lower()
            
            if sheet_date == target_date and sheet_time == target_time:
                return "conflict"

        # Note: We append the original variables to preserve the user's intended casing
        worksheet.append_row([patient_id, date, time])
        return "success"
    except Exception:
        return "error"

def get_bookings() -> list[dict]:
    """Return all appointment records as a list of dicts keyed by the header row.

    Returns [] when the sheet has no data rows or on any exception.
    """
    try:
        worksheet = _get_worksheet("Appointments")
        return worksheet.get_all_records()
    except Exception:
        return []

def delete_booking(patient_id: str, date: str, time: str) -> str:
    """Delete the first row in "Appointments" whose patient_id, date, and time
    columns match the provided values exactly.

    Returns:
        "success"   - matching row found and deleted.
        "not_found" - no row contains the exact patient_id, date, and time.
        "error"     - any exception during the operation.
    """
    try:
        worksheet = _get_worksheet("Appointments")
        all_records = worksheet.get_all_records()

        row_to_delete = -1 # Initialize with a value indicating not found

        for i, record in enumerate(all_records):
            # 1. Cast to string to prevent gspread numeric/float type mismatches
            # 2. Use .get(key, "") as a fallback to prevent NoneType errors
            # 3. Normalize with .strip().lower()
            sheet_id = str(record.get("patient_id", "")).strip().lower()
            sheet_date = str(record.get("date", "")).strip().lower()
            sheet_time = str(record.get("time", "")).strip().lower()

            target_id = patient_id.strip().lower()
            target_date = date.strip().lower()
            target_time = time.strip().lower()

            if (sheet_id == target_id and 
                sheet_date == target_date and 
                sheet_time == target_time):
                
                row_to_delete = i + 2  # +1 for 1-based index, +1 for header row
                break

        if row_to_delete != -1:
            worksheet.delete_rows(row_to_delete)
            return "success"
        else:
            return "not_found"

    except Exception:
        return "error"
