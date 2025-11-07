# Unified Text + Image Generator (Prototype)

A small prototype that accepts a single prompt and returns both generated text and an image. It uses a FastAPI backend that orchestrates text and image generators and a Streamlit frontend for a quick interactive UI.

This repo is intentionally prototype-level: it's great for experimentation and demos but not production-ready as-is.

Key features
- FastAPI backend with endpoints for health, feature discovery, and generation (text + image).
- Streamlit frontend for entering prompts and viewing combined outputs.
- Local-first image generation using Hugging Face Diffusers + PyTorch (optional; can operate in text-only mode).
- Optional S3 upload of generated images with presigned URLs.
- Unit tests and a CI workflow for basic validation.

Contents
- `src/backend/` - FastAPI app, generation helpers, S3 utilities.
- `src/frontend/` - Streamlit app.
- `tests/` - pytest tests that mock heavy dependencies.
- `Dockerfile` - example backend image (CPU-based).
- `.github/workflows/ci.yml` - basic CI to run tests.

Quick start (Windows PowerShell)

1. Copy environment template and update values as needed:

   copy .env.example .env

2. Create and activate a virtual environment, then install the Python dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1; pip install -r requirements.txt
```

3. Start the FastAPI backend (in one terminal):

```powershell
.\.venv\Scripts\Activate.ps1; uvicorn src.backend.main:app --host 0.0.0.0 --port 8000
```

4. Start the Streamlit frontend (in another terminal):

```powershell
.\.venv\Scripts\Activate.ps1; streamlit run src/frontend/app.py
```

5. Open the Streamlit UI in your browser (Streamlit will print a local URL, typically `http://localhost:8501`). The frontend calls the backend `/features` endpoint to determine whether image generation is available.

Run tests

```powershell
.\.venv\Scripts\Activate.ps1; pytest -q
```

Environment variables
- Copy `.env.example` to `.env` and set at least the values you need.
- Common variables:
  - `S3_BUCKET` - (optional) S3 bucket to upload generated images.
  - `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION` - when using S3 uploads.
  - `BACKEND_HOST`, `BACKEND_PORT` - optional bind settings for the backend.
  - `HF_API_TOKEN` - optional Hugging Face token if you later enable remote API usage.

Local model notes and performance
- The repository uses local `diffusers` + PyTorch for image generation by default. Running image generation will download model weights (Stable Diffusion-style models are several GB). Expect:
  - A multi-GB initial download when the pipeline is first created.
  - Significantly faster generation on machines with an NVIDIA GPU and a CUDA-enabled PyTorch build.
  - Very slow or impractical generation on many CPU-only machines.

If you don't want to run local image models, you can still use text generation and/or configure a remote image service (Hugging Face Inference API, a paid hosted endpoint, or another hosted model service).

Docker
- The included `Dockerfile` is a simple example for building a CPU-based backend image. Building an image with large ML packages will produce a big image and may take a long time. For production or heavy use:
  - Use a GPU-enabled base image and install a CUDA-capable PyTorch.
  - Consider serving models from a dedicated model-hosting service (Hugging Face Inference Endpoints, Triton, or similar).

Example Docker commands (host must have Docker):

```powershell
docker build -t mmgen-backend:latest .
docker run -p 8000:8000 --env-file .env mmgen-backend:latest
```

CI
- A GitHub Actions workflow runs the unit tests on push/PR. The workflow is intentionally minimal: it checks formatting and executes unit tests that mock heavy ML and network operations.

S3 and uploads
- The backend can optionally upload generated images to S3 and return a presigned GET URL. To enable this, populate the AWS credentials in your `.env` (or configure via your environment/EC2 role) and set `S3_BUCKET`.
- The S3 upload helpers live in `src/backend/s3_utils.py` and generate object keys automatically when requested.

Troubleshooting & tips
- If the frontend says "image generation not available":
  - Ensure `diffusers` and `torch` are installed in the environment used to run the backend.
  - Start the backend after installing required packages so startup checks can detect image capability.
- If image generation is extremely slow on CPU, consider running only text generation locally and using a hosted image API.
- If you hit package version conflicts (common with `diffusers`, `transformers`,), prefer pinned versions from the project's `requirements.txt` or create a fresh venv and install the provided `requirements.txt`.




Contributing
- This is a prototype; contributions that improve reliability, add CI checks, or make deployments reproducible are welcome. Please open issues or PRs.

Licensing
- Check the repository root for a license file. Model weights pulled from Hugging Face or other hubs are subject to their own licenses and terms.

Where to look in the code
- `src/backend/main.py` - FastAPI app and endpoints (`/health`, `/features`, `/generate`).
- `src/backend/generator.py` - text & image generation helpers.
- `src/backend/s3_utils.py` - S3 upload helpers.
- `src/frontend/app.py` - Streamlit UI.



