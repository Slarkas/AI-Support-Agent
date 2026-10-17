# AI Support Agent

A Python-based support ticket analyzer powered by a locally hosted Large Language Model (LLM). It classifies support requests, assigns priority levels, generates summaries, and recommends actions. If LLM analysis fails, the application falls back to a rule-based analyzer.

The project demonstrates local AI integration, structured output validation, error handling, and automated testing.

## Features

- **LLM-powered analysis** — analyzes support tickets using a local model through LM Studio.
- **Ticket classification** — categorizes requests as `technical_issue`, `billing`, `order_status`, or `general`.
- **Priority detection** — assigns `high`, `medium`, or `low` priority.
- **Automatic summaries** — generates concise summaries of support requests.
- **Recommended actions** — suggests an appropriate next step for each ticket.
- **Structured JSON output** — uses a JSON schema to constrain the model's response.
- **Response validation** — checks required fields and validates category and priority values.
- **Rule-based fallback** — continues processing tickets if the LLM request fails or returns invalid output.
- **Unit tests** — tests classification logic, response validation, and API error handling.

## Technology Stack

- Python 3.10+
- LM Studio
- A compatible locally hosted chat model
- Python standard library (`urllib`, `json`, `unittest`, and others)
- Git and GitHub

No external Python packages are required by the current implementation.

## Requirements

Before running the application, install:

1. Python 3.10 or newer.
2. [LM Studio](https://lmstudio.ai/).
3. A compatible chat model downloaded and loaded in LM Studio.

The application communicates with LM Studio through its OpenAI-compatible Chat Completions endpoint. See the [LM Studio API documentation](https://lmstudio.ai/docs/developer/openai-compat).

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

If PowerShell prevents activation, you can run Python directly from the virtual environment without changing the execution policy:

```powershell
.\.venv\Scripts\python.exe main.py
```

## LM Studio Configuration

### 1. Load a model

Open LM Studio and load a compatible chat model.

### 2. Start the local server

Open the Developer tab in LM Studio and start the local server.

This project currently expects the server to be available at:

```text
http://localhost:1235/v1
```

The Chat Completions endpoint is:

```text
http://localhost:1235/v1/chat/completions
```

LM Studio commonly uses port `1234` by default, but this project is configured for port `1235`. If your server uses a different port, update `API_BASE_URL` in `config.py`.

### 3. Configure the model

The model identifier is configured through `MODEL_ID` in `config.py`. Set it to the model identifier expected by your LM Studio server.

The application sends requests to the local server and does not require a paid cloud AI API.

## Usage

Make sure the model is loaded and the LM Studio server is running.

Start the application:

```powershell
python main.py
```

Enter a support ticket when prompted. For example:

```text
Our website is down and customers cannot log in.
```

The application displays the analysis method, category, priority, summary, and recommended action.

Example output:

```text
Analysis method:    LLM
Category:           technical_issue
Priority:           high
Summary:            Website is down and users cannot log in
Recommended Action: Investigate server status and restore login functionality immediately
```

The exact response depends on the model.

Type `quit` or `exit` to stop the application.

If LLM analysis fails, the application reports the error and attempts rule-based analysis instead. Empty input is rejected by the command-line interface.

## Running Tests

Run the unit tests with:

```powershell
python -m unittest -v test_agent
```

The tests cover rule-based ticket classification, priority assignment, required output fields, LLM response handling, invalid responses, and API errors.

## Project Structure

```text
AI-Support-Agent/
├── .gitignore
├── README.md
├── config.py
├── main.py
└── test_agent.py
```

| File | Responsibility |
|---|---|
| `main.py` | Ticket analysis, LLM requests, response parsing, fallback logic, and command-line interface |
| `config.py` | API URL, model ID, request timeout, headers, and response validation |
| `test_agent.py` | Unit tests for the analyzer and LLM integration |
| `.gitignore` | Excludes local and generated files from Git |
| `README.md` | Project documentation and setup instructions |

## Current Limitations

- The application is a development and portfolio project, not a production-ready support platform.
- Analysis quality depends on the selected model and its ability to follow the requested output schema.
- Rule-based fallback uses predefined keywords and rules, so it is less flexible than LLM analysis.
- The local LM Studio server and compatible model must be available for AI-powered analysis.
- The application currently uses a command-line interface and does not include a web interface, ticket database, or integrations with external support platforms.

## Purpose

This project explores how to integrate a locally hosted LLM into a Python application while maintaining structured outputs, validating model responses, handling failures, and testing application behavior.

**Author:** [Slarkas](https://github.com/Slarkas)