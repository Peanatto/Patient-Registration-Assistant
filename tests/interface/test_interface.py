"""Unit tests for the interface layer.

The engine layer is mocked — these tests run without a Gemini API key or
Google Sheets credentials.

Run:
    pytest tests/interface/test_interface.py -v

Key concept: run_session accepts process_fn so tests can inject a mock
engine directly, without patching.  format_response is a pure function
and needs no mocking at all.
"""

from src.interface.cli import format_response, run_session


# ---------------------------------------------------------------------------
# Test 1: format_response — success with a member list
# ---------------------------------------------------------------------------
def test_format_success_with_patient_list_shows_name_and_id():
    result = {
        "status": "success",
        "message": "2 patient(s) found.",
        "data": [
            {"name": "Alice Chen", "date_of_birth": "05-05-2002", "patient_id": "PT-12345432", "medications": "acetaminophen"},
            {"name": "Bob Smith", "date_of_birth": "08-04-1998", "patient_id": "PT-23456543", "medications": "ceritizine"},
        ],
    }
    output = format_response(result)
    assert "Alice Chen" in output
    assert "PT-12345432" in output
    assert "Bob Smith" in output


# ---------------------------------------------------------------------------
# Test 2: format_response — duplicate registration
# ---------------------------------------------------------------------------
def test_format_exists_shows_duplicate_message():
    result = {"status": "exists", "message": "Patient already registered.", "data": None}
    output = format_response(result)
    assert "already registered" in output


# ---------------------------------------------------------------------------
# Test 3: format_response — incomplete registration lists missing fields
# ---------------------------------------------------------------------------
def test_format_incomplete_lists_all_missing_fields():
    result = {
        "status": "incomplete",
        "message": "Missing required fields.",
        "missing": ["date_of_birth", "patient_id"],
    }
    output = format_response(result)
    assert "date_of_birth" in output
    assert "patient_id" in output


# ---------------------------------------------------------------------------
# Test 4: format_response — unknown intent includes help text
# ---------------------------------------------------------------------------
def test_format_unknown_includes_help_text():
    result = {
        "status": "unknown",
        "message": "I can register, list, or delete patients.",
        "data": None,
    }
    output = format_response(result)
    # Help text must mention at least one available action so the user knows
    # what to do next.
    assert "register" in output.lower() or "list" in output.lower() or "delete" in output.lower()


# ---------------------------------------------------------------------------
# Test 5: run_session — mocked engine, response appears in stdout
# ---------------------------------------------------------------------------
def test_run_session_prints_formatted_engine_response(monkeypatch, capsys):
    def mock_engine(user_input):
        return {"status": "success", "message": "Patient registered.", "data": None}

    # Simulate: one message, then quit.
    inputs = iter(
        ["Register Alice Chen, date_of_birth May 5, 2002, patient_id PT-12345432, medications acetaminophen and ceritizine.", "quit"]
    )
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    run_session(process_fn=mock_engine)

    captured = capsys.readouterr()
    assert "Patient registered." in captured.out
