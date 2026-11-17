# AgentOS Web Search Chat Agent — Design Document

## 1. Overview

This project extends AgentOS with a conversational AI agent that can search the web, answer questions using current information, and remember previous conversations.

The chat agent uses one external tool: Tavily Web Search.

The existing AgentOS authentication and business workflows remain unchanged.

## 2. Architecture

The system consists of:

- Frontend: Next.js
- Backend: FastAPI
- LLM: Groq API
- External tool: Tavily Search API
- Database: PostgreSQL
- ORM: SQLAlchemy
- Migrations: Alembic
- Cache and notification infrastructure: Redis

### Request flow

1. User submits a message.
2. FastAPI validates the request and authenticates the user.
3. The chat service creates or retrieves the conversation.
4. Previous messages are loaded from PostgreSQL.
5. The chat runtime sends the conversation context to the Groq model.
6. When web information is needed, the model calls the Tavily web search tool.
7. Search results are returned to the model.
8. The model generates an answer with source references.
9. User and assistant messages are persisted in PostgreSQL.
10. The API returns the answer, sources, conversation ID and timestamp.

## 3. Single Tool Design

The agent has one external tool:

### Web Search

Tool name: `web_search`

Provider: Tavily

Responsibilities:
- Search the public web.
- Retrieve relevant pages.
- Return titles, URLs, snippets and relevance scores.
- Provide source material for grounded responses.

The agent uses web search when the user asks for current information or explicitly requests a web search.

No additional external tools are exposed to this chat runtime.

## 4. Conversation Memory

Conversation memory is implemented using PostgreSQL.

### Conversations table

Stores:
- Conversation ID
- Organization ID
- User ID
- Conversation title
- Creation timestamp
- Last updated timestamp

### Chat messages table

Stores:
- Message ID
- Conversation ID
- Role
- Message content
- Search sources
- Creation timestamp

The latest conversation messages are loaded and passed to the LLM as context.

This allows the agent to answer follow-up questions using earlier messages.

Conversation access is scoped to the authenticated user and organization.

## 5. API Endpoints

### POST /chat/message

Sends a message and returns an AI-generated response.

Request:

    {
      "message": "What are the latest AI developments?"
    }

An optional conversation_id continues an existing conversation.

Response includes:
- conversation_id
- message_id
- answer
- sources
- created_at

### GET /chat/conversations

Returns conversations belonging to the authenticated user.

### GET /chat/conversations/{conversation_id}/messages

Returns the message history for an authorized conversation.

## 6. Model and Tool Execution

The Groq chat completion API is responsible for response generation and tool selection.

The runtime:
1. Builds the system prompt and conversation context.
2. Provides the web_search function definition.
3. Allows the model to decide whether search is necessary.
4. Executes the Tavily search when requested.
5. Passes search results back to the model.
6. Returns the final response and source metadata.

## 7. Reliability and Error Handling

The implementation includes:
- Request validation using Pydantic.
- Authentication through existing AgentOS dependencies.
- Conversation ownership checks.
- Search error handling.
- Database persistence.
- Structured API responses.

Search failures should not be represented as successful verification. The assistant should communicate when current information could not be verified.

## 8. Security

- Existing AgentOS JWT authentication is reused.
- Conversation queries are scoped by user and organization.
- API credentials are stored in environment variables.
- Secrets are excluded from Git.
- The chat agent does not expose additional business workflow tools.

## 9. Testing and Validation

The following have been manually validated:

- Existing AgentOS login.
- Authenticated chat API request.
- Tavily web search returning real sources.
- Groq response generation.
- Conversation persistence.
- Follow-up question answered using conversation history.
- Message timestamps retrieved from PostgreSQL.

The existing automated backend test suite completed successfully with 22 passing tests.

## 10. Design Trade-offs

- Tavily is used as the single external tool to keep the agent focused.
- Groq provides the language model interface.
- PostgreSQL provides durable conversation memory.
- Recent conversation messages are used as context to limit prompt size and response latency.
- Existing authentication and AgentOS workflows are reused to avoid duplicating infrastructure.

## 11. Future Improvements

- Add dedicated automated tests for chat endpoints and tool execution.
- Improve search failure recovery and retries.
- Add token usage and latency monitoring.
- Introduce configurable conversation context limits.
- Add streaming responses to improve perceived response speed.
- Improve source quality evaluation and citation verification.
