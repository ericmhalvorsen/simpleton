"""Audio endpoints for transcription and translation"""

import base64
import logging
import tempfile
import os
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, status, UploadFile, File
from faster_whisper import WhisperModel

from app.auth import RequireAPIKey
from app.config import settings
from app.models import (
    AudioTranscribeRequest,
    AudioTranscribeResponse,
    AudioTranslateRequest,
    AudioTranslateResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/audio", tags=["audio"])

# Global Whisper model cache
_whisper_models = {}


def get_whisper_model(model_size: str = "base") -> WhisperModel:
    """
    Get or load Whisper model

    Args:
        model_size: Model size (tiny, base, small, medium, large)

    Returns:
        Whisper model instance
    """
    global _whisper_models

    if model_size not in _whisper_models:
        logger.info(f"Loading Whisper model: {model_size}")
        try:
            # Use CPU with INT8 quantization for efficiency
            # For GPU: device="cuda", compute_type="float16"
            _whisper_models[model_size] = WhisperModel(
                model_size,
                device="cpu",
                compute_type="int8",
                download_root=None,  # Use default cache directory
            )
            logger.info(f"Whisper model {model_size} loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model {model_size}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to load Whisper model: {str(e)}"
            )

    return _whisper_models[model_size]


def process_audio_input(audio_data: str) -> bytes:
    """
    Process audio input (base64) and return raw bytes

    Args:
        audio_data: Base64 encoded audio

    Returns:
        Audio bytes
    """
    # If it's a data URI, extract the base64 part
    if audio_data.startswith("data:audio"):
        # Extract base64 part after comma
        audio_data = audio_data.split(",")[1] if "," in audio_data else audio_data

    try:
        return base64.b64decode(audio_data)
    except Exception as e:
        raise ValueError(f"Invalid base64 audio data: {str(e)}")


@router.post("/transcribe", response_model=AudioTranscribeResponse)
async def transcribe_audio(
    request: AudioTranscribeRequest,
    api_key: RequireAPIKey,
):
    """
    Transcribe audio to text using Whisper.

    This endpoint uses OpenAI's Whisper model to convert speech to text.
    Supports multiple languages and can auto-detect the language.

    **Model sizes:**
    - `tiny` - Fastest, lowest accuracy (~1GB RAM)
    - `base` - Good balance of speed and accuracy (~1GB RAM, default)
    - `small` - Better accuracy, slower (~2GB RAM)
    - `medium` - High accuracy (~5GB RAM)
    - `large` - Best accuracy, slowest (~10GB RAM)

    **Supported audio formats:**
    - WAV, MP3, M4A, FLAC, OGG, OPUS
    - Automatically converted to required format

    **Language codes:**
    - `en` - English
    - `es` - Spanish
    - `fr` - French
    - `de` - German
    - `zh` - Chinese
    - And 90+ more languages
    - Leave empty for auto-detection

    **Use cases:**
    - Meeting transcription
    - Podcast processing
    - Voice notes to text
    - Subtitle generation
    - Voice command processing
    """
    model_size = request.model or settings.default_audio_model

    try:
        # Process audio input
        audio_bytes = process_audio_input(request.audio)

        # Save to temporary file (Whisper needs a file path)
        with tempfile.NamedTemporaryFile(suffix=".audio", delete=False) as temp_file:
            temp_file.write(audio_bytes)
            temp_path = temp_file.name

        try:
            # Get Whisper model
            model = get_whisper_model(model_size)

            # Transcribe
            logger.info(f"Transcribing audio with Whisper {model_size}")
            segments, info = model.transcribe(
                temp_path,
                language=request.language,
                task=request.task if request.task in ["transcribe", "translate"] else "transcribe",
                beam_size=5,
                vad_filter=True,  # Use voice activity detection
                vad_parameters=dict(min_silence_duration_ms=500),
            )

            # Collect all segments
            transcript_parts = []
            for segment in segments:
                transcript_parts.append(segment.text)

            transcript = " ".join(transcript_parts).strip()

            return AudioTranscribeResponse(
                text=transcript,
                language=info.language if hasattr(info, 'language') else request.language,
                duration=info.duration if hasattr(info, 'duration') else None,
                model=model_size,
            )

        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_path)
            except Exception as e:
                logger.warning(f"Failed to delete temp file: {e}")

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transcription failed: {str(e)}"
        )


@router.post("/translate", response_model=AudioTranslateResponse)
async def translate_audio(
    request: AudioTranslateRequest,
    api_key: RequireAPIKey,
):
    """
    Translate audio to English text using Whisper.

    This endpoint transcribes audio in any language and translates it to English.
    Uses Whisper's built-in translation capability.

    **Model sizes:**
    - `tiny` - Fastest (~1GB RAM)
    - `base` - Good balance (default)
    - `small` - Better quality (~2GB RAM)
    - `medium` - High quality (~5GB RAM)
    - `large` - Best quality (~10GB RAM)

    **Supported input languages:**
    - 90+ languages automatically detected
    - Audio in any language → English text

    **Use cases:**
    - International meeting transcripts
    - Foreign language content translation
    - Multilingual customer support
    - Global podcast translation
    """
    model_size = request.model or settings.default_audio_model

    try:
        # Process audio input
        audio_bytes = process_audio_input(request.audio)

        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix=".audio", delete=False) as temp_file:
            temp_file.write(audio_bytes)
            temp_path = temp_file.name

        try:
            # Get Whisper model
            model = get_whisper_model(model_size)

            # Transcribe with translation task
            logger.info(f"Translating audio to English with Whisper {model_size}")
            segments, info = model.transcribe(
                temp_path,
                task="translate",  # This translates to English
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500),
            )

            # Collect all segments
            translation_parts = []
            for segment in segments:
                translation_parts.append(segment.text)

            translation = " ".join(translation_parts).strip()

            return AudioTranslateResponse(
                text=translation,
                source_language=info.language if hasattr(info, 'language') else None,
                duration=info.duration if hasattr(info, 'duration') else None,
                model=model_size,
            )

        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_path)
            except Exception as e:
                logger.warning(f"Failed to delete temp file: {e}")

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Translation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Translation failed: {str(e)}"
        )


@router.post("/upload/transcribe")
async def upload_and_transcribe(
    file: UploadFile = File(...),
    language: Optional[str] = None,
    model: Optional[str] = None,
    api_key: RequireAPIKey = None,
):
    """
    Upload an audio file and transcribe it.

    This is a convenience endpoint that accepts direct file uploads
    instead of base64 encoded audio.

    **Supported formats:** WAV, MP3, M4A, FLAC, OGG, OPUS, WebM

    **Example usage with cURL:**
    ```bash
    curl -X POST http://localhost:8000/audio/upload/transcribe \\
      -H "X-API-Key: your-key" \\
      -F "file=@recording.mp3" \\
      -F "language=en" \\
      -F "model=base"
    ```
    """
    try:
        # Read uploaded file
        content = await file.read()

        # Convert to base64
        audio_b64 = base64.b64encode(content).decode('utf-8')

        # Create transcribe request
        transcribe_request = AudioTranscribeRequest(
            audio=audio_b64,
            language=language,
            model=model,
            task="transcribe"
        )

        # Use the transcribe endpoint
        return await transcribe_audio(transcribe_request, api_key)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process uploaded file: {str(e)}"
        )


@router.post("/upload/translate")
async def upload_and_translate(
    file: UploadFile = File(...),
    model: Optional[str] = None,
    api_key: RequireAPIKey = None,
):
    """
    Upload an audio file and translate it to English.

    This is a convenience endpoint that accepts direct file uploads
    instead of base64 encoded audio.

    **Supported formats:** WAV, MP3, M4A, FLAC, OGG, OPUS, WebM

    **Example usage with cURL:**
    ```bash
    curl -X POST http://localhost:8000/audio/upload/translate \\
      -H "X-API-Key: your-key" \\
      -F "file=@recording.mp3" \\
      -F "model=base"
    ```
    """
    try:
        # Read uploaded file
        content = await file.read()

        # Convert to base64
        audio_b64 = base64.b64encode(content).decode('utf-8')

        # Create translate request
        translate_request = AudioTranslateRequest(
            audio=audio_b64,
            model=model
        )

        # Use the translate endpoint
        return await translate_audio(translate_request, api_key)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process uploaded file: {str(e)}"
        )
