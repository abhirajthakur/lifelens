import logging
import os
from io import BytesIO
from typing import Optional
from uuid import UUID

from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image
from sqlalchemy.orm import Session

from app.models.media import MediaMetadata

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
    """Generate embeddings optimized for document storage and retrieval."""
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


def process_image(db: Session, media_id: UUID, image_bytes: bytes):
    try:
        caption = generate_image_caption(image_bytes)
        ocr_text = image_to_text(image_bytes)

        caption_embeddings = generate_embeddings(caption) or []
        ocr_embeddings = generate_embeddings(ocr_text) or []

        embeddings = caption_embeddings + ocr_embeddings
        if not embeddings:
            logging.error("No embeddings generated for image")

        logging.info("Embeddings generated for image")

        metadata = MediaMetadata(
            media_id=media_id, caption=caption, ocr_text=ocr_text, embeddings=embeddings
        )
        logging.info("Metadata generated for image: %s", metadata)

        db.add(metadata)
        db.commit()
    except Exception as e:
        logging.error("Error processing image: %s", e)
