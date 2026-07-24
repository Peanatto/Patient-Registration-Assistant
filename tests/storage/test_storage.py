import pytest
from unittest.mock import patch, MagicMock
from src.storage.storage_handler import save_patient, _get_worksheet, SPREADSHEET_NAME, _SERVICE_ACCOUNT_PATH, get_patients, delete_patient, verify_patient, save_booking, get_bookings, delete_booking

# Test 1: Happy Path
def test_save_new_patient_success():
    sample_data = {
        "name": "Alice Doe", 
        "date_of_birth": "1990-05-15", 
        "patient_id": "PT-12345", 
        "medications": "Acetaminophen", 
    }
    result = save_patient(sample_data)
    assert result == "success"

# Test 2: Conflict Path (Duplicate)
def test_duplicate_patient_id_prevention():
    sample_data = {
        "name": "Alice Doe", 
        "date_of_birth": "1990-05-15", 
        "patient_id": "PT-12345", 
        "medications": "Acetaminophen", 
    }
    save_patient(sample_data)
    result = save_patient(sample_data)
    assert result == "exists"

# Test 3: Error Path (Incomplete Data)
def test_missing_fields_error():
    incomplete_data = {"name": "Bob"}  # Missing date_of_birth, patient_id, medications
    result = save_patient(incomplete_data)
    assert result == "error"

# Test 4: _get_worksheet covering lines 28-29
def test_get_worksheet_successful_access():
    """
    Tests that _get_worksheet successfully authenticates and opens the correct sheet.
    """
    from src.storage.storage_handler import _get_worksheet, _SERVICE_ACCOUNT_PATH, SPREADSHEET_NAME
    with patch('gspread.service_account') as mock_service_account:
        mock_client = MagicMock()
        mock_service_account.return_value = mock_client

        mock_spreadsheet = MagicMock()
        mock_client.open.return_value = mock_spreadsheet

        # Call the function under test with a tab name
        _get_worksheet("Patients")

        # Assertions
        mock_service_account.assert_called_once_with(filename=str(_SERVICE_ACCOUNT_PATH))
        mock_client.open.assert_called_once_with(SPREADSHEET_NAME)
        # Verify that the specific worksheet tab was requested
        mock_spreadsheet.worksheet.assert_called_once_with("Patients")

# New test for lines 59-60 in src/storage/storage_handler.py (exception handling)
def test_save_patient_exception_during_worksheet_access():
    """
    Tests the exception handling path in save_patient when _get_worksheet fails.
    This covers lines 59-60 (the start of the try block) and 67-68 (except block)
    in src/storage/storage_handler.py.
    """
    sample_data = {
        "name": "Charlie Brown",
        "date_of_birth": "1960-10-02",
        "patient_id": "CB-00001",
        "medications": "Peanuts",
    }
    with patch('src.storage.storage_handler._get_worksheet', side_effect=Exception("Mock worksheet error")):\
        result = save_patient(sample_data)
    assert result == "error"

def test_get_patients_success():
    """
    Tests the successful retrieval of patient records using get_patients.
    This covers the success path in src/storage/storage_handler.py for get_patients.
    """
    mock_patients_data = [
        {"name": "Patient A", "date_of_birth": "2000-01-01", "patient_id": "PA-001", "medications": "None"},
        {"name": "Patient B", "date_of_birth": "1995-05-10", "patient_id": "PB-002", "medications": "Aspirin"},
    ]
    with patch('src.storage.storage_handler._get_worksheet') as mock_get_worksheet:
        mock_worksheet = MagicMock()
        mock_get_worksheet.return_value = mock_worksheet
        mock_worksheet.get_all_records.return_value = mock_patients_data

        result = get_patients()
        
        mock_get_worksheet.assert_called_once()
        mock_worksheet.get_all_records.assert_called_once()
        assert result == mock_patients_data

def test_get_patients_exception_handling():
    """
    Tests the exception handling in get_patients, ensuring it returns an empty list on failure.
    This covers the exception path in src/storage/storage_handler.py for get_patients.
    """
    with patch('src.storage.storage_handler._get_worksheet', side_effect=Exception("Worksheet access failed")):\
        result = get_patients()
    assert result == []

    with patch('src.storage.storage_handler._get_worksheet') as mock_get_worksheet:
        mock_worksheet = MagicMock()
        mock_get_worksheet.return_value = mock_worksheet
        mock_worksheet.get_all_records.side_effect = Exception("Failed to get records")

        result = get_patients()
        
        mock_get_worksheet.assert_called_once()
        mock_worksheet.get_all_records.assert_called_once()
        assert result == []

# --- New tests for delete_patient ---

def test_delete_patient_success():
    """
    Tests the successful deletion of a patient record.
    """
    with patch('src.storage.storage_handler._get_worksheet') as mock_get_worksheet:
        mock_worksheet = MagicMock()
        mock_get_worksheet.return_value = mock_worksheet
        
        mock_cell = MagicMock()
        mock_cell.row = 2 # Simulate a found cell not in the header row
        mock_worksheet.find.return_value = mock_cell

        patient_id_to_delete = "PT-999"
        result = delete_patient(patient_id_to_delete)

        mock_get_worksheet.assert_called_once()
        mock_worksheet.find.assert_called_once_with(patient_id_to_delete, in_column=3) # _ID_COL is 3
        mock_worksheet.delete_rows.assert_called_once_with(2)
        assert result == "success"

def test_delete_patient_not_found_no_cell():
    """
    Tests deletion when the patient ID is not found (find returns None).
    """
    with patch('src.storage.storage_handler._get_worksheet') as mock_get_worksheet:
        mock_worksheet = MagicMock()
        mock_get_worksheet.return_value = mock_worksheet
        
        mock_worksheet.find.return_value = None # Simulate patient not found

        patient_id_to_delete = "NON-EXISTENT"
        result = delete_patient(patient_id_to_delete)

        mock_get_worksheet.assert_called_once()
        mock_worksheet.find.assert_called_once_with(patient_id_to_delete, in_column=3)
        mock_worksheet.delete_rows.assert_not_called() # Ensure delete_rows is not called
        assert result == "not_found"

def test_delete_patient_not_found_header_row():
    """
    Tests deletion when the patient ID is found in the header row (row 1).
    """
    with patch('src.storage.storage_handler._get_worksheet') as mock_get_worksheet:
        mock_worksheet = MagicMock()
        mock_get_worksheet.return_value = mock_worksheet
        
        mock_cell = MagicMock()
        mock_cell.row = 1 # Simulate finding the ID in the header row
        mock_worksheet.find.return_value = mock_cell

        patient_id_to_delete = "patient_id" # This would be the header value
        result = delete_patient(patient_id_to_delete)

        mock_get_worksheet.assert_called_once()
        mock_worksheet.find.assert_called_once_with(patient_id_to_delete, in_column=3)
        mock_worksheet.delete_rows.assert_not_called() # Ensure delete_rows is not called
        assert result == "not_found"

def test_delete_patient_error_on_worksheet_access():
    """
    Tests exception handling when _get_worksheet fails during deletion.
    """
    with patch('src.storage.storage_handler._get_worksheet', side_effect=Exception("Worksheet access error")):\
        patient_id_to_delete = "ANY-ID"
    result = delete_patient(patient_id_to_delete)
    assert result == "error"

def test_delete_patient_error_on_find():
    """
    Tests exception handling when worksheet.find raises an exception.
    """
    with patch('src.storage.storage_handler._get_worksheet') as mock_get_worksheet:
        mock_worksheet = MagicMock()
        mock_get_worksheet.return_value = mock_worksheet
        
        mock_worksheet.find.side_effect = Exception("Find operation failed")

        patient_id_to_delete = "ERROR-ID"
        result = delete_patient(patient_id_to_delete)

        mock_get_worksheet.assert_called_once()
        mock_worksheet.find.assert_called_once_with(patient_id_to_delete, in_column=3)
        assert result == "error"

def test_delete_patient_error_on_delete_rows():
    """
    Tests exception handling when worksheet.delete_rows raises an exception.
    """
    with patch('src.storage.storage_handler._get_worksheet') as mock_get_worksheet:
        mock_worksheet = MagicMock()
        mock_get_worksheet.return_value = mock_worksheet
        
        mock_cell = MagicMock()
        mock_cell.row = 5
        mock_worksheet.find.return_value = mock_cell
        mock_worksheet.delete_rows.side_effect = Exception("Delete operation failed")

        patient_id_to_delete = "ERROR-DEL"
        result = delete_patient(patient_id_to_delete)

        mock_get_worksheet.assert_called_once()
        mock_worksheet.find.assert_called_once_with(patient_id_to_delete, in_column=3)
        mock_worksheet.delete_rows.assert_called_once_with(5)
        assert result == "error"


# --- New tests for verify_patient ---

def test_verify_patient_true():
    """Tests verify_patient when the patient exists."""
    with patch('src.storage.storage_handler._get_worksheet') as mock_get_worksheet, \
         patch('src.storage.storage_handler._existing_ids') as mock_existing_ids:
        
        mock_worksheet = MagicMock()
        mock_get_worksheet.return_value = mock_worksheet
        mock_existing_ids.return_value = {"pt-12345", "pt-99999"}
        
        result = verify_patient("PT-12345")
        
        mock_get_worksheet.assert_called_once_with("Patients")
        assert result is True

def test_verify_patient_false():
    """Tests verify_patient when the patient does not exist."""
    with patch('src.storage.storage_handler._get_worksheet') as mock_get_worksheet, \
         patch('src.storage.storage_handler._existing_ids') as mock_existing_ids:
        
        mock_worksheet = MagicMock()
        mock_get_worksheet.return_value = mock_worksheet
        mock_existing_ids.return_value = {"pt-12345"}
        
        result = verify_patient("PT-00000")
        
        assert result is False

def test_verify_patient_exception():
    """Tests exception handling in verify_patient."""
    with patch('src.storage.storage_handler._get_worksheet', side_effect=Exception("API Error")):
        result = verify_patient("PT-12345")
        assert result is False

# --- New tests for save_booking ---

def test_save_booking_success():
    """
    Tests successful appendage of an appointment when no conflict exists.
    """
    with patch('src.storage.storage_handler._get_worksheet') as mock_get_worksheet:
        mock_worksheet = MagicMock()
        mock_get_worksheet.return_value = mock_worksheet

        mock_worksheet.get_all_records.return_value = []
        
        result = save_booking("PT-12345", "10-15-2026", "2:00 PM")
        
        mock_get_worksheet.assert_called_once_with("Appointments")
        mock_worksheet.get_all_records.assert_called_once()
        mock_worksheet.append_row.assert_called_once_with(["PT-12345", "10-15-2026", "2:00 PM"])
        assert result == "success"

def test_save_booking_conflict_prevents_overlap():
    """
    Tests that a booking returns 'conflict' if the date and time are already taken.
    """
    with patch('src.storage.storage_handler._get_worksheet') as mock_get_worksheet:
        mock_worksheet = MagicMock()
        mock_get_worksheet.return_value = mock_worksheet
        
        # Mock an existing appointment at the exact same date and time (different patient)
        mock_worksheet.get_all_records.return_value = [
            {"patient_id": "PT-99999", "date": "10-15-2026", "time": "2:00 PM"}
        ]
        
        # Attempt to book the same slot for a new patient
        result = save_booking("PT-12345", "10-15-2026", "2:00 PM")
        
        # Assert the conflict is caught and append_row is NEVER called
        assert result == "conflict"
        mock_worksheet.append_row.assert_not_called()

def test_save_booking_exception():
    """
    Tests exception handling during save_booking.
    """
    with patch('src.storage.storage_handler._get_worksheet') as mock_get_worksheet:
        mock_worksheet = MagicMock()
        mock_get_worksheet.return_value = mock_worksheet
        mock_worksheet.append_row.side_effect = Exception("Write error")
        
        result = save_booking("PT-12345", "10-15-2026", "2:00 PM")
        
        assert result == "error"

# --- New tests for get_bookings ---
def test_get_bookings_success():
    """
    Tests the successful retrieval of appointment records using get_bookings.
    """
    mock_bookings_data = [
        {"patient_id": "PT-001", "date": "2023-11-01", "time": "10:00 AM"},
        {"patient_id": "PT-002", "date": "2023-11-02", "time": "11:00 AM"},
    ]
    with patch('src.storage.storage_handler._get_worksheet') as mock_get_worksheet:
        mock_worksheet = MagicMock()
        mock_get_worksheet.return_value = mock_worksheet
        mock_worksheet.get_all_records.return_value = mock_bookings_data

        result = get_bookings()
        
        mock_get_worksheet.assert_called_once_with("Appointments")
        mock_worksheet.get_all_records.assert_called_once()
        assert result == mock_bookings_data

def test_get_bookings_exception_handling():
    """
    Tests the exception handling in get_bookings, ensuring it returns an empty list on failure.
    """
    with patch('src.storage.storage_handler._get_worksheet', side_effect=Exception("Worksheet access failed")):\
        result = get_bookings()
    assert result == []

    with patch('src.storage.storage_handler._get_worksheet') as mock_get_worksheet:
        mock_worksheet = MagicMock()
        mock_get_worksheet.return_value = mock_worksheet
        mock_worksheet.get_all_records.side_effect = Exception("Failed to get records")

        result = get_bookings()
        
        mock_get_worksheet.assert_called_once()
        mock_worksheet.get_all_records.assert_called_once()
        assert result == []

# --- New tests for delete_booking ---
def test_delete_booking_success():
    """
    Tests the successful deletion of an appointment record.
    """
    mock_appointments_data = [
        {"patient_id": "PT-001", "date": "2023-11-01", "time": "10:00 AM"},
        {"patient_id": "PT-002", "date": "2023-11-02", "time": "11:00 AM"},
        {"patient_id": "PT-001", "date": "2023-11-03", "time": "09:00 AM"},
    ]
    with patch('src.storage.storage_handler._get_worksheet') as mock_get_worksheet:
        mock_worksheet = MagicMock()
        mock_get_worksheet.return_value = mock_worksheet
        mock_worksheet.get_all_records.return_value = mock_appointments_data

        patient_id_to_delete = "PT-002"
        date_to_delete = "2023-11-02"
        time_to_delete = "11:00 AM"
        result = delete_booking(patient_id_to_delete, date_to_delete, time_to_delete)

        mock_get_worksheet.assert_called_once_with("Appointments")
        mock_worksheet.get_all_records.assert_called_once()
        # The row index in gspread is 1-based, and there's a header row, so index 1 (0-based) is row 2.
        mock_worksheet.delete_rows.assert_called_once_with(3) # PT-002 is at 0-indexed position 1, so 1+2 = 3
        assert result == "success"

def test_delete_booking_not_found():
    """
    Tests deletion when the exact appointment is not found.
    """
    mock_appointments_data = [
        {"patient_id": "PT-001", "date": "2023-11-01", "time": "10:00 AM"},
        {"patient_id": "PT-002", "date": "2023-11-02", "time": "11:00 AM"},
    ]
    with patch('src.storage.storage_handler._get_worksheet') as mock_get_worksheet:
        mock_worksheet = MagicMock()
        mock_get_worksheet.return_value = mock_worksheet
        mock_worksheet.get_all_records.return_value = mock_appointments_data

        # Mismatch in time
        result = delete_booking("PT-001", "2023-11-01", "10:30 AM")

        mock_get_worksheet.assert_called_once_with("Appointments")
        mock_worksheet.get_all_records.assert_called_once()
        mock_worksheet.delete_rows.assert_not_called() # Ensure delete_rows is not called
        assert result == "not_found"

def test_delete_booking_error_on_worksheet_access():
    """
    Tests exception handling when _get_worksheet fails during delete_booking.
    """
    with patch('src.storage.storage_handler._get_worksheet', side_effect=Exception("Worksheet access error")):\
        result = delete_booking("PT-ANY", "ANY-DATE", "ANY-TIME")
    assert result == "error"

def test_delete_booking_error_on_get_all_records():
    """
    Tests exception handling when get_all_records fails during delete_booking.
    """
    with patch('src.storage.storage_handler._get_worksheet') as mock_get_worksheet:
        mock_worksheet = MagicMock()
        mock_get_worksheet.return_value = mock_worksheet
        mock_worksheet.get_all_records.side_effect = Exception("Failed to get all records")

        result = delete_booking("PT-ANY", "ANY-DATE", "ANY-TIME")
        
        mock_get_worksheet.assert_called_once()
        mock_worksheet.get_all_records.assert_called_once()
        assert result == "error"