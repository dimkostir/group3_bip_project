import base64
import io
import json
import os
import re
from collections.abc import Iterator
from pathlib import Path
from openai import OpenAI
from PIL import Image

# ============================================================
# SETTINGS
# ============================================================

API_KEY = os.environ["HTW_API_KEY"]

BASE_URL = "https://f2ki-h100-1.f2.htw-berlin.de:11435/v1"

MODEL = "qwen3.8-27b"

# File types picked up when processing a whole folder
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp"}

PROMPT = (
    "This is a plan image. It may be handwritten or printed. "
    "There are 2 things for you to do: "
    "1.Extract the title, the location and the main content of the plan. "
    "Try to focus only in these specific information and ignore any other irrelevant details. "
    "If any of the requested information is not present, please indicate that it is missing. "
    "2. Try to classify the picture into one of the following categories: 1) Stations & building plans, 2) Tunnel & railway infrastructure, 3) Structural & construction details, 4) Technical systems & installations. "
    "Do not invent any categories. If it is difficult to classify, put it in the most appropriate category. "
    "Return only valid JSON with the keys: file_name, title, location, main_content, category. "
    "The category value must be exactly one of the four category names above, without the number." \
    "All your answers must be in English. (Except the title and location). Main content should be in english. "
)


# ============================================================
# CONNECT TO HTW API
# ============================================================

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)


# ============================================================
# HELPERS
# ============================================================

def to_png_base64(image_bytes: bytes) -> str:
    # TIFF and other formats are converted to PNG so the model can read them
    image = Image.open(io.BytesIO(image_bytes))
    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def parse_json(text: str):
    # Models often wrap JSON in ```json ... ``` fences
    match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if match:
        text = match.group(1)
    return json.loads(text.strip())


# ============================================================
# AGENT
# ============================================================

def analyze_image(image_bytes: bytes, file_name: str, prompt: str | None = None) -> dict:
    """Send the image to the model and return its parsed JSON plus the raw text.

    "result" is None when the model did not return valid JSON.
    A custom prompt replaces PROMPT; "{file_name}" in it is filled in.
    """
    prompt_text = (prompt or PROMPT).replace("{file_name}", file_name)

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_text},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{to_png_base64(image_bytes)}"},
                    },
                ],
            }
        ],
    )
    raw_output = response.choices[0].message.content

    try:
        result = parse_json(raw_output)
    except json.JSONDecodeError:
        result = None

    return {"file_name": file_name, "result": result, "raw_output": raw_output}


# ============================================================
# BATCH: PROCESS A WHOLE FOLDER
# ============================================================

def list_images(folder: Path) -> list[Path]:
    """All images in the folder and its subfolders, sorted by path. Hidden files are skipped."""
    return sorted(
        path for path in folder.rglob("*")
        if path.is_file()
        and path.suffix.lower() in IMAGE_EXTENSIONS
        and not any(part.startswith(".") for part in path.relative_to(folder).parts)
    )


def process_folder(folder: Path, prompt: str | None = None) -> Iterator[dict]:
    """Send every image in the folder to the model, one by one, yielding each result as it finishes.

    A failing image doesn't stop the batch: it is yielded with status "error".
    """
    for path in list_images(folder):
        file_name = str(path.relative_to(folder))
        try:
            output = analyze_image(path.read_bytes(), path.name, prompt)
        except Exception as e:
            yield {"file_name": file_name, "status": "error", "result": None, "raw_output": None, "error": str(e)}
        else:
            yield {**output, "file_name": file_name, "status": "ok", "error": None}
