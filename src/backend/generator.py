import os
import io
import base64
from typing import Optional
import logging
from dotenv import load_dotenv

from PIL import Image

# Suppress the HF symlink warning if desired (Windows users can set this in env instead)
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", os.getenv("HF_HUB_DISABLE_SYMLINKS_WARNING", "1"))

# Load environment variables from .env so HF_API_TOKEN and other vars are available
load_dotenv()

# Optional heavy imports guarded to allow fallback
try:
    from transformers import pipeline
    HF_TRANSFORMERS_AVAILABLE = True
except Exception:
    HF_TRANSFORMERS_AVAILABLE = False

# For image generation
try:
    from diffusers import StableDiffusionPipeline
    import torch
    DIFFUSERS_AVAILABLE = True
except Exception:
    DIFFUSERS_AVAILABLE = False

# We're using local models only (no HF remote inference)

# Cache the text generation pipeline to avoid reloading on every request
_TEXT_PIPE = None

def _get_text_pipeline():
    global _TEXT_PIPE
    if not HF_TRANSFORMERS_AVAILABLE:
        return None
    if _TEXT_PIPE is None:
        # Create pipeline once
        _TEXT_PIPE = pipeline("text-generation", model=os.getenv("TEXT_MODEL", "gpt2"))
        # Ensure pad token exists to silence padding warnings
        try:
            if getattr(_TEXT_PIPE.tokenizer, "pad_token", None) is None:
                _TEXT_PIPE.tokenizer.pad_token = _TEXT_PIPE.tokenizer.eos_token
        except Exception:
            logging.exception("Failed to set pad_token on tokenizer")
    return _TEXT_PIPE


def generate_text(prompt: str, max_length: int = 150) -> str:
    """Generate text using local transformers pipeline if available, otherwise return a simple echo.

    Uses a cached pipeline and passes truncation=True to avoid tokenizer warnings.
    """
    if HF_TRANSFORMERS_AVAILABLE:
        try:
            gen = _get_text_pipeline()
            if gen is None:
                raise RuntimeError("transformers pipeline unavailable")
            out = gen(prompt, max_length=max_length, do_sample=True, num_return_sequences=1, truncation=True)
            return out[0].get("generated_text", "")
        except Exception as e:
            logging.exception("Local text generation failed")
            return f"[text generation failed locally: {e}] {prompt}"
    # Fallback
    return prompt + "\n\n[Text-generation fallback — set up transformers or HF_API_TOKEN]"


def generate_image_local(prompt: str, height: int = 512, width: int = 512, num_inference_steps: int = 20) -> Image.Image:
    """Attempt to generate an image locally using diffusers if available."""
    if not DIFFUSERS_AVAILABLE:
        raise RuntimeError("diffusers or torch not available for local image generation")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model_id = os.getenv("IMAGE_MODEL", "runwayml/stable-diffusion-v1-5")
    pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float16 if device=="cuda" else torch.float32)
    pipe = pipe.to(device)
    image = pipe(prompt, height=height, width=width, num_inference_steps=num_inference_steps).images[0]
    return image


# (No remote HF inference) - image generation uses local diffusers only


def image_to_base64(img: Image.Image, fmt: str = "PNG") -> str:
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return b64


def generate_image(prompt: str, prefer_local: bool = False) -> dict:
    """Generate an image and return a dict with either 'image_base64' or raise an error.

    Strategy:
    - If prefer_local and diffusers available -> local
    - Else if HF_API_TOKEN available -> call HF Inference API
    - Else if diffusers available -> local
    - Else raise
    """
    # try local if requested and available
    if prefer_local and DIFFUSERS_AVAILABLE:
        img = generate_image_local(prompt)
        return {"image_base64": image_to_base64(img)}

    # Use local diffusers if available
    if DIFFUSERS_AVAILABLE:
        img = generate_image_local(prompt)
        return {"image_base64": image_to_base64(img)}

    raise RuntimeError("No image generation method available; install diffusers or set HF_API_TOKEN")
