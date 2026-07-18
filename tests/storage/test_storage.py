import pytest
from src.storage.storage_handler import save_patient

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
    assert result == "incomplete"