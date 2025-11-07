import streamlit as st
import requests
import base64
import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Unified Text+Image Generator")
st.title("Unified Text + Image Generator")

# Default/example prompts users can pick from
DEFAULT_PROMPTS = {
    "Cozy fantasy tavern (art)": "A cozy fantasy tavern at sunset, warm lighting, detailed digital painting",
    "Friendly robot assistant (illustration)": "A friendly robot assistant explaining AI to children, colorful children's book illustration",
    "Product description (marketing)": "Write a concise, persuasive product description for a solar-powered backpack that charges devices on the go.",
    "Professional meeting request (email)": "Write a short professional email requesting a 30-minute meeting next week to discuss project milestones.",
    "Surreal landscape (art)": "A surreal landscape with floating islands and neon waterfalls, ultra-detailed, cinematic lighting"
}

example_key = st.selectbox("Or choose an example prompt", ["Custom"] + list(DEFAULT_PROMPTS.keys()))
if example_key != "Custom":
    default_text = DEFAULT_PROMPTS[example_key]
else:
    default_text = ""

prompt = st.text_area("Enter prompt", value=default_text, height=150)

# Fetch backend features (text/image availability)
def fetch_features():
    try:
        resp = requests.get(f"{BACKEND_URL}/features", timeout=3)
        if resp.status_code == 200:
            j = resp.json()
            return j.get("text", True), j.get("image", False)
    except Exception:
        pass
    # Default: text available, image not
    return True, False

text_avail, image_avail = fetch_features()

col1, col2 = st.columns([2,1])
with col2:
    if image_avail:
        prefer_local = st.checkbox("Prefer local image generation", value=False)
        save_to_s3 = st.checkbox("Store image to S3", value=False)
    else:
        prefer_local = False
        save_to_s3 = False
        st.info("Image generation unavailable on the backend (local models not installed).")
    max_length = st.slider("Max text length", min_value=32, max_value=1024, value=150)

if st.button("Generate"):
    if not prompt.strip():
        st.warning("Please enter a prompt")
    else:
        payload = {
            "prompt": prompt,
            "text_max_length": max_length,
            "prefer_local_image": prefer_local,
            "save_to_s3": save_to_s3
        }
        with st.spinner("Generating — this may take a while"):
            resp = requests.post(f"{BACKEND_URL}/generate", json=payload, timeout=600)
        if resp.status_code != 200:
            st.error(f"Error from backend: {resp.status_code} {resp.text}")
        else:
            data = resp.json()
            st.subheader("Generated text")
            st.write(data.get("text"))

            st.subheader("Generated image")
            s3url = data.get("image_s3_url")
            if s3url:
                st.markdown(f"**Image stored:** {s3url}")
            img_b64 = data.get("image_base64")
            if img_b64:
                img_bytes = base64.b64decode(img_b64)
                st.image(img_bytes, use_column_width=True)
            else:
                st.warning("No image returned")
