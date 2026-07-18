# FUNCTIONALITY.md

## Functionality 1: Chatbot Support
- Input: Open-ended user question (e.g. "What medications does [patient] require?")
- Output: Natural-language response provided to user
- Success: Answer relevant to user prompt is returned
- Failure/Edge Cases: 
    - Unknown question -> return fallback response such as "Not enough information to provide a solid answer."
    - Empty input -> return prompt to user to enter question

## Functionality 2: Patient Registration
- Input: Open-ended text or form submission with fields (e.g. name, date of birth, patient ID number, medications)
- Output: Submission result message (`success`, `exists`, or `incomplete`)
- Success: All required fields are filled and data is successfully saved to database
- Failure/Edge Cases:
    - Missing required field(s) -> return missing field list along with `incomplete` 
    - Duplicate patient ID number -> return `exists`
    - Invalid formats -> return validation error