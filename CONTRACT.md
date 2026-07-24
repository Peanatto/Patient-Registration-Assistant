# CONTRACT.md

## Architecture Mapping

### Functionality 1 Mapping (Chatbot Support)
- `interface` responsibilities: collect user question, display conversational response
- `engine` responsibilities: interpret the "inquiry" intent, coordinate with storage to fetch current context, and use the LLM to generate an answer based on the data
- `storage` responsibilities: retrieve all active patient and appointment records to provide context to the engine

### Functionality 2 Mapping (Patient Registration)
- `interface` responsibilities: form submission with name/date of birth/patient ID number/medications, then show result message
- `engine` responsibilities: validate required fields + normalize values using local rules
- `storage` responsibilities: check for duplicate patient ID number and save the patient's information

### Functionality 3 Mapping (Patient Directory)
- `interface` responsibilities: capture user request to view all patients and display the formatted list
- `engine` responsibilities: route the list request to the storage layer and format the returned data
- `storage` responsibilities: retrieve all active patient records from the database

### Functionality 4 Mapping (Patient Removal)
- `interface` responsibilities: capture user request to delete a specific patient and display the outcome
- `engine` responsibilities: parse the target patient ID from the input and route the delete command
- `storage` responsibilities: find the corresponding row by patient ID and remove it from the database

### Functionality 5 Mapping (Appointment Booking)
- `interface` responsibilities: capture user request to book an appointment and display outcome
- `engine` responsibilities: extract patient_id, date, and time; validate completeness; coordinate with storage
- `storage` responsibilities: verify patient exists in "Patients" tab, append new row to "Appointments" tab

---

## Interface Contracts

### Functionality 1
**`interface -> engine`**
- Function(s): `process_request(user_input: str)` (handled via the "inquiry" intent)
- Input payload: `user_input`
- Return payload/status: `{"status": "success", "message": "Bob takes acetaminophen and his next appointment is 10-15-2026.", "data": None}`
- Failure statuses: `{"status": "error", "message": "API or Storage failure."}`

**`engine -> storage`**
- Function(s): `get_patients()` and `get_bookings()`
- Input payload: None
- Return payload/status: Lists containing dictionaries of current database records
- Failure statuses: `[]` (empty lists returned if database is empty)

### Functionality 2
**`interface -> engine`**
- Function(s): `parse_registration(raw_text: str)`
- Input payload: `raw_text`
- Return payload/status: `{"status": "success", "data": {"name": "...", "patient_id": "..."}}`
- Failure statuses: `{"status": "incomplete", "missing": ["patient_id"]}`

**`engine -> storage`**
- Function(s): `save_patient(patient_data: dict)`
- Input payload: `patient_data` dictionary containing name, dob, patient_id, medications
- Return payload/status: `"success"`
- Failure statuses: `"exists"` (duplicate ID), `"error"` (malformed data or API failure)

### Functionality 3
**`interface -> engine`**
- Function(s): `handle_list_request()`
- Input payload: None
- Return payload/status: `{"status": "success", "data": [{"name": "...", "patient_id": "..."}]}`
- Failure statuses: `{"status": "error", "message": "Failed to retrieve patients"}`

**`engine -> storage`**
- Function(s): `get_patients()`
- Input payload: None
- Return payload/status: `[{"name": "...", "patient_id": "...", "dob": "...", "medications": "..."}]`
- Failure statuses: `[]` (empty list returned on empty sheet or exception)

### Functionality 4
**`interface -> engine`**
- Function(s): `handle_delete_request(raw_text: str)`
- Input payload: `raw_text`
- Return payload/status: `{"status": "success", "message": "Patient deleted."}`
- Failure statuses: `{"status": "not_found", "message": "Patient ID not found."}`

**`engine -> storage`**
- Function(s): `delete_patient(patient_id: str)`
- Input payload: `patient_id`
- Return payload/status: `"success"`
- Failure statuses: `"not_found"` (ID missing from sheet), `"error"` (API failure)

### Functionality 5
**`interface -> engine`**
- Function(s): `process_request(user_input: str)` (handled via a new "book" intent)
- Input payload: `user_input`
- Return payload/status: `{"status": "success", "message": "Appointment booked successfully."}`
- Failure statuses: `{"status": "not_found", "message": "Patient not found."}, {"status": "incomplete", "missing": ["time"]}, {"status":        "conflict", "message": "That time slot is already booked..."}`

**`engine -> storage`**
- Function(s): `verify_patient(patient_id: str)`
- Input payload: `patient_id`
- Return payload/status: `True` or `False`

**`engine -> storage`**
- Function(s): `save_booking(patient_id: str, date: str, time: str)`
- Input payload: `patient_id`, `date`, `time`
- Return payload/status: `"success"`
- Failure statuses: `"conflict"` (time slot already exists in sheet), `"error"` (API failure)

### Functionality 6 Mapping (Appointment Directory)
- `interface` responsibilities: capture user requests to view appointments and display outcomes
- `engine` responsibilities: route list requests
- `storage` responsibilities: retrieve all appointment records

**`interface -> engine`**
- Function(s): `process_request(user_input: str)` (handled via new "list_bookings" intent)
- Return payload/status: `{"status": "success", "data": [...]}`

**`engine -> storage`**
- Function(s): `get_bookings()`
- Input payload: None
- Return payload/status: `[{"patient_id": "...", "date": "...", "time": "..."}]`
- Failure statuses: `[]` (empty list or error)

### Functionality 7 Mapping (Appointment Cancellation)
- `interface` responsibilities: capture user request to cancel an appointment and display the outcome
- `engine` responsibilities: extract patient_id, date, and time, validate completeness, and route the cancellation command
- `storage` responsibilities: find the specific appointment row matching all three criteria and remove it

**`interface -> engine`**
- Function(s): `process_request(user_input: str)` (handled via a new "cancel_booking" intent)
- Input payload: `user_input`
- Return payload/status: `{"status": "success", "message": "Appointment cancelled successfully."}`
- Failure statuses: `{"status": "not_found", "message": "Appointment not found."}, {"status": "incomplete", "missing": ["time"]}`

**`engine -> storage`**
- Function(s): `delete_booking(patient_id: str, date: str, time: str)`
- Input payload: `patient_id`, `date`, `time`
- Return payload/status: `"success"`
- Failure statuses: `"not_found"` (no exact match for all three parameters), `"error"` (API failure)