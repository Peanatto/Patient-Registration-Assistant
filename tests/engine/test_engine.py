"""Unit tests for the engine layer (Tool Use + Reflection patterns).

Storage functions are mocked so these tests run without Google Sheets credentials.
The AI calls (Gemini) are real — ensure GEMINI_API_KEY is set in .env.

Run:
    pytest tests/engine/test_engine.py -v

Key concept: the patch path is "src.engine.engine.<function>" because that is
where the function is USED (imported), not where it is defined.
"""

from unittest.mock import patch

from src.engine.engine import process_request


# ---------------------------------------------------------------------------
# Test 1: Register — success path
# ---------------------------------------------------------------------------
def test_register_success_returns_correct_status():
    with patch("src.engine.engine.save_patient", return_value="success"):
        result = process_request(
            "Register Alice Chen, date_of_birth 05-05-2002, patient_id PT-12345432, medications of acetaminophen and cetirizine."
        )
    assert result["status"] == "success"
    assert "message" in result


# ---------------------------------------------------------------------------
# Test 2: Register — duplicate path
# ---------------------------------------------------------------------------
def test_register_duplicate_returns_exists_status():
    with patch("src.engine.engine.save_patient", return_value="exists"):
        result = process_request(
            "Register Alice Chen, date_of_birth 05-05-2002, patient_id PT-12345432, medications of acetaminophen and cetirizine."
        )
    assert result["status"] == "exists"
    assert "message" in result


# ---------------------------------------------------------------------------
# Test 3: List members
# ---------------------------------------------------------------------------
def test_list_patients_returns_success_with_data():
    mock_patients = [
        {"name": "Alice", "date_of_birth": "05-05-2002", "patient_id": "PT-12345432", "medications": "acetaminophen, cetirizine"}
    ]
    with patch("src.engine.engine.get_patients", return_value=mock_patients):
        result = process_request("Show me all registered patients.")
    assert result["status"] == "success"
    assert isinstance(result["data"], list)


# ---------------------------------------------------------------------------
# Test 4: Reflection — incomplete registration blocks storage call
# ---------------------------------------------------------------------------
def test_incomplete_registration_is_blocked_before_storage():
    with patch("src.engine.engine.save_patient") as mock_save:
        result = process_request("Register Bob.")  # Missing date_of_birth, patient_id, and medications
    assert result["status"] == "incomplete"
    assert "missing" in result
    # The Reflection step must prevent save_patient from ever being called.
    mock_save.assert_not_called()


# ---------------------------------------------------------------------------
# Test 5: Unknown intent — graceful fallback
# ---------------------------------------------------------------------------
def test_unknown_intent_returns_unknown_status():
    result = process_request("What is the meaning of life?")
    assert result["status"] == "unknown"
    assert "message" in result


# ---------------------------------------------------------------------------
# Test 6: Delete — success path
# ---------------------------------------------------------------------------
def test_delete_success_returns_correct_status():
    with patch("src.engine.engine.delete_patient", return_value="success") as mock_delete:
        result = process_request("Please delete the patient record for patient ID PT-12345432.")
    assert result["status"] == "success"
    assert "message" in result
    # Verify the engine actually extracted and passed the correct ID to storage
    mock_delete.assert_called_once_with("PT-12345432")


# ---------------------------------------------------------------------------
# Test 7: Delete — not found path
# ---------------------------------------------------------------------------
def test_delete_not_found_returns_correct_status():
    with patch("src.engine.engine.delete_patient", return_value="not_found"):
        result = process_request("Remove patient record with ID PT-99999999.")
    assert result["status"] == "not_found"
    assert "message" in result


# ---------------------------------------------------------------------------
# Test 8: Register — storage error path (covers line 122)
# ---------------------------------------------------------------------------
def test_register_storage_error_returns_error_status():
    with patch("src.engine.engine.save_patient", return_value="error"):
        result = process_request(
            "Register John Doe, date_of_birth 01-15-1990, patient_id PT-98765432, medications of ibuprofen."
        )
    assert result["status"] == "error"
    assert result["message"] == "Storage error while saving patient."


# ---------------------------------------------------------------------------
# Test 9: Delete — missing patient ID (covers line 131)
# ---------------------------------------------------------------------------
def test_delete_missing_patient_id_returns_error_status():
    with patch("src.engine.engine.delete_patient") as mock_delete:
        result = process_request("Delete a patient record without providing an ID.")
    assert result["status"] == "error"
    assert result["message"] == "Patient ID not provided for deletion."
    mock_delete.assert_not_called()


# ---------------------------------------------------------------------------
# Test 10: Delete — storage error path (covers line 139)
# ---------------------------------------------------------------------------
def test_delete_storage_error_returns_error_status():
    with patch("src.engine.engine.delete_patient", return_value="error"):
        result = process_request("Delete patient record PT-55555555 due to an issue.")
    assert result["status"] == "error"
    assert result["message"] == "Storage error during deletion."


# ---------------------------------------------------------------------------
# Test 11: General exception handling (covers lines 144-145)
# ---------------------------------------------------------------------------
def test_process_request_exception_handling_returns_error_status():
    with patch("src.engine.engine.genai.Client") as mock_client_class:
        mock_client_class.side_effect = ValueError("Simulated API client error")
        result = process_request("Any input will do as the client initialization will fail.")
    assert result["status"] == "error"
    assert "Simulated API client error" in result["message"]
    assert result["data"] is None

# ---------------------------------------------------------------------------
# Test 12: Booking success
# ---------------------------------------------------------------------------
def test_book_success_returns_correct_status():
    with patch("src.engine.engine.verify_patient", return_value=True) as mock_verify_patient, \
         patch("src.engine.engine.save_booking", return_value="success") as mock_save_booking:
        result = process_request("Book an appointment for PT-98765432 on 12-25-2023 at 14:00.")
    assert result["status"] == "success"
    assert "message" in result
    mock_verify_patient.assert_called_once_with("PT-98765432")
    mock_save_booking.assert_called_once_with("PT-98765432", "12-25-2023", "14:00")

# ---------------------------------------------------------------------------
# Test 13: Booking patient not found
# ---------------------------------------------------------------------------
def test_book_patient_not_found_returns_not_found_status():
    with patch("src.engine.engine.verify_patient", return_value=False) as mock_verify_patient, \
         patch("src.engine.engine.save_booking") as mock_save_booking:
        result = process_request("Book an appointment for PT-11111111 on 01-01-2024 at 10:00.")
    assert result["status"] == "not_found"
    assert "message" in result
    mock_verify_patient.assert_called_once_with("PT-11111111")
    mock_save_booking.assert_not_called()

# ---------------------------------------------------------------------------
# Test 14: Booking incomplete (missing date/time)
# ---------------------------------------------------------------------------
def test_book_incomplete_returns_incomplete_status():
    with patch("src.engine.engine.verify_patient") as mock_verify_patient, \
         patch("src.engine.engine.save_booking") as mock_save_booking:
        result = process_request("Book an appointment for PT-22222222.") # Missing date and time
    assert result["status"] == "incomplete"
    assert "missing" in result
    # The reflection should catch missing date and time
    assert "date" in result["missing"] or "time" in result["missing"]
    mock_verify_patient.assert_not_called()
    mock_save_booking.assert_not_called()

# ---------------------------------------------------------------------------
# Test 15: Booking storage error
# ---------------------------------------------------------------------------
def test_book_storage_error_returns_error_status():
    with patch("src.engine.engine.verify_patient", return_value=True) as mock_verify_patient, \
         patch("src.engine.engine.save_booking", return_value="error") as mock_save_booking:
        result = process_request("Book an appointment for PT-33333333 on 02-02-2024 at 11:30.")
    assert result["status"] == "error"
    assert "message" in result
    mock_verify_patient.assert_called_once_with("PT-33333333")
    mock_save_booking.assert_called_once_with("PT-33333333", "02-02-2024", "11:30")