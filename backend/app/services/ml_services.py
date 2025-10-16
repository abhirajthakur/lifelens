import logging
import os
import io
from io import BytesIO
from typing import List, Optional, Tuple
from uuid import UUID

from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image
from sqlalchemy.orm import Session

from app.models.media import Media, MediaMetadata

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-2.5-flash-preview-05-20"

client = genai.Client(api_key=API_KEY)


def generate_image_caption(image_bytes: bytes) -> str:
    try:
        img = Image.open(BytesIO(image_bytes))
        img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)

        instruction = (
            "Generate a concise caption describing the main content of this image."
        )

        response = client.models.generate_content(
            model=MODEL_NAME, contents=[instruction, img]
        )

        if response.text is None:
            logging.error("No caption generated from image")
            return ""

        logging.info("Caption generated from image: %s", response.text)
        return response.text
    except Exception as e:
        logging.error("Error generating caption from image: %s", e)
        return ""


def image_to_text(image_bytes: bytes) -> str:
    try:
        img = Image.open(BytesIO(image_bytes))
        img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)

        instruction = """
        Extract ALL text content from this image with high accuracy. Include both printed and handwritten text.

        Extract:
        - All printed text (typed, computer-generated)
        - All handwritten text (cursive, print, notes, signatures if readable)
        - Text in any orientation or size
        - Text in tables, forms, or structured layouts
        - Numbers, dates, addresses, phone numbers
        - Text that appears faded, small, or partially visible

        For structured documents:
        - Maintain table structure using markdown table format
        - Preserve paragraph breaks and formatting
        - Keep headers, footers, and sections organized
        - Preserve field labels and their corresponding values

        If text is unclear, provide your best interpretation and mark as [unclear: text].
        Focus on accuracy and completeness.
        """

        response = client.models.generate_content(
            model=MODEL_NAME, contents=[instruction, img]
        )

        if response.text is None:
            logging.error("No text extracted from image")
            return ""

        extracted_text = response.text.strip()
        logging.info(
            "Enhanced text extracted from image: %s",
            extracted_text[:100] + "..."
            if len(extracted_text) > 100
            else extracted_text,
        )
        return extracted_text
    except Exception as e:
        logging.error("Error extracting text from image: %s", e)
        return ""


def generate_embeddings(text: str) -> Optional[list[float]]:
    try:
        result = client.models.embed_content(
            model="gemini-embedding-001",
            contents=[text],
            config=types.EmbedContentConfig(
                output_dimensionality=1536,
                task_type="RETRIEVAL_DOCUMENT",
            ),
        )

        if result.embeddings is None:
            logging.error("No embeddings generated for text")
            return []

        logging.info(
            "Document embeddings generated for text: %s",
            text[:50] + "..." if len(text) > 50 else text,
        )
        return result.embeddings[0].values
    except Exception as e:
        logging.error("Error generating embeddings for text: %s", e)
        return []


def generate_summary_and_topics(
    content: str, content_type: str = "document"
) -> Tuple[Optional[str], Optional[List[str]]]:
    try:
        if not content or not content.strip():
            return None, None

        content_preview = content[:4000] if len(content) > 4000 else content

        summary_prompt = f"""
        Provide a concise 2-3 sentence summary of the following {content_type} content:

        {content_preview}

        Focus on the main ideas, key information, and overall purpose.
        """

        summary_response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[summary_prompt],
        )
        summary = summary_response.text.strip() if summary_response.text else None

        topics_prompt = f"""
        Extract 3-7 key topics or themes from the following {content_type} content.
        Return ONLY a comma-separated list of topics (no explanations, no numbering).

        {content_preview}

        Examples of good topics: "machine learning", "project management", "budget planning", "travel itinerary"
        """

        topics_response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[topics_prompt],
        )

        topics = None
        if topics_response.text:
            topics_text = topics_response.text.strip()
            topics = [
                topic.strip() for topic in topics_text.split(",") if topic.strip()
            ]
            # Limit to 10 topics max
            topics = topics[:10] if topics else None

        return summary, topics

    except Exception as e:
        logging.error(f"Error generating summary and topics: {e}")
        return None, None


def process_image(db: Session, media_id: UUID, image_bytes: bytes) -> bool:
    try:
        caption = generate_image_caption(image_bytes)
        ocr_text = image_to_text(image_bytes)

        combined_text = f"Caption: {caption.strip()} OCR: {ocr_text.strip()}"

        embeddings = generate_embeddings(combined_text)
        if not embeddings:
            logging.error("No embeddings generated for image")
            return False

        logging.info("Embeddings generated for image")

        metadata = MediaMetadata(
            media_id=media_id, caption=caption, ocr_text=ocr_text, embeddings=embeddings
        )
        logging.info("Metadata generated for image: %s", metadata)

        db.add(metadata)
        db.commit()

        return True
    except Exception as e:
        logging.error("Error processing image: %s", e)
        return False


def process_audio(db: Session, media_id: UUID, audio_bytes: bytes) -> bool:
    try:
        logging.info(f"Processing audio for media_id: {media_id}")

        uploaded_file = client.files.upload(file=io.BytesIO(audio_bytes))

        transcription_prompt = """
        Transcribe all spoken content from this audio file.
        Include:
        1. All speech and dialogue
        2. Speaker identification if multiple speakers
        3. Notable background sounds or music
        4. Timestamps for different sections if applicable

        Format as a clear, readable transcript.
        If there's no speech, respond with 'No speech detected'.
        """

        transcription_response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[transcription_prompt, uploaded_file],
        )
        transcript = transcription_response.text if transcription_response.text else ""

        if transcript.strip().lower() == "no speech detected":
            transcript = None

        if transcript:
            caption = (
                f"Audio recording: {transcript[:150]}..."
                if len(transcript) > 150
                else f"Audio recording: {transcript}"
            )
        else:
            caption = "Audio file with no detectable speech"

        content_for_analysis = transcript if transcript else caption
        summary, topics = generate_summary_and_topics(content_for_analysis, "audio")

        embeddings = generate_embeddings(content_for_analysis)

        metadata = MediaMetadata(
            media_id=media_id,
            caption=caption,
            transcript=transcript,
            summary=summary,
            topics=topics,
            embeddings=embeddings,
        )

        db.add(metadata)
        db.commit()

        logging.info(f"Successfully processed audio for media_id: {media_id}")
        return True

    except Exception as e:
        logging.error(f"Error processing audio for media_id {media_id}: {e}")
        db.rollback()
        return False


def process_text(db: Session, media_id: UUID, text_content: bytes) -> bool:
    try:
        logging.info(f"Processing text document for media_id: {media_id}")

        media = db.query(Media).filter(Media.id == media_id).first()
        if not media:
            logging.error(f"Media not found: {media_id}")
            return False

        extracted_text = ""

        if media.file_name.lower().endswith(".pdf"):
            try:
                import PyPDF2

                pdf_file = io.BytesIO(text_content)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                extracted_text = ""
                for page in pdf_reader.pages:
                    extracted_text += page.extract_text() + "\n"
            except Exception as e:
                logging.warning(f"PyPDF2 failed, trying with Gemini: {e}")
                extract_prompt = "Extract all text from this PDF document. Maintain formatting and structure."

                response = client.models.generate_content(
                    model=MODEL_NAME,
                    contents=[
                        types.Part.from_bytes(
                            data=text_content,
                            mime_type="application/pdf",
                        ),
                        extract_prompt,
                    ],
                )

                extracted_text = response.text if response.text else ""

        elif media.file_name.lower().endswith((".docx", ".doc")):
            try:
                import docx

                doc = docx.Document(io.BytesIO(text_content))
                extracted_text = "\n".join([para.text for para in doc.paragraphs])
            except Exception as e:
                logging.error(f"Error extracting from Word document: {e}")
                extracted_text = text_content.decode("utf-8", errors="ignore")

        else:
            try:
                extracted_text = text_content.decode("utf-8")
            except UnicodeDecodeError:
                extracted_text = text_content.decode("utf-8", errors="ignore")

        if not extracted_text.strip():
            logging.warning(f"No text extracted from document: {media_id}")
            extracted_text = "Empty document"

        caption = extracted_text[:200] if len(extracted_text) > 200 else extracted_text

        summary, topics = generate_summary_and_topics(extracted_text, "document")

        embeddings = generate_embeddings(extracted_text)

        metadata = MediaMetadata(
            media_id=media_id,
            caption=caption,
            summary=summary,
            topics=topics,
            embeddings=embeddings,
        )

        db.add(metadata)
        db.commit()

        logging.info(f"Successfully processed text document for media_id: {media_id}")
        return True

    except Exception as e:
        logging.error(f"Error processing text document for media_id {media_id}: {e}")
        db.rollback()
        return False
