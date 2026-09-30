# BVG Image Classifier

A small tool that reads scanned BVG plans (building plans, tunnel drawings, technical drawings, and so on) and tells you what each one is about. For every image it pulls out the **title**, the **location**, and a short summary of the **main content**, and it sorts the plan into one of four **categories**:

1. Stations & building plans
2. Tunnel & railway infrastructure
3. Structural & construction details
4. Technical systems & installations

The actual "reading" is done by a vision language model (`qwen3.8-27b`) hosted on the HTW Berlin server.

---

## How it works

The system has three parts, and each one only talks to the next:

```
 ┌──────────────┐     HTTP      ┌──────────────┐    function    ┌──────────────┐    HTTPS    ┌────────────────┐
 │  bvg_app.py  │ ────────────▶ │    api.py    │ ─────────────▶ │   agent.py   │ ──────────▶ │  HTW AI model  │
 │  (web page)  │ ◀──────────── │  (backend)   │ ◀───────────── │ (talks to AI)│ ◀────────── │  (qwen3.8-27b) │
 └──────────────┘               └──────────────┘                └──────────────┘             └────────────────┘
```

### 1. `agent.py`: the part that talks to the AI

This is the core of the system.

- It holds the **prompt**, the instruction text sent to the model with each image. The prompt asks the model to find the title, location and main content, pick one of the four categories, and reply **only in JSON**.
- `analyze_image()` takes an image, converts it to PNG (the model can't read TIFF files, which is what most scans are), encodes it, and sends it to the model together with the prompt.
- The model's answer is text. `parse_json()` turns it into structured data. Models often wrap JSON in ```` ```json ```` fences, so those are removed first. If the answer still isn't valid JSON, the result is `None` and the raw text is kept, so nothing is lost.
- `process_folder()` does the same for every image in a folder (including subfolders), one at a time. If one image fails, the error is recorded and the batch moves on.

### 2. `api.py`: the backend (FastAPI)

A small web server that makes the agent available over HTTP. The web page (or any other program) can use it.

| Endpoint | What it does |
|---|---|
| `GET /health` | Checks that the API is running. |
| `GET /prompt` | Returns the default prompt, so the web page can show it. |
| `POST /analyze` | Upload **one image** (plus an optional custom prompt) and get the result right away. |
| `POST /batch` | Start processing **every image in the `data/` folder** in the background. Returns a job id immediately. |
| `GET /batch` | Lists all batch jobs since the API started. |
| `GET /batch/{job_id}` | Shows a batch's progress (how many done, how many failed) and the results so far. |

How batches work:
- Only **one batch can run at a time**. Starting a second one returns an error (`409`).
- After **each** image, the results so far are saved to `results/`, as both:
  - a **JSON** file (everything, including errors and raw model output)
  - a **CSV** file (one row per image, one column per field; opens directly in Excel, umlauts included)
- So even if something crashes halfway, the finished images are already on disk.
- The job list is kept in memory, so restarting the API forgets running jobs. The files in `results/` stay.

### 3. `bvg_app.py`: the web page (Streamlit)

The user interface, styled in BVG colours. It doesn't talk to the AI itself. It only calls the API.

- **Step 1: Prompt.** Shows the default prompt, which you can edit. Your edited prompt is used for both modes. Writing `{file_name}` in the prompt inserts each image's file name.
- **Step 2: Choose a mode.**
  - **Single image:** upload an image, click *Analyze image*, and the result appears as a card (category badge, title, location, main content). You can view the raw JSON or download it.
  - **Whole data folder:** click *Process data folder*. The page checks the API every 3 seconds, shows a progress bar, and adds each result card as it finishes. At the end you can download all results as JSON.

---

## Project structure

```
bip_group3/
├── agent.py          # Talks to the AI model (prompt, image conversion, JSON parsing)
├── api.py            # FastAPI backend (single-image + batch endpoints)
├── bvg_app.py        # Streamlit web interface
├── requirements.txt
├── data/             # Put the images for batch processing here (not in git)
└── results/          # Batch results are written here (JSON + CSV)
```

Supported image formats: `.jpg`, `.jpeg`, `.png`, `.tif`, `.tiff`, `.bmp`, `.webp`. Hidden files and folders (starting with `.`) are skipped.

---

## Setup

**1. Create a virtual environment and install dependencies**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install fastapi uvicorn python-multipart streamlit pillow requests
```

**2. Set your HTW API key**

```bash
export HTW_API_KEY="your-key-here"
```

The API won't start without it.

**3. (Optional) Change folders or the API address**

| Variable | Default | Used by |
|---|---|---|
| `BVG_DATA_DIR` | `./data` | `api.py`: folder with images for batch mode |
| `BVG_RESULTS_DIR` | `./results` | `api.py`: where batch results are saved |
| `BVG_API_URL` | `http://localhost:8000` | `bvg_app.py`: address of the API |

---

## Running

Start the two parts in **two separate terminals** (both with the virtual environment activated).

**Terminal 1: the API**
```bash
uvicorn api:app --reload
```
API docs are available at http://localhost:8000/docs

**Terminal 2: the web page**
```bash
streamlit run bvg_app.py
```
The page opens in your browser (usually at http://localhost:8501).

### Using the API without the web page

```bash
# Analyze one image
curl -F "file=@test_bvg.jpg" http://localhost:8000/analyze

# Start a batch over the data folder
curl -X POST http://localhost:8000/batch

# Check its progress
curl http://localhost:8000/batch/<job_id>
```

---

## Example output

```json
{
  "file_name": "A_318_005.tif",
  "title": "U-Bhf. Alexanderplatz – Grundriss Bahnsteigebene",
  "location": "Berlin-Mitte, Alexanderplatz",
  "main_content": "Floor plan of the platform level showing stairways, exits and platform dimensions.",
  "category": "Stations & building plans"
}
```

If a field isn't on the plan, the model marks it as missing, and the web page shows it as *Not found*.

---

## Team: Group 2+1

- Jana Kusch: Team Leader
- Monika Mikulevic: Data Analyst
- Yuliya Chtcherbo: Data Analyst
- Dimitrios Kostiris: Prototype Developer
- Jan Rutkowski: Test and assessment
