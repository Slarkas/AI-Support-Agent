# AI Support Agent

A Python-based support ticket analyzer powered by a locally hosted Large Language Model (LLM). The application classifies support requests, assigns priority levels, generates summaries, and recommends actions. It also stores analyzed tickets in a local SQLite database.

If LLM analysis fails or returns an invalid response, the application can fall back to a rule-based analyzer.

This project demonstrates local AI integration, structured response validation, error handling, database persistence, and automated testing.

## Features

- **LLM-powered analysis** — analyzes support tickets using a local model through LM Studio.
- **Ticket classification** — categorizes requests as `technical_issue`, `billing`, `order_status`, or `general`.
- **Priority assignment** — assigns `high`, `medium`, or `low` priority.
- **Automatic summaries** — generates concise summaries of support requests.
- **Recommended actions** — suggests an appropriate next step for each ticket.
- **Response validation** — validates the returned JSON structure and checks required fields, categories, and priorities.
- **Rule-based fallback** — attempts to analyze tickets using predefined rules if LLM analysis fails.
- **SQLite storage** — saves analyzed tickets locally and supports retrieving and listing stored tickets.
- **Automated tests** — covers ticket analysis, response validation, error handling, and database operations.

## Technology Stack

- Python 3.10+
- LM Studio
- A compatible locally hosted chat model
- SQLite
- Python standard library, including `urllib`, `json`, `sqlite3`, and `unittest`
- Git and GitHub

The application code uses Python's standard library and does not require external Python packages.

## Requirements

Before running the application, install:

1. Python 3.10 or newer.
2. [LM Studio](https://lmstudio.ai/).
3. A compatible chat model downloaded and loaded in LM Studio.

The application communicates with LM Studio through its OpenAI-compatible Chat Completions API.

See the [LM Studio API documentation](https://lmstudio.ai/docs/developer/openai-compat).

## Installation

### 1. Clone the repository

```powershell
git clone https://github.com/Slarkas/AI-Support-Agent.git
cd AI-Support-Agent
```

### 2. Create a virtual environment

```powershell
py -3.10 -m venv .venv
```

If the Python launcher is unavailable, use:

```powershell
python -m venv .venv
```

### 3. Activate the virtual environment

In Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell prevents activation, run Python directly from the virtual environment:

```powershell
.\.venv\Scripts\python.exe main.py
```

## LM Studio Configuration

### 1. Load a model

Open LM Studio and load a compatible chat model.

### 2. Start the local server

Open the Developer tab in LM Studio and start the local server.

This project is configured to use:

```text
http://localhost:1235/v1
```

The Chat Completions endpoint is:

```text
http://localhost:1235/v1/chat/completions
```

LM Studio commonly uses port `1234` by default, but this project uses port `1235`. If your server uses another port, update the relevant API URL in `config.py`.

### 3. Configure the model

The model identifier is configured in `config.py`. Set it to the model identifier expected by your LM Studio server.

All LLM requests are sent to the local server. The application does not require a paid cloud AI API subscription.

## Usage

Make sure the model is loaded and the LM Studio server is running.

Start the application:

```powershell
python main.py
```

Enter a support ticket when prompted.

Example input:

```text
Our website is down and customers cannot log in.
```

The application displays the analysis method, category, priority, summary, and recommended action.

Example output:

```text
Analysis method:    LLM
Category:           technical_issue
Priority:            high
Summary:             Website is down and customers cannot log in
Recommended Action: Investigate the server and restore login functionality immediately
```

The exact response depends on the selected model.

Type `quit` or `exit` to stop the application.

If LLM analysis fails, the application attempts to use its rule-based fallback. Empty input is rejected by the command-line interface.

## Ticket Storage

Analyzed tickets are stored in a local SQLite database named `tickets.db`.

The storage module, `ticket_store.py`, handles database operations, including initializing the database and saving, retrieving, listing, and deleting tickets.

The database is created or initialized by the application's storage logic as needed. Keep `tickets.db` if you want to preserve your existing ticket history.

## Running Tests

Run the project's test suite with:

```powershell
python -m pytest test_agent.py test_ticket_store.py test_integration_real.py -v
```

The tests cover:

- Rule-based ticket classification and priority assignment.
- Required response fields and response validation.
- LLM response handling, invalid output, and API errors.
- Ticket database operations.
- Integration with a real, temporary SQLite database.

The integration test uses a temporary database so it can verify database behavior without intentionally modifying the application's existing ticket history.

## Project Structure

```text
AI-Support-Agent/
├── .gitignore
├── README.md
├── config.py
├── llm_client.py
├── main.py
├── ticket_store.py
├── test_agent.py
├── test_ticket_store.py
└── test_integration_real.py
```

| File | Responsibility |
|---|---|
| `main.py` | Command-line interface, ticket analysis flow, and fallback handling |
| `config.py` | API configuration, model settings, and response validation |
| `llm_client.py` | Communication with LM Studio and LLM response processing |
| `ticket_store.py` | SQLite database operations for support tickets |
| `test_agent.py` | Tests for ticket analysis and LLM response handling |
| `test_ticket_store.py` | Tests for ticket storage operations |
| `test_integration_real.py` | Integration tests using a real temporary SQLite database |
| `.gitignore` | Excludes local and generated files from Git |
| `README.md` | Project documentation and setup instructions |

## Current Limitations

- This is a development and portfolio project, not a production-ready support platform.
- Analysis quality depends on the selected model and its ability to follow the requested output format.
- Rule-based fallback relies on predefined keywords and rules and is less flexible than LLM analysis.
- The local LM Studio server and a compatible model must be available for AI-powered analysis.
- The application uses a command-line interface and does not currently provide a web interface.
- SQLite provides local ticket persistence, but the project does not include a multi-user support dashboard or external help-desk integrations.

## Purpose

This project explores integrating a locally hosted LLM into a Python application while maintaining structured outputs, validating model responses, handling failures, storing ticket data, and testing application behavior.

**Author:** [Slarkas](https://github.com/Slarkas)