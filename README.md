# AgentOS — Web Search Chat Agent

An AI-powered conversational agent built with **FastAPI, Groq, and Tavily**. It answers user questions, searches the web when current information is needed, and remembers previous conversations using persistent database storage.

**Repository:** https://github.com/Kundank8789/agentos-web-search-chat

## Overview

This project extends AgentOS with a focused chat agent that can:

- Understand and respond to natural-language questions.
- Search the web using Tavily when up-to-date information is required.
- Generate responses using Groq-hosted LLMs.
- Maintain conversation context across multiple messages.
- Persist conversations and messages in a database.
- Return web sources alongside answers.
- Authenticate users using the existing AgentOS authentication system.

The agent uses one external tool: **Tavily Web Search**. Conversation history is handled internally through database persistence.

## Key Features

### 1. AI-powered conversations
Uses the Groq API with an OpenAI-compatible client to generate conversational responses.

### 2. Web search
Integrates Tavily to retrieve relevant web results, including titles, URLs, snippets, and relevance scores.

### 3. Persistent conversation memory
Stores user messages and assistant responses so the agent can use previous conversation context.

### 4. Conversation management
Supports creating conversations, listing a user's conversations, and retrieving message history.

### 5. Authenticated API
Uses the existing AgentOS authentication and user authorization flow.

### 6. Source-aware responses
Search results are passed to the LLM so it can provide answers supported by retrieved web sources.

## Architecture

```text
User
 |
 v
FastAPI Chat API
 |
 v
Authentication & Authorization
 |
 v
Chat Service
 |
 +------> Conversation History (Database)
 |
 v
Chat Agent Runtime
 |
 v
Groq LLM
 |
 +------> Tavily Web Search (when needed)
 |
 v
Final Answer + Sources
 |
 v
Save Assistant Response
 |
 v
Return Response to User
```

## Tech Stack

| Component | Technology |
|---|---|
| Backend | Python |
| API Framework | FastAPI |
| LLM Provider | Groq |
| Web Search | Tavily |
| LLM Client | OpenAI-compatible Python client |
| Database | SQLAlchemy async database |
| Migrations | Alembic |
| Cache / Supporting Service | Redis |
| Authentication | Existing AgentOS authentication |

## Project Structure

```text
agentos/
├── apps/
│   └── api/
│       ├── app/
│       │   ├── agent/
│       │   │   └── chat_runtime.py
│       │   ├── api/
│       │   │   └── chat.py
│       │   ├── models/
│       │   │   ├── conversation.py
│       │   │   └── chat_message.py
│       │   ├── schemas/
│       │   │   └── chat.py
│       │   ├── services/
│       │   │   └── chat.py
│       │   ├── tools/
│       │   │   └── web_search.py
│       │   ├── config.py
│       │   └── main.py
│       ├── alembic/
│       └── requirements.txt
├── design.md
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.11+
- Redis
- A supported database configured for the existing AgentOS backend
- Groq API key
- Tavily API key

### 1. Clone the repository

```powershell
git clone https://github.com/Kundank8789/agentos-web-search-chat.git
cd agentos-web-search-chat
```

### 2. Create and activate the virtual environment

```powershell
cd apps/api
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure environment variables

Create the environment file in the location expected by the backend configuration.

Configure your Groq and Tavily credentials, database connection, Redis connection, and existing AgentOS authentication settings.

Example values:

```env
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
REDIS_URL=redis://localhost:6379/0
```

Add the database and authentication variables required by your existing AgentOS configuration.

**Important:** Never commit API keys, passwords, JWT secrets, or `.env` files.

### 5. Start Redis

Make sure Redis is running before starting the backend.

Verify the connection:

```powershell
Test-NetConnection localhost -Port 6379
```

If Redis is installed in WSL, start it from Ubuntu:

```bash
sudo service redis-server start
redis-cli ping
```

Expected response:

```text
PONG
```

### 6. Run database migrations

From the API directory, run:

```powershell
alembic upgrade head
```

### 7. Start the backend

```powershell
python -m uvicorn app.main:app --reload
```

Backend URL:

```text
http://127.0.0.1:8000
```

Interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

## API Endpoints

The chat API uses the existing AgentOS authentication flow.

| Method | Endpoint | Description |
|---|---|---|
| POST | `/chat/message` | Send a message and receive an AI response |
| GET | `/chat/conversations` | List the authenticated user's conversations |
| GET | `/chat/conversations/{conversation_id}/messages` | Retrieve conversation messages |

### Example request

`POST /chat/message`

```json
{
  "message": "What are the latest developments in AI agents?"
}
```

A follow-up request can include the existing conversation ID:

```json
{
  "message": "Summarize the first result.",
  "conversation_id": "YOUR_CONVERSATION_ID"
}
```

Requests must include valid authentication according to the existing AgentOS API.

The response includes the assistant's answer, conversation information, and available web sources.

## Conversation Memory

Conversation messages are persisted in the database.

This allows the agent to:

1. Retrieve previous messages from a conversation.
2. Use recent conversation history when generating a response.
3. Remember what the user asked earlier.
4. Associate messages with their conversation and authenticated user.

For example:

**User:** What are the latest developments in AI agents in 2026?

**User:** What topic did I ask about in my first message?

**Agent:** You asked about the latest developments in AI agents in 2026.

## Testing

Run the backend test suite from the API directory:

```powershell
python -m pytest -q
```

The existing backend test suite passed **22 tests** during development.

## Design Documentation

See [`design.md`](./design.md) for the design decisions, architecture, implementation approach, and potential future improvements.

## Security Considerations

- Keep API credentials in environment variables.
- Never expose authentication tokens or API keys.
- Enforce conversation ownership and user authorization.
- Validate incoming API requests.
- Handle external API failures safely.

## Future Improvements

- Streaming responses.
- Better retry and timeout handling.
- Improved source citation formatting.
- Dedicated automated tests for chat workflows.
- Conversation summarization for longer histories.
- More robust monitoring and observability.

## Author

**Kundan Kumar**

GitHub: https://github.com/Kundank8789

---

Built as an extension of AgentOS to explore practical AI agents with web search and persistent conversational memory.
