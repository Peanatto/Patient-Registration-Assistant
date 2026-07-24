# Patient Management System

This application provides a comprehensive system for managing patient records, offering features such as chatbot support for patient information, patient registration, a directory of registered patients, and the ability to remove patient records.

## Setup

To set up the project, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <project_directory>
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **One-time Configuration:**
    *   **Google Sheets API Credentials:** This project uses `gspread` for interacting with Google Sheets. You will need to set up Google Cloud Platform credentials for a service account, enable the Google Sheets API, and share your target Google Sheet with the service account's email address. Place your service account JSON key file in a secure location and ensure your application can access it.
    *   **Google Generative AI API Key:** For chatbot functionality, set up your Google Generative AI API key. This key should be set as an environment variable (e.g., `GOOGLE_API_KEY`).

## How to Run

To start the application, execute the main script:

```bash
python main.py
```

To run tests, use `pytest`:

```bash
pytest
```

## Usage Examples

Here are a few examples demonstrating the core functionalities of the Patient Management System:

### 1. Chatbot Support

**Input:**
```
What medications does Alice Chen require?
```

**Expected Output:**
```
Alice Chen takes acetaminophen.
```

### 2. Patient Registration

**Example 1: Successful Registration**

**Input:**
```
Register patient: Alice Chen, 05-05-2002, PT-12345432, acetaminophen
```

**Expected Output:**
```
Submission result: success
```

**Example 2: Incomplete Registration (missing date of birth)**

**Input:**
```
Register patient: Bob Smith, PT-54321098, ibuprofen
```

**Expected Output:**
```
Submission result: incomplete, missing: ['date_of_birth']
```

### 3. Patient Directory

**Input:**
```
List all patients
```

**Expected Output:**
```
- Name: Alice Chen, ID: PT-12345432, DOB: 05-05-2002, Medications: acetaminophen
- Name: Bob Smith, ID: PT-54321098, DOB: 10-10-1990, Medications: ibuprofen
```

### 4. Patient Removal

**Input:**
```
Delete patient PT-12345432
```

**Expected Output:**
```
Confirmation: Patient deleted.
```

## Project Structure

The project follows a standard layout:

```
./
├── src/
│   ├── main.py
│   └── ... (other source files)
├── tests/
│   ├── test_functionality.py
│   └── ... (other test files)
├── requirements.txt
├── FUNCTIONALITY.md
├── CONTRACT.md
└── README.md
```
