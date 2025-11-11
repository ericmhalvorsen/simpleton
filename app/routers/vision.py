"""Vision endpoints for image analysis and understanding"""

import httpx
import logging
import base64
from fastapi import APIRouter, HTTPException, status, UploadFile, File
from fastapi.responses import JSONResponse
from typing import Optional
from PIL import Image
from io import BytesIO

from app.auth import RequireAPIKey
from app.config import settings
from app.models import (
    VisionAnalyzeRequest,
    VisionAnalyzeResponse,
    VisionCaptionRequest,
    VisionCaptionResponse,
    VisionOCRRequest,
    VisionOCRResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/vision", tags=["vision"])


def process_image_input(image_data: str) -> str:
    """
    Process image input (base64 or URL) and return base64 encoded string

    Args:
        image_data: Base64 encoded image or image URL

    Returns:
        Base64 encoded image string
    """
    # If it's already base64 (starts with data:image), extract the data
    if image_data.startswith("data:image"):
        # Extract base64 part after comma
        return image_data.split(",")[1] if "," in image_data else image_data

    # If it's just base64 without data URI prefix
    if not image_data.startswith("http"):
        return image_data

    # If it's a URL, we would need to fetch it (not implemented for security)
    raise ValueError("Image URLs are not supported yet. Please use base64 encoded images.")


@router.post("/analyze", response_model=VisionAnalyzeResponse)
async def analyze_image(
    request: VisionAnalyzeRequest,
    api_key: RequireAPIKey,
):
    """
    Analyze an image with a custom prompt.

    This endpoint uses vision-capable models (like LLaVA) to understand
    and answer questions about images.

    **Use cases:**
    - Visual question answering
    - Object detection and description
    - Scene understanding
    - Image-based reasoning

    **Supported models:**
    - `llava` - General purpose vision model
    - `llava-phi3` - Efficient vision model
    - `bakllava` - Alternative vision model

    **Image format:**
    - Base64 encoded image: `data:image/png;base64,iVBORw0KG...`
    - Or just the base64 data without the prefix

    **Note:** Image URLs are not supported for security reasons.
    """
    model = request.model or settings.default_vision_model

    try:
        # Process image input
        image_b64 = process_image_input(request.image)

        # Build Ollama request payload
        payload = {
            "model": model,
            "prompt": request.prompt,
            "images": [image_b64],
            "stream": False,
        }

        # Add optional parameters
        options = {}
        if request.temperature is not None:
            options["temperature"] = request.temperature
        if request.max_tokens is not None:
            options["num_predict"] = request.max_tokens

        if options:
            payload["options"] = options

        # Call Ollama vision API
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{settings.ollama_base_url}/api/generate",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            return VisionAnalyzeResponse(
                model=model,
                response=data.get("response", ""),
                done=data.get("done", True),
                total_duration=data.get("total_duration"),
                eval_count=data.get("eval_count"),
            )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Ollama API error: {e.response.text}",
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Could not connect to Ollama: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Vision analysis error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )


@router.post("/caption", response_model=VisionCaptionResponse)
async def caption_image(
    request: VisionCaptionRequest,
    api_key: RequireAPIKey,
):
    """
    Generate a caption for an image.

    This endpoint automatically generates descriptive captions for images.

    **Detail levels:**
    - `brief` - Short, one-sentence caption
    - `normal` - Standard descriptive caption (default)
    - `detailed` - Comprehensive description with multiple details

    **Example captions:**
    - Brief: "A cat sitting on a windowsill"
    - Normal: "An orange tabby cat sitting on a white windowsill, looking outside"
    - Detailed: "An orange tabby cat with green eyes is sitting on a white painted wooden windowsill, gazing out at a sunny garden with flowers visible in the background"
    """
    model = request.model or settings.default_vision_model

    # Create prompt based on detail level
    prompts = {
        "brief": "Provide a brief one-sentence caption for this image.",
        "normal": "Describe this image in detail.",
        "detailed": "Provide a comprehensive and detailed description of this image, including all visible elements, colors, actions, and context."
    }

    prompt = prompts.get(request.detail_level, prompts["normal"])

    try:
        # Process image input
        image_b64 = process_image_input(request.image)

        # Build Ollama request payload
        payload = {
            "model": model,
            "prompt": prompt,
            "images": [image_b64],
            "stream": False,
        }

        # Call Ollama vision API
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{settings.ollama_base_url}/api/generate",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            return VisionCaptionResponse(
                caption=data.get("response", "").strip(),
                model=model,
            )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Ollama API error: {e.response.text}",
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Could not connect to Ollama: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Vision caption error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )


@router.post("/ocr", response_model=VisionOCRResponse)
async def extract_text(
    request: VisionOCRRequest,
    api_key: RequireAPIKey,
):
    """
    Extract text from an image using OCR.

    This endpoint uses vision models to read and extract text from images,
    similar to traditional OCR but powered by multimodal LLMs.

    **Use cases:**
    - Extract text from screenshots
    - Read text from photos of documents
    - Parse text from signs, labels, or displays
    - Convert image-based text to machine-readable format

    **Note:** Accuracy depends on image quality and text clarity.
    For best results, use high-resolution images with clear text.
    """
    model = request.model or settings.default_vision_model

    prompt = "Extract all text visible in this image. Provide only the text content without any additional commentary or description."

    try:
        # Process image input
        image_b64 = process_image_input(request.image)

        # Build Ollama request payload
        payload = {
            "model": model,
            "prompt": prompt,
            "images": [image_b64],
            "stream": False,
        }

        # Call Ollama vision API
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{settings.ollama_base_url}/api/generate",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            return VisionOCRResponse(
                text=data.get("response", "").strip(),
                model=model,
            )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Ollama API error: {e.response.text}",
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Could not connect to Ollama: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Vision OCR error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )


@router.post("/upload")
async def upload_image_for_analysis(
    file: UploadFile = File(...),
    prompt: str = "Describe this image",
    model: Optional[str] = None,
    api_key: RequireAPIKey = None,
):
    """
    Upload an image file and analyze it.

    This is a convenience endpoint that accepts direct file uploads
    instead of base64 encoded images.

    **Supported formats:** PNG, JPEG, GIF, WebP, BMP

    **Example usage with cURL:**
    ```bash
    curl -X POST http://localhost:8000/vision/upload \\
      -H "X-API-Key: your-key" \\
      -F "file=@image.jpg" \\
      -F "prompt=What is in this image?" \\
      -F "model=llava"
    ```
    """
    try:
        # Read uploaded file
        content = await file.read()

        # Verify it's a valid image
        try:
            image = Image.open(BytesIO(content))
            image.verify()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid image file: {str(e)}"
            )

        # Convert to base64
        image_b64 = base64.b64encode(content).decode('utf-8')

        # Create analyze request
        analyze_request = VisionAnalyzeRequest(
            image=image_b64,
            prompt=prompt,
            model=model
        )

        # Use the analyze endpoint
        return await analyze_image(analyze_request, api_key)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process uploaded file: {str(e)}"
        )
