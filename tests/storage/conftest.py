import pytest
import src.storage.storage_handler as handler

class _InMemoryWorksheet:
    def __init__(self, headers):
        self._rows = [headers]  # header row

    def col_values(self, col: int) -> list[str]:
        return [row[col - 1] for row in self._rows if len(row) >= col]

    def append_row(self, row: list) -> None:
        self._rows.append(row)

@pytest.fixture(autouse=True)
def in_memory_worksheet(monkeypatch, request):
    # Skip mock if this specific test is running
    if  request.node.name == "test_get_worksheet_successful_access":
        return

    # Initialize two separate mocked sheets with their respective headers
    patients_ws = _InMemoryWorksheet(["name", "date_of_birth", "patient_id", "medications"])
    appointments_ws = _InMemoryWorksheet(["patient_id", "date", "time"])
    
    # Create a replacement function that routes requests to the correct mock
    def mock_get_worksheet(tab_name="Patients", *args, **kwargs):
        if tab_name == "Appointments":
            return appointments_ws
        return patients_ws

    # Patch the handler with the new routing function instead of the lambda
    monkeypatch.setattr(handler, "_get_worksheet", mock_get_worksheet)