"""Unified storage layer: CRUD operations for patient records via Google Sheets."""

from __future__ import annotations

import os
from pathlib import Path

import gspread

# --- Schema Definitions ---
# The exact keys required to successfully register a new patient.
REQUIRED_KEYS = {"name", "date_of_birth", "patient_id", "medications"}

# Sheet header order; must match the actual spreadsheet column layout exactly.
_COLUMNS = ["name", "date_of_birth", "patient_id", "medications"]

# Column position (1-indexed) of the Patient ID field used for deduplication and deletion.
_ID_COL = _COLUMNS.index("patient_id") + 1

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_SERVICE_ACCOUNT_PATH = _PROJECT_ROOT / "service_account.json"

SPREADSHEET_NAME = os.environ.get("SPREADSHEET_NAME", "patient-registration-assistant-records")


def _get_worksheet() -> gspread.Worksheet:
    """Single standardized authentication helper to open the primary worksheet."""
    client = gspread.service_account(filename=str(_SERVICE_ACCOUNT_PATH))
    return client.open(SPREADSHEET_NAME).sheet1


def _existing_ids(worksheet: gspread.Worksheet) -> set[str]:
    """Fetch all existing patient IDs to prevent duplicate registrations."""
    all_values = worksheet.col_values(_ID_COL)
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
        worksheet = _get_worksheet()

        # Check for duplicates using patient_id instead of email
        if patient_data["patient_id"].strip().lower() in _existing_ids(worksheet):
            return "exists"

        worksheet.append_row([patient_data[col] for col in _COLUMNS])
        return "success"

    except Exception:
        return "error"


def get_patients() -> list[dict]:
    """Return all patient records as a list of dicts keyed by the header row.

    Returns [] when the sheet has no data rows or on any exception.
    """
    try:
        worksheet = _get_worksheet()
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
        worksheet = _get_worksheet()
        # Find the patient by their ID in column 3 (or whatever _ID_COL evaluates to)
        cell = worksheet.find(patient_id, in_column=_ID_COL)
        if cell is None:
            return "not_found"
        # Guard against accidentally matching the header row.
        if cell.row == 1:
            return "not_found"
        worksheet.delete_rows(cell.row)
        return "success"
    except Exception:
        return "error"