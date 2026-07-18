# CONTRACT.md

## Architecture Mapping

### Functionality 1 Mapping
- `interface` responsibilities: collect user question, display response (answer or fallback)
- `engine` responsibilities: interpret question and produce response
- `storage` responsibilities: None, basic chatbot support does not require

### Functionality 2 Mapping
- `interface` responsibilities: form submission with name/date of birth/patient ID number/medications, then show result message
- `engine` responsibilities: validate required fields + normalize values using local rules
- `storage` responsibilities: check for duplicate patient ID number and save the patient's information

---

## Interface Contracts

### Functionality 1
**`interface -> engine`**
- Function(s): get_response(user_query: str)
- Input payload: user_query
- Return payload/status: {"status": "success", "data": {"answer": "Bob takes acetaminophen and cetirizine."}}
- Failure statuses: {"status": "not_found", "message": "This patient is not in our system."}

### Functionality 2
**`interface -> engine`**
- Function(s): parse_registration(raw_text: str)
- Input payload: raw_text
- Return payload/status: {"status": "success", "data": {"name": "...", "patient_id": "..."}}
- Failure statuses: {"status": "incomplete", "missing": ["patient_id"]}

**`engine -> storage`**
- Function(s): save_patient(patient_data: patient_record)
- Input payload: patient_data
- Return payload/status: {"status": "success", "patient_id": "member_123"}
- Failure statuses: {"status": "exists", "message": "duplicate patient ID number"}