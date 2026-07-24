# CONTRACT.md

## Architecture Mapping

### Functionality 1 Mapping (Chatbot Support)
- `interface` responsibilities: collect user question, display response (answer or fallback)
- `engine` responsibilities: interpret question and produce response
- `storage` responsibilities: None, basic chatbot support does not require

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
- Function(s): `get_response(user_query: str)`
- Input payload: `user_query`
- Return payload/status: `{"status": "success", "data": {"answer": "Bob takes acetaminophen and cetirizine."}}`
- Failure statuses: `{"status": "not_found", "message": "This patient is not in our system."}`

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
- Failure statuses: `{"status": "not_found", "message": "Patient not found."}, {"status": "incomplete", "missing": ["time"]}`

**`engine -> storage`**
- Function(s): `verify_patient(patient_id: str)`
- Input payload: `patient_id`
- Return payload/status: `True` or `False`

**`engine -> storage`**
- Function(s): `save_booking(patient_id: str, date: str, time: str)`
- Input payload: `patient_id`, `date`, `time`
- Return payload/status: `"success"`
- Failure statuses: `"error"` (API failure)