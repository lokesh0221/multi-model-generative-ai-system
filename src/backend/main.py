import os
import base64
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from .generator import generate_text, generate_image, DIFFUSERS_AVAILABLE
from .s3_utils import upload_bytes, make_key

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Unified Text+Image Generator")

# Startup note about local capabilities
USE_IMG = "available" if DIFFUSERS_AVAILABLE else "unavailable (install diffusers/torch)"
logger.info(f"Starting backend. Local image generation: {USE_IMG}")


class GenerateRequest(BaseModel):
    prompt: str
    text_max_length: int = 150
    prefer_local_image: bool = False
    save_to_s3: bool = False


class GenerateResponse(BaseModel):
    text: str
    image_base64: str | None = None
    image_s3_url: str | None = None


@app.get("/health")
async def health():
    return {"status": "ok"}


class FeaturesResponse(BaseModel):
    text: bool
    image: bool


@app.get("/features", response_model=FeaturesResponse)
async def features():
    """Return available generation features (text/image)."""
    return FeaturesResponse(text=True, image=bool(DIFFUSERS_AVAILABLE))


@app.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    prompt = req.prompt
    if not prompt or not prompt.strip():
        raise HTTPException(status_code=400, detail="prompt is required")

    # Generate text
    try:
        text = generate_text(prompt, max_length=req.text_max_length)
    except Exception as e:
        logger.exception("Text generation failed")
        raise HTTPException(status_code=500, detail=f"Text generation error: {e}")

    # Generate image (may raise)
    try:
        image_result = generate_image(prompt, prefer_local=req.prefer_local_image)
    except Exception as e:
        logger.exception("Image generation failed")
        raise HTTPException(status_code=500, detail=f"Image generation error: {e}")

    image_b64 = image_result.get("image_base64")
    image_s3_url = None

    if req.save_to_s3 and image_b64:
        # upload bytes to S3
        try:
            img_bytes = base64.b64decode(image_b64)
            key = make_key(prefix="generated")
            image_s3_url = upload_bytes(img_bytes, key)
        except Exception:
            logger.exception("S3 upload failed; returning inline image instead")
            image_s3_url = None

    return GenerateResponse(text=text, image_base64=image_b64, image_s3_url=image_s3_url)
