import logging
import re
from typing import Any, Dict, List, Optional
from uuid import UUID

from google.genai import types
from sqlalchemy.orm import Session

from app.models.media import Media, MediaMetadata
from app.services.ml_services import MODEL_NAME, client
from app.services.temporal_filtering import filter_media_by_date_time

FUNCTION_DEFINITIONS = [
    types.FunctionDeclaration(
        name="filter_by_date",
        description=(
            "Filter media by date and time. Use when query mentions dates, times, or relative periods. "
            "Supports flexible expressions like '5 minutes ago', '2 hours ago', '3 days ago', 'last week', "
            "'yesterday', 'this month', etc."
        ),
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "relative_time": types.Schema(
                    type=types.Type.STRING,
                    description=(
                        "Relative time expression. Examples: "
                        "'5 minutes ago', '30 seconds ago', '2 hours ago', "
                        "'3 days ago', '2 weeks ago', '1 month ago', "
                        "'today', 'yesterday', 'last week', 'this week', "
                        "'last month', 'this month', 'last year', 'this year'"
                    ),
                ),
                "time_range": types.Schema(
                    type=types.Type.STRING,
                    description="Optional time range within the day: 'morning', 'afternoon', 'evening', 'night'",
                    enum=["morning", "afternoon", "evening", "night"],
                ),
            },
            required=["relative_time"],
        ),
    ),
    types.FunctionDeclaration(
        name="semantic_search",
        description="Search media content using semantic similarity. Use for content-based searches.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "query": types.Schema(
                    type=types.Type.STRING,
                    description="Search query describing what to look for",
                )
            },
            required=["query"],
        ),
    ),
    types.FunctionDeclaration(
        name="analyze_text",
        description="Analyze text content in media to find specific information like names, numbers, addresses.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "search_type": types.Schema(
                    type=types.Type.STRING,
                    description="Type of information to find",
                    enum=["names", "phone_numbers", "addresses", "dates", "general"],
                )
            },
            required=["search_type"],
        ),
    ),
    types.FunctionDeclaration(
        name="get_media_details",
        description=(
            "Get full details of specific media items including complete OCR text, captions, "
            "and metadata. Use this when you need to read or analyze the full content of media files."
        ),
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "media_ids": types.Schema(
                    type=types.Type.ARRAY,
                    description="List of media IDs to retrieve full details for",
                    items=types.Schema(type=types.Type.STRING),
                )
            },
            required=["media_ids"],
        ),
    ),
    types.FunctionDeclaration(
        name="count_media",
        description=(
            "Retrieve the total number of media items uploaded by a user. Can optionally filter by media type"
            "(image, video, document, audio) and/or by specific timeframes such as 'yesterday', 'last week', or a custom date range."
            "Use this when the user asks how many files or media items they have, including any specific type or date-based queries"
            "like 'How many images did I upload yesterday?' or 'Count my videos from last week.'"
        ),
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "media_type": types.Schema(
                    type=types.Type.STRING,
                    description="Optional: Filter by media type",
                    enum=["image", "video", "document", "audio", "all"],
                ),
            },
        ),
    ),
]


def generate_query_embeddings(query: str) -> Optional[List[float]]:
    try:
        result = client.models.embed_content(
            model="gemini-embedding-001",
            contents=[query],
            config=types.EmbedContentConfig(
                output_dimensionality=1536,
                task_type="RETRIEVAL_QUERY",
            ),
        )

        if result.embeddings:
            return result.embeddings[0].values
        return None
    except Exception as e:
        logging.error(f"Error generating query embeddings: {e}")
        return None


def search_by_embeddings(
    db: Session, query: str, user_id: UUID, limit: int = 10
) -> List[Dict[str, Any]]:
    try:
        query_embeddings = generate_query_embeddings(query)
        if not query_embeddings:
            return []

        results = (
            db.query(
                Media.id.label("media_id"),
                Media.file_name,
                Media.file_type,
                MediaMetadata.created_at,
                MediaMetadata.caption,
                MediaMetadata.ocr_text,
                (1 - MediaMetadata.embeddings.cosine_distance(query_embeddings)).label(
                    "similarity_score"
                ),
            )
            .join(Media, MediaMetadata.media_id == Media.id)
            .filter(MediaMetadata.embeddings.isnot(None), Media.user_id == user_id)
            .order_by(MediaMetadata.embeddings.cosine_distance(query_embeddings))
            .limit(limit)
            .all()
        )

        formatted_results = []
        for row in results:
            formatted_results.append(
                {
                    "media_id": str(row.media_id),
                    "file_name": row.file_name,
                    "file_type": row.file_type,
                    "created_at": row.created_at.isoformat(),
                    "caption": row.caption,
                    "ocr_text": row.ocr_text[:200] + "..."
                    if row.ocr_text and len(row.ocr_text) > 200
                    else row.ocr_text,
                    "similarity_score": float(row.similarity_score),
                }
            )

        return formatted_results

    except Exception as e:
        logging.error(f"Error in embedding search: {e}")
        return []


def analyze_text_content(
    db: Session, search_type: str, user_id: UUID
) -> List[Dict[str, Any]]:
    try:
        recent_media = (
            db.query(MediaMetadata, Media)
            .join(Media, MediaMetadata.media_id == Media.id)
            .filter(Media.user_id == user_id, MediaMetadata.ocr_text.isnot(None))
            .order_by(MediaMetadata.created_at.desc())
            .limit(20)
            .all()
        )

        results = []

        for metadata, media in recent_media:
            ocr_text = metadata.ocr_text or ""
            found_items = []

            if search_type == "names":
                names = re.findall(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b", ocr_text)
                found_items = names

            elif search_type == "phone_numbers":
                phones = re.findall(
                    r"\b\d{3}-\d{3}-\d{4}\b|\b\(\d{3}\)\s*\d{3}-\d{4}\b", ocr_text
                )
                found_items = phones

            elif search_type == "addresses":
                addresses = re.findall(
                    r"\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd)\b",
                    ocr_text,
                    re.IGNORECASE,
                )
                found_items = addresses

            elif search_type == "dates":
                dates = re.findall(
                    r"\b\d{1,2}/\d{1,2}/\d{2,4}\b|\b\d{4}-\d{1,2}-\d{1,2}\b", ocr_text
                )
                found_items = dates

            elif search_type == "general":
                found_items = [
                    ocr_text[:300] + "..." if len(ocr_text) > 300 else ocr_text
                ]

            if found_items:
                results.append(
                    {
                        "media_id": str(media.id),
                        "file_name": media.file_name,
                        "created_at": metadata.created_at.isoformat(),
                        "found_items": found_items,
                        "search_type": search_type,
                    }
                )

        return results[:10]

    except Exception as e:
        logging.error(f"Error analyzing text content: {e}")
        return []


def get_media_details(
    db: Session, media_ids: List[str], user_id: UUID
) -> List[Dict[str, Any]]:
    try:
        results = []

        for media_id_str in media_ids:
            try:
                media_id = UUID(media_id_str)
            except ValueError:
                logging.warning(f"Invalid media ID format: {media_id_str}")
                continue

            media = (
                db.query(Media)
                .filter(Media.id == media_id, Media.user_id == user_id)
                .first()
            )

            if not media:
                logging.warning(f"Media not found or access denied: {media_id_str}")
                continue

            metadata = (
                db.query(MediaMetadata)
                .filter(MediaMetadata.media_id == media_id)
                .first()
            )

            if metadata:
                results.append(
                    {
                        "media_id": str(media.id),
                        "file_name": media.file_name,
                        "file_type": media.file_type.value,
                        "created_at": metadata.created_at.isoformat(),
                        "caption": metadata.caption,
                        "ocr_text": metadata.ocr_text,
                        "duration": media.duration,
                    }
                )

        return results

    except Exception as e:
        logging.error(f"Error getting media details: {e}")
        return []


def count_media(db: Session, user_id: UUID, media_type: str = "all") -> Dict[str, Any]:
    try:
        query = db.query(Media).filter(Media.user_id == user_id)

        if media_type and media_type != "all":
            query = query.filter(Media.file_type == media_type)

        count = query.count()

        return {
            "count": count,
            "media_type": media_type,
        }

    except Exception as e:
        logging.error(f"Error counting media: {e}")
        return {"count": 0, "media_type": media_type, "error": str(e)}


def execute_function(db: Session, function_call, user_id: UUID) -> types.Part | None:
    function_name = function_call.name
    args = function_call.args
    print("=" * 55)
    print(f"Executing function {function_name} with args {args}")
    print("=" * 55)

    try:
        if function_name == "filter_by_date":
            results = filter_media_by_date_time(db=db, user_id=user_id, **args)

            formatted_results = []
            for metadata in results:
                media = db.query(Media).filter(Media.id == metadata.media_id).first()
                if media:
                    formatted_results.append(
                        {
                            "media_id": str(media.id),
                            "file_name": media.file_name,
                            "file_type": media.file_type.value,
                            "created_at": metadata.created_at.isoformat(),
                            "caption": metadata.caption,
                            # Return preview for date filtering, with media_id for follow-up
                            "ocr_text_preview": metadata.ocr_text[:200] + "..."
                            if metadata.ocr_text and len(metadata.ocr_text) > 200
                            else metadata.ocr_text,
                        }
                    )

            return types.Part.from_function_response(
                name=function_name, response={"results": formatted_results}
            )

        elif function_name == "semantic_search":
            results = search_by_embeddings(db=db, user_id=user_id, **args)

            return types.Part.from_function_response(
                name=function_name, response={"results": results}
            )

        elif function_name == "analyze_text":
            results = analyze_text_content(db=db, user_id=user_id, **args)

            return types.Part.from_function_response(
                name=function_name, response={"results": results}
            )

        elif function_name == "get_media_details":
            results = get_media_details(db=db, user_id=user_id, **args)

            return types.Part.from_function_response(
                name=function_name, response={"results": results}
            )

        elif function_name == "count_media":
            result = count_media(db=db, user_id=user_id, **args)

            return types.Part.from_function_response(
                name=function_name, response=result
            )

    except Exception as e:
        logging.error(f"Error executing function {function_name}: {e}")
        return None


def process_query(db: Session, query: str, user_id: UUID) -> Dict[str, Any]:
    try:
        logging.info(f"Processing query: '{query}' for user: {user_id}")

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
1. First use `filter_by_date` to find relevant media items
2. Then use `get_media_details` with the returned media_ids to get full OCR text
3. Finally, answer the user's question based on the complete content

Example: "What was written on the page uploaded last hour?"
- Step 1: Call `filter_by_date` with "1 hour ago"
- Step 2: Call `get_media_details` with the media_id from step 1
- Step 3: Read the full ocr_text and provide the answer

### 🗣️ Response Style
- Be **precise**, **helpful**, and **grounded in the data** retrieved.
- If a question cannot be answered from available media, clearly say so.
- When you cite files, include their names (e.g., *"Based on 'invoice_2024.pdf'…"*).
- Do not hallucinate or assume information not present in the data.
- When showing OCR text, present it clearly and format it if needed.

### ⚙️ Tool Use Policy
- Always prefer using retrieval functions before answering factual queries.
- When the initial search returns truncated text (ocr_text_preview), use `get_media_details` to get the full content.
- You can combine multiple tool calls to form multi-step reasoning chains.
- Only return final text answers to the user — not raw data or embeddings.

Now begin assisting the user. Interpret their intent intelligently and call functions as needed.
"""

        tools = types.Tool(function_declarations=FUNCTION_DEFINITIONS)
        config = types.GenerateContentConfig(
            tools=[tools], system_instruction=system_prompt
        )

        contents: types.ContentListUnionDict = [
            types.Content(
                role="user",
                parts=[types.Part(text=query)],
            )
        ]

        # Allow multiple rounds of function calling
        max_iterations = 5
        iteration = 0

        while iteration < max_iterations:
            response = client.models.generate_content(
                model=MODEL_NAME, contents=contents, config=config
            )

            if not (
                response.candidates
                and response.candidates[0].content
                and response.candidates[0].content.parts
            ):
                break

            has_function_call = False

            for part in response.candidates[0].content.parts:
                if part.function_call:
                    has_function_call = True
                    function_response_part = execute_function(
                        db, part.function_call, user_id
                    )

                    contents.append(response.candidates[0].content)

                    if function_response_part:
                        contents.append(
                            types.Content(role="user", parts=[function_response_part])
                        )

            # No more function calls, we have the final response
            if not has_function_call:
                break

            iteration += 1

        logging.info(f"Completed after {iteration + 1} iterations")

        final_response = client.models.generate_content(
            model=MODEL_NAME,
            config=config,
            contents=contents,
        )

        return {
            "response": final_response.text,
        }

    except Exception as e:
        logging.error(f"Error processing query '{query}': {e}")
        return {
            "error": str(e),
        }
