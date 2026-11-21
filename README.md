# 🎙️ Gnani Voice Field Register

### A Voice-Based Digital Field Registration System for ASHA Workers

**Team Name:** Cookies  
**Project:** Voice Field Register  
**Repository:** [Gnani Voice Field Register](https://github.com/manyagowdajune2006-png/Gnani-Voice-Field-Register)

---

## 📌 1. About the Project

Gnani Voice Field Register is a voice-based digital platform designed to make field data collection easier for ASHA (Accredited Social Health Activist) workers.

ASHA workers regularly visit households to collect important health-related information. Recording this information manually can take time and create difficulties during field visits.

Our solution provides a voice-assisted system that allows workers to interact with the application using their voice instead of depending entirely on manual data entry.

The application supports English and Hindi conversations and helps collect and organize household visit information digitally.

## 🎯 2. Problem Statement

Traditional field registration methods often involve:

- Manual recording of household information.
- Time-consuming data entry.
- Difficulty maintaining organized records.
- Challenges when workers need to enter information while conducting field visits.
- Dependence on typing and written documentation.

These challenges can make field data collection less convenient and efficient.

## 💡 3. Our Solution

We developed a voice-assisted field registration platform that allows ASHA workers to communicate with the system through spoken responses.

The application asks questions, receives voice input, processes the conversation, and collects the required visit details.

It provides a simple interface with login, registration, language selection, voice interaction, and visit information management.

## ✨ 4. Key Features

### 🎤 Voice-Based Interaction
- Allows workers to interact through voice.
- Uses speech recognition to process spoken responses.
- Provides spoken responses through text-to-speech.

### 🌐 Multiple Language Support
- Supports English and Hindi.
- Allows workers to select their preferred language.

### 👩‍⚕️ ASHA Worker Registration and Login
- Provides individual worker registration.
- Supports secure password storage.
- New registrations remain pending until administrator approval.
- Only approved workers can log in.

### 📝 Digital Visit Registration
Collects important household visit details, including:
- Visit date
- Village name
- Household ID
- Person's name
- Age
- Main health concern
- Additional notes

### 📂 Visit Records
- Stores collected visit information digitally.
- Uses an SQLite database for data storage.

### 🎨 Simple User Interface
- Clean teal-and-white design.
- Easy-to-understand dashboard.
- Designed to make voice interaction straightforward.

## 🔄 5. How the System Works

1. **Worker Registration:** An ASHA worker creates an account.
2. **Administrator Approval:** The new account is approved before login.
3. **Worker Login:** The approved worker logs into the application.
4. **Language Selection:** The worker selects English or Hindi.
5. **Voice Interaction:** The system asks questions and receives spoken answers.
6. **Speech Processing:** The speech recognition service converts spoken input into text.
7. **Data Collection:** The application processes the answers and organizes visit details.
8. **Voice Response:** The system responds using text-to-speech.
9. **Record Storage:** Visit information is stored digitally.

## 🏗️ 6. System Architecture

The project follows a frontend-backend architecture.

```text
       ASHA WORKER
            |
            v
     FRONTEND (HTML, CSS, JS)
            |
            v
       FASTAPI BACKEND
            |
      +-----+------+
      |            |
      v            v
 SPEECH SERVICES  AUTHENTICATION
      |            |
      v            v
  SPEECH TO TEXT  WORKER ACCOUNTS
      |
      v
 CONVERSATION PROCESSING
      |
      v
 TEXT TO SPEECH
      |
      v
 SQLITE DATABASE
      |
      v
   VISIT RECORDS
```

### Main Components

| Component | Responsibility |
|---|---|
| Frontend | User interface and voice interaction |
| FastAPI | Backend application and API handling |
| Speech-to-Text | Converts spoken input into text |
| Dialogue Processing | Manages the question-and-answer flow |
| Text-to-Speech | Converts system responses into speech |
| Authentication | Manages worker registration and login |
| SQLite | Stores worker and visit information |

## 🛠️ 7. Technology Stack

| Technology | Usage |
|---|---|
| HTML | Frontend structure |
| CSS | User interface design |
| JavaScript | Frontend interaction |
| Python | Backend development |
| FastAPI | Backend framework |
| SQLite | Database |
| Vachana AI APIs | Speech recognition and speech generation |
| WebSocket | Real-time voice communication |
| Git & GitHub | Version control and collaboration |

## 📁 8. Project Structure

```text
Gnani-Voice-Field-Register/
│
├── backend/
│   ├── main.py
│   ├── auth.py
│   ├── dialogue.py
│   ├── gnani_adapter.py
│   ├── llm.py
│   ├── approve_worker.py
│   └── create_worker.py
│
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── app.js
│
├── data/
│   └── visits.db
│
├── .gitignore
└── README.md
```

*Note: The `data/` directory and database are created or maintained locally and are not included in the public repository.*

## ⚙️ 9. Installation and Setup

Follow these steps to run the project locally.

### Prerequisites

- Python installed
- Git installed
- Visual Studio Code (recommended)
- Valid Vachana AI API credentials

### Step 1: Clone the Repository

```bash
git clone https://github.com/manyagowdajune2006-png/Gnani-Voice-Field-Register.git
```

### Step 2: Open the Project Folder

```bash
cd Gnani-Voice-Field-Register
```

### Step 3: Create a Virtual Environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

### Step 4: Install Dependencies

If the project contains a `requirements.txt` file, run:

```bash
pip install -r requirements.txt
```

### Step 5: Configure Environment Variables

Create a `.env` file in the project root and configure the required values:

```env
GNANI_API_KEY=your_api_key
DATABASE_PATH=./data/visits.db
```

Replace the API key placeholder with your own valid credentials. Never upload your API key or `.env` file to GitHub.

### Step 6: Start the Backend

```bash
uvicorn backend.main:app --reload
```

### Step 7: Open the Application

Open the local application URL:

```text
http://127.0.0.1:8000
```

*Make sure the required Python dependencies and environment variables are configured before starting the application.*

## 🔐 10. Security and Data Handling

- Passwords are stored as password hashes rather than plain text.
- New worker accounts require approval before login.
- Local database files are excluded from Git tracking.
- API credentials are maintained through environment variables.
- Access to the voice session requires an authenticated worker.

## 🚀 11. Future Enhancements

The project can be extended with:

- Offline voice interaction for areas with limited internet connectivity.
- Regional language support.
- Administrator dashboard for managing worker accounts.
- Advanced reporting and analytics.
- Synchronization of records across multiple devices.
- Improved field data visualization.

## 🌍 12. Expected Impact

Gnani Voice Field Register aims to:

- Reduce dependence on manual data entry.
- Make field registration easier through voice interaction.
- Support Hindi and English communication.
- Improve the organization of household visit information.
- Provide a simple digital tool for ASHA workers.

## 👥 13. Team

**Team Name:** Cookies

**Project:** Gnani Voice Field Register

---

### Building a simpler, voice-enabled way to collect field information.

**Thank you for exploring our project!**
