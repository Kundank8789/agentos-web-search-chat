
import json
from typing import Any

from openai import AsyncOpenAI

from app.config import settings
from app.tools.web_search import WebSearchTool


client = AsyncOpenAI(
    api_key=settings.groq_api_key,
    base_url="https://api.groq.com/openai/v1",
)


WEB_SEARCH_DEFINITION = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": (
            "Search the internet for current information, "
            "recent events, updated facts, or information "
            "that needs reliable external sources. "
            "Use this when the user explicitly asks to search "
            "or when current information is necessary."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "A concise web search query.",
                }
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
}


SYSTEM_PROMPT = """
You are a helpful, accurate, and conversational AI assistant.

Your responsibilities:
1. Answer questions clearly and directly.
2. Use the conversation history to understand follow-up questions.
3. Remember relevant details from earlier messages in this conversation.
4. Use web_search when current information or external verification
   is needed, or when the user explicitly requests a web search.
5. Do not use web search for simple, stable, general knowledge.
6. Never invent search results, facts, URLs, or citations.
7. When search results are available, use them to support your answer.
8. Cite relevant search results using [1], [2], etc.
9. If search fails, clearly explain that current information
   could not be verified.
10. Be concise but sufficiently detailed.

You have exactly one external tool: web_search.
Never claim to have used a tool if you did not use it.
"""


async def generate_chat_response(
    user_message: str,
    history: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        }
    ]

    # Include recent conversation history.
    for item in (history or [])[-12:]:
        role = item.get("role")
        content = item.get("content")

        if role in {"user", "assistant"} and content:
            messages.append({
                "role": role,
                "content": content,
            })

    messages.append({
        "role": "user",
        "content": user_message,
    })

    # First LLM call: decide whether web search is needed.
    response = await client.chat.completions.create(
        model=settings.groq_model,
        messages=messages,
        tools=[WEB_SEARCH_DEFINITION],
        tool_choice="auto",
        temperature=0.2,
        max_tokens=1200,
    )

    assistant_message = response.choices[0].message

    sources: list[dict[str, str]] = []

    # Process at most one external tool call.
    if assistant_message.tool_calls:
        tool_call = next(
            (
                call
                for call in assistant_message.tool_calls
                if call.function.name == "web_search"
            ),
            None,
        )

        if tool_call is not None:
            try:
                arguments = json.loads(
                    tool_call.function.arguments
                )

                query = arguments.get("query", "").strip()

                if not query:
                    raise ValueError("Search query is empty.")

                search_tool = WebSearchTool()

                search_result = await search_tool.execute(
                    query=query
                )

                if search_result.get("success"):
                    sources = [
                        {
                            "title": item.get("title", ""),
                            "url": item.get("url", ""),
                            "snippet": item.get("snippet", ""),
                        }
                        for item in search_result.get("results", [])
                    ]

                # Add the assistant tool-call message.
                messages.append({
                    "role": "assistant",
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": "web_search",
                                "arguments": tool_call.function.arguments,
                            },
                        }
                    ],
                })

                # Give search results to the LLM.
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(search_result),
                })

                # Second LLM call: generate the final answer.
                final_response = await client.chat.completions.create(
                    model=settings.groq_model,
                    messages=messages,
                    temperature=0.2,
                    max_tokens=1500,
                )

                answer = (
                    final_response.choices[0].message.content
                    or "I couldn't generate an answer."
                )

                return {
                    "answer": answer,
                    "sources": sources,
                    "search_used": True,
                }

            except (ValueError, TypeError, json.JSONDecodeError):
                pass

    # No web search was needed.
    answer = assistant_message.content or (
        "I couldn't generate an answer. Please try again."
    )

    return {
        "answer": answer,
        "sources": sources,
        "search_used": False,
    }
