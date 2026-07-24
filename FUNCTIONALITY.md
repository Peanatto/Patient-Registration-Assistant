# FUNCTIONALITY.md

## Functionality 1: Chatbot Support
- **Input:** Open-ended user question about clinical records or schedules (e.g., "What medications does PT-12345678 take?" or "When is their next appointment?")
- **Output:** Natural-language, conversational response provided to the user
- **Success:** The system successfully retrieves both the patient and appointment databases, uses them as context, and returns an accurate answer based strictly on the stored data.
- **Failure/Edge Cases:** 
    - Unknown question / Data not found -> The LLM informs the user that the requested information is not in the provided database.
    - Empty input -> System ignores and prompts the user to enter a question.

## Functionality 2: Patient Registration
- **Input:** Open-ended text or form submission with fields (name, date of birth, patient ID, medications)
- **Output:** Submission result message (`success`, `exists`, or `incomplete`)
- **Success:** All required fields are filled and data is successfully saved to the database
- **Failure/Edge Cases:**
    - Missing required field(s) -> return missing field list along with `incomplete` status
    - Duplicate patient ID -> return `exists` status and abort save
    - Invalid formats -> return validation error and prompt for correction

## Functionality 3: Patient Directory
- **Input:** Open-ended user command (e.g., "List all patients", "Show registered members")
- **Output:** Formatted text display of all current patients in the system
- **Success:** System retrieves and displays a readable list of patient records
- **Failure/Edge Cases:**
    - Database is empty -> return "No patients currently registered in the system."
    - API/Connection error -> return safe fallback indicating retrieval failure

## Functionality 4: Patient Removal
- **Input:** Command identifying a specific patient to remove (e.g., "Delete patient PT-12345432")
- **Output:** Confirmation message of deletion
- **Success:** Target patient is located by their unique ID and permanently removed from the system
- **Failure/Edge Cases:**
    - Patient ID does not exist -> return "Patient ID not found in the database."
    - Input lacks specific ID -> prompt the user to provide the exact patient ID to prevent accidental deletions

## Functionality 5: Appointment Booking
- **Input:** User command containing a patient ID, a date, and a time (e.g., "Book PT-12345678 for 10-15-2026 at 2:00 PM")
- **Output:** Confirmation message of the booked appointment
- **Success:** The system verifies the patient ID exists, then saves the booking details to the Appointments tab
- **Failure/Edge Cases:**
    - Patient ID does not exist -> return "Patient not found. Please register the patient first."
    - Missing date or time -> return validation error and prompt for missing information
    - Time Slot Taken -> return `conflict` status and prompt the user to choose another time (prevents double-booking)

## Functionality 6: Appointment Directory
- **Input:** Open-ended user command to list bookings (e.g., "Show all appointments")
- **Output:** Formatted display of all appointments
- **Success:** System retrieves a readable list of appointments
- **Failure/Edge Cases:**
    - Database empty/API error -> return fallback indicating retrieval failure

## Functionality 7: Appointment Cancellation
- **Input:** Command identifying a specific appointment to cancel (e.g., "Cancel the appointment for PT-12345 on 10-15-2026 at 2:00 PM")
- **Output:** Confirmation message of cancellation
- **Success:** System successfully locates and removes the target appointment row from the database
- **Failure/Edge Cases:**
    - Appointment not found -> return "Appointment not found for that patient at that specific date and time."
    - Missing required fields -> return missing field list (e.g., date or time) along with `incomplete` status