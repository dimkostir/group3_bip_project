import html
import json
import os
import time

import requests
import streamlit as st
from PIL import Image

# ============================================================
# SETTINGS
# ============================================================

# Address of the FastAPI backend (api.py)
API_URL = os.environ.get("BVG_API_URL", "http://localhost:8000")

TEAM_NAME = "Group 2+1"
TEAM_MEMBERS = [
    "Jana Kusch: Team Leader",
    "Monika Mikulevic: Data Analyst",
    "Yuliya Chtcherbo: Data Analyst",
    "Dimitrios Kostiris: Prototype Developer",
    "Jan Rutkowski: Test and assessment",
]

# BVG colours
BVG_YELLOW = "#F0D722"
BVG_BLACK = "#1A1A1A"
BVG_GREY = "#3C3C3C"
BVG_LIGHT_GREY = "#E6E6E6"


# ============================================================
# PAGE SETUP & STYLE
# ============================================================

st.set_page_config(page_title="BVG Image classifier", page_icon="🟡", layout="centered")

st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {BVG_BLACK};
        color: {BVG_LIGHT_GREY};
    }}
    .bvg-header {{
        background-color: {BVG_YELLOW};
        color: {BVG_BLACK};
        padding: 1.4rem 1.6rem;
        border-radius: 6px;
        margin-bottom: 0.4rem;
    }}
    .bvg-header h1 {{
        color: {BVG_BLACK};
        margin: 0;
        padding: 0;
        font-weight: 800;
        letter-spacing: -0.5px;
    }}
    .bvg-team {{
        background-color: {BVG_GREY};
        color: {BVG_YELLOW};
        padding: 0.5rem 1.6rem;
        border-radius: 6px;
        font-weight: 700;
        margin-bottom: 1.5rem;
    }}
    .bvg-card {{
        background-color: #242424;
        border: 1px solid {BVG_GREY};
        border-top: 5px solid {BVG_YELLOW};
        border-radius: 8px;
        padding: 1.4rem 1.6rem 1.2rem;
        margin: 0.5rem 0 1rem;
    }}
    .bvg-card-top {{
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 0.9rem;
    }}
    .bvg-pill {{
        background-color: {BVG_YELLOW};
        color: {BVG_BLACK};
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        padding: 0.2rem 0.6rem;
        border-radius: 999px;
    }}
    .bvg-file {{
        color: #9A9A9A;
        font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
        font-size: 0.82rem;
        overflow-wrap: anywhere;
    }}
    .bvg-title {{
        color: #FFFFFF;
        font-size: 1.35rem;
        font-weight: 700;
        line-height: 1.35;
        margin: 0 0 1.2rem;
        overflow-wrap: anywhere;
    }}
    .bvg-meta {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 0.8rem;
        margin-bottom: 1.2rem;
    }}
    .bvg-meta-item {{
        background-color: {BVG_BLACK};
        border-left: 3px solid {BVG_YELLOW};
        border-radius: 4px;
        padding: 0.7rem 0.9rem;
    }}
    .bvg-label {{
        color: {BVG_YELLOW};
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin-bottom: 0.3rem;
    }}
    .bvg-value {{
        color: {BVG_LIGHT_GREY};
        font-size: 0.95rem;
        line-height: 1.5;
        overflow-wrap: anywhere;
    }}
    .bvg-missing {{
        color: #7A7A7A;
        font-style: italic;
    }}
    .bvg-section {{
        border-top: 1px solid {BVG_GREY};
        padding-top: 1rem;
        margin-top: 0.2rem;
    }}
    .bvg-body {{
        color: {BVG_LIGHT_GREY};
        font-size: 1rem;
        line-height: 1.7;
        white-space: pre-wrap;
        overflow-wrap: anywhere;
    }}
    [data-testid="stDownloadButton"] button {{
        background-color: transparent;
        color: {BVG_YELLOW};
        border: 1.5px solid {BVG_YELLOW};
        font-weight: 700;
    }}
    [data-testid="stDownloadButton"] button:hover {{
        background-color: {BVG_YELLOW};
        color: {BVG_BLACK};
    }}
    [data-testid="stExpander"] details {{
        border: 1px solid {BVG_GREY};
        border-radius: 8px;
    }}
    h2, h3 {{
        color: {BVG_YELLOW} !important;
    }}
    [data-testid="stFileUploader"] section {{
        background-color: {BVG_GREY};
        border: 2px dashed {BVG_YELLOW};
    }}
    [data-testid="stFileUploader"] label, .stMarkdown p {{
        color: {BVG_LIGHT_GREY};
    }}
    .stButton > button, [data-testid="stFormSubmitButton"] button {{
        background-color: {BVG_YELLOW};
        color: {BVG_BLACK};
        font-weight: 700;
        border: none;
        width: 100%;
    }}
    .stButton > button:hover, [data-testid="stFormSubmitButton"] button:hover {{
        background-color: {BVG_LIGHT_GREY};
        color: {BVG_BLACK};
    }}
    [data-testid="stForm"] {{
        border: 1px solid {BVG_GREY};
    }}
    .stTextArea label, .stTextArea label p {{
        color: {BVG_YELLOW} !important;
        font-weight: 700;
    }}
    .bvg-step {{
        color: {BVG_YELLOW};
        font-size: 0.78rem;
        font-weight: 800;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin: 1.4rem 0 0.4rem;
    }}
    .bvg-mode-info {{
        background-color: #242424;
        border-left: 4px solid {BVG_YELLOW};
        border-radius: 4px;
        padding: 0.8rem 1rem;
        margin: 0.4rem 0 1rem;
        color: {BVG_LIGHT_GREY};
        line-height: 1.5;
    }}
    .bvg-mode-info b {{
        color: #FFFFFF;
    }}
    [data-testid="stRadio"] [role="radiogroup"] {{
        gap: 0.6rem;
    }}
    [data-testid="stRadio"] [role="radiogroup"] > label {{
        background-color: {BVG_GREY};
        border: 1.5px solid {BVG_GREY};
        border-radius: 999px;
        padding: 0.45rem 1.1rem;
        margin: 0;
        cursor: pointer;
    }}
    [data-testid="stRadio"] [role="radiogroup"] > label:has(input:checked) {{
        background-color: {BVG_YELLOW};
        border-color: {BVG_YELLOW};
    }}
    [data-testid="stRadio"] [role="radiogroup"] > label:has(input:checked) p {{
        color: {BVG_BLACK} !important;
        font-weight: 800;
    }}
    [data-testid="stRadio"] [role="radiogroup"] > label > div:first-child {{
        display: none;
    }}
    [data-testid="stExpander"] summary p {{
        color: {BVG_YELLOW} !important;
        font-weight: 700;
    }}
    [data-testid="stSidebar"] {{
        background-color: {BVG_GREY};
    }}
    [data-testid="stSidebar"] * {{
        color: {BVG_LIGHT_GREY};
    }}
    [data-testid="stSidebar"] h2 {{
        color: {BVG_YELLOW} !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="bvg-header"><h1>BVG Image classifier</h1></div>', unsafe_allow_html=True)
st.markdown(f'<div class="bvg-team">{TEAM_NAME}</div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown(f"## {TEAM_NAME}")
    for member in TEAM_MEMBERS:
        st.markdown(f"- {member}")


# ============================================================
# API CALL
# ============================================================

@st.cache_data(ttl=60)
def get_default_prompt() -> str:
    try:
        response = requests.get(f"{API_URL}/prompt", timeout=5)
        response.raise_for_status()
        return response.json()["prompt"]
    except (requests.RequestException, ValueError, KeyError):
        return ""


def analyze_image(file_name: str, image_bytes: bytes, mime_type: str, prompt: str) -> dict:
    response = requests.post(
        f"{API_URL}/analyze",
        files={"file": (file_name, image_bytes, mime_type)},
        data={"prompt": prompt},
        timeout=300,
    )
    raise_for_api_error(response)
    return response.json()


def raise_for_api_error(response: requests.Response):
    if not response.ok:
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text
        raise RuntimeError(f"{response.status_code}: {detail}")


def start_batch(prompt: str) -> tuple[dict, bool]:
    """Start processing the API's data folder. Returns (job, already_running).

    If a batch is already running, that batch is returned instead of starting a new one.
    """
    response = requests.post(f"{API_URL}/batch", data={"prompt": prompt}, timeout=30)
    if response.status_code == 409:
        jobs = requests.get(f"{API_URL}/batch", timeout=10).json()
        running = next((job for job in jobs if job["status"] == "running"), None)
        if running is not None:
            return running, True
    raise_for_api_error(response)
    return response.json(), False


def get_batch(job_id: str) -> dict:
    response = requests.get(f"{API_URL}/batch/{job_id}", timeout=10)
    raise_for_api_error(response)
    return response.json()


# ============================================================
# RESULT VIEW
# ============================================================

MISSING_WORDS = {"", "missing", "n/a", "none", "not present", "unknown"}


def format_value(value) -> str:
    if value is None:
        text = ""
    elif isinstance(value, (list, dict)):
        text = json.dumps(value, indent=2, ensure_ascii=False)
    else:
        text = str(value)
    if text.strip().lower() in MISSING_WORDS:
        return '<span class="bvg-missing">Not found</span>'
    return html.escape(text)


def render_result(result: dict, file_name: str):
    fields = dict(result)
    shown_file = fields.pop("file_name", file_name)
    title = fields.pop("title", None)
    main_content = fields.pop("main_content", None)
    category = fields.pop("category", None)
    if category is None or str(category).strip().lower() in MISSING_WORDS:
        badge = "Uncategorized"
    else:
        badge = str(category)

    # Short fields (author, locationand anything extra the prompt asked for) go in the grid
    meta_items = "".join(
        f'<div class="bvg-meta-item"><div class="bvg-label">{html.escape(key.replace("_", " "))}</div>'
        f'<div class="bvg-value">{format_value(value)}</div></div>'
        for key, value in fields.items()
    )

    parts = [
        '<div class="bvg-card">',
        f'<div class="bvg-card-top"><span class="bvg-pill" title="Category">{html.escape(badge)}</span>'
        f'<span class="bvg-file">{html.escape(str(shown_file))}</span></div>',
    ]
    if title is not None:
        parts.append(f'<div class="bvg-label">Title</div><div class="bvg-title">{format_value(title)}</div>')
    if meta_items:
        parts.append(f'<div class="bvg-meta">{meta_items}</div>')
    if main_content is not None:
        parts.append(
            '<div class="bvg-section"><div class="bvg-label">Main content</div>'
            f'<div class="bvg-body">{format_value(main_content)}</div></div>'
        )
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)


def render_batch_item(item: dict):
    if item["status"] == "error":
        st.error(f"{item['file_name']}: {item['error']}")
    elif item["result"] is None:
        st.warning(f"{item['file_name']}: the model did not return valid JSON. Showing raw output.")
        st.code(item["raw_output"], language="text")
    elif isinstance(item["result"], dict):
        render_result(item["result"], item["file_name"])
    else:
        st.json(item["result"])


def show_batch(job_id: str):
    """Show a batch's progress and results, refreshing every few seconds until it finishes."""
    st.markdown("### Batch: data folder")
    status_box = st.empty()
    results_box = st.empty()
    shown = -1

    while True:
        try:
            job = get_batch(job_id)
        except requests.ConnectionError:
            status_box.error(f"Could not reach the API at {API_URL}. Is api.py running?")
            return
        except Exception as e:
            # For example the API was restarted, which clears its list of batches
            status_box.error(f"Could not load the batch: {e}")
            st.session_state.pop("batch_job_id", None)
            return

        total, processed, failed = job["total"], job["processed"], job["failed"]
        with status_box.container():
            st.progress(processed / total if total else 1.0)
            if job["status"] == "running":
                st.caption(f"Processing image {min(processed + 1, total)} of {total}... ({failed} failed so far)")
            elif job["status"] == "done":
                st.success(f"Done: {processed} of {total} images processed, {failed} failed.")
            else:
                st.error(f"Batch stopped: {job['error']}")
            st.caption(f"Results file: {job['results_file']}")

        if len(job["results"]) != shown:
            shown = len(job["results"])
            with results_box.container():
                for item in job["results"]:
                    render_batch_item(item)

        if job["status"] != "running":
            break
        time.sleep(3)

    st.download_button(
        "Download all results",
        data=json.dumps(job["results"], indent=2, ensure_ascii=False),
        file_name=f"batch_{job_id}_results.json",
        mime="application/json",
    )
    if st.button("Clear batch results"):
        st.session_state.pop("batch_job_id", None)
        st.rerun()


# ============================================================
# UPLOAD & RESULT
# ============================================================

SINGLE_MODE = "Single image"
FOLDER_MODE = "Whole data folder"

# Step 1: the prompt, shared by both modes
st.markdown('<div class="bvg-step">Step 1 · Prompt</div>', unsafe_allow_html=True)
with st.expander("Prompt for the agent (used by both options)", expanded=False):
    prompt = st.text_area(
        "Prompt",
        value=get_default_prompt(),
        height=220,
        label_visibility="collapsed",
        help="{file_name} is replaced with each image's file name.",
    )

# Step 2: choose what to process
st.markdown('<div class="bvg-step">Step 2 · What do you want to process?</div>', unsafe_allow_html=True)
mode = st.radio(
    "What do you want to process?",
    [SINGLE_MODE, FOLDER_MODE],
    horizontal=True,
    label_visibility="collapsed",
    key="mode",
)


def prompt_is_empty() -> bool:
    if not prompt.strip():
        st.warning("The prompt is empty. Open Step 1 and enter a prompt.")
        return True
    return False


# ------------------------------------------------------------
# Option 1: one uploaded image
# ------------------------------------------------------------

if mode == SINGLE_MODE:
    st.markdown(
        '<div class="bvg-mode-info"><b>Single image:</b> upload one image and analyze it. '
        "The result appears below.</div>",
        unsafe_allow_html=True,
    )
    uploaded_file = st.file_uploader(
        "Upload an image",
        type=["jpg", "jpeg", "png", "tif", "tiff", "bmp", "webp"],
    )
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption=uploaded_file.name, use_container_width=True)

    if st.button("Analyze image", disabled=uploaded_file is None, key="analyze_single"):
        if not prompt_is_empty():
            with st.spinner("Analyzing image..."):
                try:
                    data = analyze_image(
                        uploaded_file.name,
                        uploaded_file.getvalue(),
                        uploaded_file.type or "application/octet-stream",
                        prompt,
                    )
                except requests.ConnectionError:
                    st.error(f"Could not reach the API at {API_URL}. Is api.py running?")
                except Exception as e:
                    st.error(f"Request failed: {e}")
                else:
                    # Kept in session state so the result survives other clicks on the page
                    st.session_state["single_result"] = data

    data = st.session_state.get("single_result")
    if data is not None:
        st.markdown("### Result")
        result = data["result"]
        if result is None:
            st.warning("The model did not return valid JSON. Showing raw output.")
            st.code(data["raw_output"], language="text")
        else:
            if isinstance(result, dict):
                render_result(result, data["file_name"])
                with st.expander("Raw JSON"):
                    st.json(result)
            else:
                st.json(result)
            st.download_button(
                "Download JSON",
                data=json.dumps(result, indent=2, ensure_ascii=False),
                file_name=f"{data['file_name']}_result.json",
                mime="application/json",
            )


# ------------------------------------------------------------
# Option 2: every image in the data folder
# ------------------------------------------------------------

else:
    st.markdown(
        '<div class="bvg-mode-info"><b>Whole data folder:</b> the API processes every image in its '
        "<code>data</code> folder, one by one. Progress and results appear below as each image "
        "finishes, and everything is saved to a results file.</div>",
        unsafe_allow_html=True,
    )

    if st.button("Process data folder", key="start_batch"):
        if not prompt_is_empty():
            try:
                job, already_running = start_batch(prompt)
            except requests.ConnectionError:
                st.error(f"Could not reach the API at {API_URL}. Is api.py running?")
            except Exception as e:
                st.error(f"Could not start the batch: {e}")
            else:
                if already_running:
                    st.info("A batch is already running, so it wasn't started again. Showing the running batch.")
                st.session_state["batch_job_id"] = job["job_id"]

    # Kept in session state so the batch view survives other clicks and switching modes
    if st.session_state.get("batch_job_id"):
        show_batch(st.session_state["batch_job_id"])
