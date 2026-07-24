import pytest
from unittest.mock import patch, MagicMock
from src.storage.storage_handler import save_patient, _get_worksheet, SPREADSHEET_NAME, _SERVICE_ACCOUNT_PATH, get_patients, delete_patient

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
    This covers lines 28-29 in src/storage/storage_handler.py.
    """
    with patch('gspread.service_account') as mock_service_account:
        mock_client = MagicMock()
        mock_service_account.return_value = mock_client

        mock_spreadsheet = MagicMock()
        mock_client.open.return_value = mock_spreadsheet

        mock_worksheet = MagicMock()
        # Mocking .sheet1 as an attribute directly, as it's typically accessed like that
        type(mock_spreadsheet).sheet1 = MagicMock(return_value=mock_worksheet)


        # Call the function under test
        returned_worksheet = _get_worksheet()

        # Assertions
        mock_service_account.assert_called_once_with(filename=str(_SERVICE_ACCOUNT_PATH))
        mock_client.open.assert_called_once_with(SPREADSHEET_NAME)
        # Verify that sheet1 was accessed. Since it's an attribute, we check the returned object.
        assert returned_worksheet == mock_spreadsheet.sheet1

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