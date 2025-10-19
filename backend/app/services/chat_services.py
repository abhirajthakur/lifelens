import json
import logging
from typing import AsyncGenerator, Dict, List, Optional
from uuid import UUID

from google.genai import types
from sqlalchemy.orm import Session

from app.models.chat import Conversation, Message, MessageRole
from app.services.ml_services import MODEL_NAME, client
from app.services.query_processor import (
    FUNCTION_DEFINITIONS,
    execute_function,
)


def create_conversation(
    db: Session, user_id: UUID, title: str = "New Conversation"
) -> Conversation:
    conversation = Conversation(user_id=user_id, title=title)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    logging.info(f"Created conversation {conversation.id} for user {user_id}")
    return conversation


def get_conversation(
    db: Session, conversation_id: UUID, user_id: UUID
) -> Optional[Conversation]:
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == user_id)
        .first()
    )

    return conversation


def list_conversations(
    db: Session,
    user_id: UUID,
    skip: int = 0,
    limit: int = 20,
) -> List[Conversation]:
    conversations = (
        db.query(Conversation)
        .filter(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return conversations


def add_message(
    db: Session,
    conversation_id: UUID,
    role: MessageRole,
    content: str,
    function_calls: Optional[List[Dict]] = None,
) -> Message:
    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        function_calls=json.dumps(function_calls) if function_calls else None,
    )

    db.add(message)

    conversation = (
        db.query(Conversation).filter(Conversation.id == conversation_id).first()
    )
    if conversation:
        from datetime import datetime, timezone

        conversation.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(message)

    return message


def get_conversation_messages(
    db: Session, conversation_id: UUID, limit: Optional[int] = None
) -> List[Message]:
    query = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    )

    if limit:
        query = query.limit(limit)

    return query.all()


def build_conversation_history(messages: List[Message]):
    contents: types.ContentListUnionDict = [
        types.Content(role="system", parts=[types.Part(text="You are LifeLens.")])
    ]
    contents.pop()
    # above is the workaround because the content being an empty list gives eror and
    # since i'm removing the first element every time, it's not a problem

    for message in messages:
        role = "user" if message.role == MessageRole.USER else "model"

        contents.append(
            types.Content(role=role, parts=[types.Part(text=message.content)])
        )

    return contents


def generate_conversation_title(first_message: str) -> str:
    try:
        prompt = f"""Generate a short, concise title (max 50 characters) for a conversation that starts with this message:

"{first_message[:200]}"

Return ONLY the title, nothing else."""

        response = client.models.generate_content(
            model=MODEL_NAME, contents=[types.Part(text=prompt)]
        )

        if response.text is None:
            raise ValueError("No response generated")

        title = response.text.strip().strip("\"'")
        return title[:50] if len(title) > 50 else title

    except Exception as e:
        logging.error(f"Error generating title: {e}")
        words = first_message.split()[:5]
        return " ".join(words) + ("..." if len(first_message.split()) > 5 else "")


async def process_chat_message_stream(
    db: Session, conversation_id: UUID, user_id: UUID, message: str
) -> AsyncGenerator[str, None]:
    try:
        logging.info(f"Processing chat message in conversation {conversation_id}")

        conversation = get_conversation(db, conversation_id, user_id)
        if not conversation:
            yield f"data: {json.dumps({'error': 'Conversation not found'})}\n\n"
            return

        add_message(
            db=db,
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=message,
        )

        all_messages = get_conversation_messages(db, conversation_id)

        recent_messages = all_messages[-11:-1] if len(all_messages) > 1 else []
        conversation_history = build_conversation_history(recent_messages)

        conversation_history.append(
            types.Content(role="user", parts=[types.Part(text=message)])
        )

        system_prompt = """
You are **LifeLens**, an intelligent AI media assistant that helps users query, explore, and reason over their personal media collection.

### 🔍 Your Purpose
You help users find information or insights from their uploaded media — which may include:
- Documents (PDFs, notes, reports)
- Images (screenshots, infographics)
- Audio and Video (meetings, lectures, voice notes)

You use structured tools (functions) to **retrieve**, **analyze**, **summarize**, and **converse** about this content intelligently.

### 🧰 Your Abilities
You can:
1. Retrieve semantically relevant media using vector search.
2. Filter media by date and time periods.
3. Get full details of specific media items including complete OCR text.
4. Count media items by type.
5. Extract or compare information across multiple files.
6. Continue conversationally using prior context and user intent.
7. Chain multiple tool calls if needed (e.g., filter by date first, then get full details).

### 🔗 Multi-Step Reasoning
When a user asks about content in recent media:
1. First use `filter_by_date` or `semantic_search` to find relevant media items
2. EXTRACT the **media_id** field (UUID format) from the results
3. Then use `get_media_details` with those EXACT media_id values to get full content
4. Finally, answer the user's question based on the complete content

### 🆔 CRITICAL: Media ID Usage
**IMPORTANT**: When calling `get_media_details`:
- ✅ ALWAYS use the `media_id` field from previous search results (UUID format like '9a3960ad-8ec5-4061-a359-6d26d990945a')
- ❌ NEVER use file names (e.g., 'document.pdf')
- ❌ NEVER use numeric IDs (e.g., '12345')
- ❌ NEVER make up or guess IDs

**Example of correct usage:**
```
Step 1: filter_by_date returns:
{
  "results": [
    {"media_id": "9a3960ad-8ec5-4061-a359-6d26d990945a", "file_name": "receipt.jpg"},
    {"media_id": "b2c4d5e6-7890-1234-5678-90abcdef1234", "file_name": "invoice.pdf"}
  ]
}

Step 2: Call get_media_details with:
{
  "media_ids": ["9a3960ad-8ec5-4061-a359-6d26d990945a", "b2c4d5e6-7890-1234-5678-90abcdef1234"]
}
```

Example: "What was written on the page uploaded last hour?"
- Step 1: Call `filter_by_date` with "1 hour ago"
- Step 2: Call `get_media_details` with the media_id from step 1
- Step 3: Read the full ocr_text and provide the answer

### 🔁 Tool Chaining Instructions (Critical)

- When the user's query involves both a **count** and **content**, you **must** call multiple tools.
- For example, if the user asks for a count of PDFs and their content:
  1. First call `count_media` with `media_type='pdf'`.
  2. Then call `get_media_details` or `analyze_text` to retrieve or summarize their content.
  3. Combine both results and return a final summary.

- You can chain multiple functions in one response cycle to fully answer user intent.

### 🗣️ Response Style
- Be **precise**, **helpful**, and **grounded in the data** retrieved
- Reference previous messages when relevant
- If a question cannot be answered from available media, clearly say so
- When you cite files, include their names (e.g., *"Based on 'invoice_2024.pdf'…"*)
- Do not hallucinate or assume information not present in the data
- When showing OCR text, present it clearly and format it if needed

### ⚙️ Tool Use Policy
- Always prefer using retrieval functions before answering factual queries
- When the initial search returns truncated text (ocr_text_preview), use `get_media_details` to get the full content
- You can combine multiple tool calls to form multi-step reasoning chains
- Only return final text answers to the user — not raw data or embeddings
- ALWAYS extract and use the correct media_id from previous results



Now begin assisting the user. Interpret their intent intelligently and call functions as needed.
"""

        tools = types.Tool(function_declarations=FUNCTION_DEFINITIONS)
        config = types.GenerateContentConfig(
            tools=[tools], system_instruction=system_prompt
        )

        function_calls_made = []
        accumulated_text = ""

        max_iterations = 5
        iteration = 0

        while iteration < max_iterations:
            response_stream = client.models.generate_content_stream(
                model=MODEL_NAME, contents=conversation_history, config=config
            )

            has_function_call = False
            chunk_text = ""

            for chunk in response_stream:
                if chunk.candidates and chunk.candidates[0].content:
                    content = chunk.candidates[0].content
                    if not content.parts:
                        continue

                    # Check for function calls
                    for part in content.parts:
                        if part.function_call:
                            has_function_call = True
                            func_info = {
                                "type": "function_call",
                                "name": part.function_call.name,
                                "args": part.function_call.args,
                            }
                            yield f"data: {json.dumps(func_info)}\n\n"

                            function_calls_made.append(func_info)

                            function_response_part = execute_function(
                                db, part.function_call, user_id
                            )

                            conversation_history.append(content)

                            if function_response_part:
                                conversation_history.append(
                                    types.Content(
                                        role="user", parts=[function_response_part]
                                    )
                                )

                        elif part.text:
                            chunk_text += part.text
                            accumulated_text += part.text
                            yield f"data: {json.dumps({'type': 'text', 'content': part.text})}\n\n"

            if not has_function_call:
                break

            iteration += 1

        if accumulated_text:
            assistant_message = add_message(
                db=db,
                conversation_id=conversation_id,
                role=MessageRole.ASSISTANT,
                content=accumulated_text,
                function_calls=function_calls_made if function_calls_made else None,
            )

            # Auto-generate title for first message
            if len(all_messages) == 1:
                title = generate_conversation_title(message)
                conversation.title = title
                db.commit()

            # Send completion event
            yield f"data: {json.dumps({'type': 'done', 'message_id': assistant_message.id})}\n\n"
        else:
            yield f"data: {json.dumps({'type': 'error', 'message': 'No response generated'})}\n\n"

    except Exception as e:
        logging.error(f"Error in streaming chat: {e}", exc_info=True)
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"


def delete_conversation(db: Session, conversation_id: UUID, user_id: UUID) -> bool:
    conversation = get_conversation(db, conversation_id, user_id)
    if not conversation:
        return False

    db.delete(conversation)
    db.commit()

    logging.info(f"Deleted conversation {conversation_id}")
    return True


def update_conversation_title(
    db: Session, conversation_id: UUID, user_id: UUID, new_title: str
) -> Optional[Conversation]:
    conversation = get_conversation(db, conversation_id, user_id)
    if not conversation:
        return None

    conversation.title = new_title
    db.commit()
    db.refresh(conversation)

    return conversation
