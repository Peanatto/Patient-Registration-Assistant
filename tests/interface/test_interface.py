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
import unittest.mock
import runpy


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


# ---------------------------------------------------------------------------
# Test 6: format_response — error status returns message
# ---------------------------------------------------------------------------
def test_format_error_returns_error_message():
    result = {"status": "error", "message": "An unexpected error occurred.", "data": None}
    output = format_response(result)
    assert "An unexpected error occurred." in output


# ---------------------------------------------------------------------------
# Test 7: run_session — process_fn is None, uses default process_request
# ---------------------------------------------------------------------------
def test_run_session_with_none_process_fn_uses_default_process_request(monkeypatch, capsys):
    def mock_default_process_request(user_input):
        return {"status": "success", "message": "Default engine processed: " + user_input, "data": None}

    monkeypatch.setattr("src.interface.cli.process_request", mock_default_process_request)

    # Simulate: one message, then quit.
    inputs = iter(["Hello", "quit"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    run_session()

    captured = capsys.readouterr()
    assert "Default engine processed: Hello" in captured.out


# ---------------------------------------------------------------------------
# Test 8: run_session — empty input (blank line or whitespace) continues
# ---------------------------------------------------------------------------
def test_run_session_continues_on_empty_input(monkeypatch, capsys):
    mock_engine = unittest.mock.MagicMock(return_value={"status": "success", "message": "Processed.", "data": None})

    # Simulate: empty input, then whitespace-only input, then valid input, then quit.
    inputs = iter(["", "   ", "Hello", "quit"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    run_session(process_fn=mock_engine)

    captured = capsys.readouterr()
    # Ensure process_fn was called only for "Hello", not for "" or "   "
    mock_engine.assert_called_once_with("Hello")
    assert "Processed." in captured.out
    assert "Goodbye!" in captured.out


# ---------------------------------------------------------------------------
# Test 9: run_session — EOFError on input exits cleanly
# ---------------------------------------------------------------------------
def test_run_session_exits_on_eof_error(monkeypatch, capsys):
    # Simulate an EOFError when input() is called
    def mock_input_raises_eof_error(_):
        raise EOFError

    monkeypatch.setattr("builtins.input", mock_input_raises_eof_error)

    # We also need to mock process_request, as run_session will try to call it
    # before the EOFError, if the input is not 'quit' or 'exit'.
    # In this specific test, input() raises EOFError on the first call,
    # so process_request is not actually called, but it's good practice to mock it.
    def mock_process_request(_):
        return {"status": "error", "message": "Should not be called", "data": None}

    monkeypatch.setattr("src.interface.cli.process_request", mock_process_request)

    run_session()

    captured = capsys.readouterr()
    assert "Goodbye!" in captured.out


# ---------------------------------------------------------------------------
# Test 11: __main__ block — executes run_session when run as script
# ---------------------------------------------------------------------------
def test_cli_main_block_executes_run_session(monkeypatch, capsys):
    # 1. Feed 'quit' into input() so run_session terminates immediately
    # instead of waiting forever for human typing in the terminal.
    monkeypatch.setattr("builtins.input", lambda _: "quit")

    # 2. Execute the module with __name__ set to "__main__"
    runpy.run_module("src.interface.cli", run_name="__main__")

    # 3. Verify run_session actually ran by checking stdout for the exit message
    captured = capsys.readouterr()
    assert "Goodbye!" in captured.out