# Patient Registration Assistant

The Patient Registration Assistant is an AI-powered application designed to streamline patient management within a healthcare setting. It provides a conversational interface for various tasks, including patient registration, inquiry about patient records and schedules, appointment booking, and managing both patient and appointment directories. The system leverages an underlying database to store and retrieve patient and appointment information, ensuring efficient and accurate data handling.

## Setup

To set up the Patient Registration Assistant, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-repo/patient-registration-assistant.git
    cd patient-registration-assistant
    ```

2.  **Install dependencies:**
    The project relies on the following Python packages:
    -   `pytest`
    -   `gspread`
    -   `google-auth`
    -   `google-genai`
    -   `pytest-cov`

    You can install them using pip:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure API Key:**
    Create a file named `.env` in the root directory of the project. Add your Google Gemini API key to this file in the following format:
    ```
    GEMINI_API_KEY=your_api_key_here
    ```
    Replace `your_api_key_here` with your actual API key.

## How to Run

To start the Patient Registration Assistant, execute the following command from the project root directory:

```bash
python -m src.interface.cli
```

## Usage Examples

Here are a few examples demonstrating the core functionalities of the Patient Registration Assistant:

### 1. Patient Registration

**Input:**
```
Register a patient named John Doe, born 1990-01-01, patient ID PT-12345678, takes Aspirin.
```

**Expected Output:**
```
Assistant: Patient registered successfully.
```

### 2. Listing Registered Patients

**Input:**
```
Register Jane Smith, born 1985-05-05, patient ID PT-87654321, takes Insulin.
List all patients.
```

**Expected Output:**
```
Assistant: Patient registered successfully.

Assistant: 2 patient record(s) found.
  - John Doe (ID: PT-12345678)
  - Jane Smith (ID: PT-87654321)
```

### 3. Patient Inquiry (Chatbot Support)

**Input:**
```
What medications does PT-12345678 take?
```

**Expected Output:**
```
Assistant: John Doe takes Aspirin.
```

### 4. Appointment Booking

**Input:**
```
Book PT-12345678 for an appointment on 2024-12-25 at 10:00 AM.
```

**Expected Output:**
```
Assistant: Appointment booked successfully.
```

## Project Structure

The project follows a modular structure to ensure separation of concerns and maintainability:

```
.
├── .env                  # Environment variables (e.g., API keys)
├── FUNCTIONALITY.md      # Detailed description of system functionalities
├── CONTRACT.md           # API contracts and architecture mapping
├── README.md             # Project overview and instructions
├── requirements.txt      # Python dependencies
├── src/
│   ├── interface/        # User-facing components (e.g., cli.py)
│   │   └── cli.py        # Command-line interface for the assistant
│   ├── engine/           # Business logic and AI integration
│   │   └── engine.py     # Core processing and request handling
│   └── storage/          # Data persistence layer (e.g., Google Sheets integration)
│       └── storage.py    # Handles data storage and retrieval
└── tests/
    ├── interface/             
    ├── engine/      
    └── storage/
        └── conftest.py
```

## Demo Video

<video src="./assets/CS180_demo.mp4" width="100%" controls>
  Your browser does not support the video tag.
</video>

Note: the cancellation error is due to an exact time mismatch. The sheet had 04:00 PM, and I gave 4:00 PM. After changing to match, it worked.