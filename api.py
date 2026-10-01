import csv
import json
import os
import threading
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from PIL import UnidentifiedImageError

from agent import PROMPT, analyze_image, list_images, process_folder

PROJECT_DIR = Path(__file__).parent

# Folder with the images to process in a batch, and where batch results are saved
DATA_DIR = Path(os.environ.get("BVG_DATA_DIR", PROJECT_DIR / "data"))
RESULTS_DIR = Path(os.environ.get("BVG_RESULTS_DIR", PROJECT_DIR / "results"))

app = FastAPI(title="BVG Image classifier API")

# Batch jobs in memory, by job id. Results are also saved to RESULTS_DIR.
jobs: dict[str, dict] = {}
jobs_lock = threading.Lock()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/prompt")
def default_prompt():
    return {"prompt": PROMPT}


@app.post("/analyze")
def analyze(file: UploadFile = File(...), prompt: str | None = Form(None)):
    image_bytes = file.file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        return analyze_image(image_bytes, file.filename or "unknown", prompt)
    except UnidentifiedImageError:
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid image.")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Model request failed: {e}")


# ============================================================
# BATCH: PROCESS THE DATA FOLDER
# ============================================================

def write_results_csv(results: list[dict], csv_path: str | Path):
    """Write all batch results to one CSV file: one row per image, one column per JSON key.

    Columns are file_name and status, then every key the model returned (in the order first seen),
    then error and raw_output. raw_output is only filled when the model did not return valid JSON.
    """
    result_keys: list[str] = []
    for item in results:
        if isinstance(item["result"], dict):
            for key in item["result"]:
                # The batch's own file_name (path inside the data folder) is used instead of the model's
                if key != "file_name" and key not in result_keys:
                    result_keys.append(key)

    columns = ["file_name", "status", *result_keys, "error", "raw_output"]
    rows = []
    for item in results:
        result = item["result"] if isinstance(item["result"], dict) else {}
        row = {"file_name": item["file_name"], "status": item["status"], "error": item["error"] or ""}
        for key in result_keys:
            value = result.get(key, "")
            row[key] = json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else value
        row["raw_output"] = item["raw_output"] if item["result"] is None and item["raw_output"] else ""
        rows.append(row)

    # utf-8-sig so Excel shows umlauts (ä, ö, ü, ß) correctly
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def save_job(job: dict):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(job["results_file"], "w", encoding="utf-8") as f:
        json.dump(job, f, indent=2, ensure_ascii=False)
    write_results_csv(job["results"], job["csv_file"])


def run_batch(job_id: str, prompt: str | None):
    job = jobs[job_id]
    try:
        for item in process_folder(DATA_DIR, prompt):
            with jobs_lock:
                job["results"].append(item)
                job["processed"] += 1
                if item["status"] == "error":
                    job["failed"] += 1
                save_job(job)
        status, error = "done", None
    except Exception as e:
        status, error = "failed", str(e)
    with jobs_lock:
        job["status"] = status
        job["error"] = error
        job["finished_at"] = datetime.now().isoformat(timespec="seconds")
        save_job(job)


@app.post("/batch")
def start_batch(background_tasks: BackgroundTasks, prompt: str | None = Form(None)):
    """Start processing every image in the data folder, one by one, in the background."""
    with jobs_lock:
        if any(job["status"] == "running" for job in jobs.values()):
            raise HTTPException(status_code=409, detail="A batch is already running. Wait for it to finish.")

        if not DATA_DIR.is_dir():
            raise HTTPException(status_code=404, detail=f"Data folder not found: {DATA_DIR}")
        images = list_images(DATA_DIR)
        if not images:
            raise HTTPException(status_code=400, detail=f"No images found in {DATA_DIR}")

        started_at = datetime.now()
        job_id = uuid.uuid4().hex[:8]
        jobs[job_id] = {
            "job_id": job_id,
            "status": "running",
            "data_dir": str(DATA_DIR),
            "total": len(images),
            "processed": 0,
            "failed": 0,
            "started_at": started_at.isoformat(timespec="seconds"),
            "finished_at": None,
            "error": None,
            "results_file": str(RESULTS_DIR / f"batch_{started_at:%Y%m%d_%H%M%S}_{job_id}.json"),
            "csv_file": str(RESULTS_DIR / f"batch_{started_at:%Y%m%d_%H%M%S}_{job_id}.csv"),
            "results": [],
        }

    background_tasks.add_task(run_batch, job_id, prompt)
    return {key: value for key, value in jobs[job_id].items() if key != "results"}


@app.get("/batch")
def list_batches():
    """All batch jobs since the API started, newest first, without their results."""
    with jobs_lock:
        return [
            {key: value for key, value in job.items() if key != "results"}
            for job in reversed(list(jobs.values()))
        ]


@app.get("/batch/{job_id}")
def get_batch(job_id: str):
    """Progress of one batch job, with the results finished so far."""
    with jobs_lock:
        if job_id not in jobs:
            raise HTTPException(status_code=404, detail=f"No batch job with id {job_id}")
        job = jobs[job_id]
        return {**job, "results": list(job["results"])}


# ============================================================
# RESULTS: CSV FILES IN THE RESULTS FOLDER
# ============================================================

@app.get("/results")
def list_result_csvs():
    """All CSV files in the results folder, newest first."""
    if not RESULTS_DIR.is_dir():
        return []
    files = sorted(RESULTS_DIR.glob("*.csv"), key=lambda path: path.stat().st_mtime, reverse=True)
    return [
        {
            "name": path.name,
            "size": path.stat().st_size,
            "modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds"),
        }
        for path in files
    ]


@app.get("/results/{name}")
def get_result_csv(name: str):
    """Download one CSV file from the results folder."""
    path = RESULTS_DIR / name
    # Only plain file names of CSVs inside the results folder, so no other files can be read
    if Path(name).name != name or path.suffix != ".csv" or not path.is_file():
        raise HTTPException(status_code=404, detail=f"No CSV file named {name} in the results folder")
    return FileResponse(path, media_type="text/csv", filename=name)
