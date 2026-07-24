# FUNCTIONALITY.md

## Functionality 1: Chatbot Support
- **Input:** Open-ended user question (e.g., "What medications does [patient] require?")
- **Output:** Natural-language response provided to user
- **Success:** Answer relevant to user prompt is returned
- **Failure/Edge Cases:** 
    - Unknown question -> return fallback response such as "Not enough information to provide a solid answer."
    - Empty input -> return prompt to user to enter question

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