from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import Response, JSONResponse
import shutil
import uuid
import os
import json
from services.upscale_service import upscale_image

router = APIRouter()

PROGRESS_DIR = "progress"
os.makedirs(PROGRESS_DIR, exist_ok=True)


# ----------------------------
# Progress update
# ----------------------------
def update_progress(job_id, percent, message):
    with open(f"{PROGRESS_DIR}/{job_id}.json", "w") as f:
        json.dump({
            "percent": percent,
            "message": message
        }, f)


# ----------------------------
# Cleanup function
# ----------------------------
def clean_files(*paths):
    for path in paths:
        if path and os.path.exists(path):
            os.remove(path)

    # remove progress file
    job_id = paths[-1]
    progress_file = f"{PROGRESS_DIR}/{job_id}.json"
    if os.path.exists(progress_file):
        os.remove(progress_file)


# ----------------------------
# Progress endpoint
# ----------------------------
@router.get("/progress/{job_id}")
def progress(job_id: str):
    path = f"{PROGRESS_DIR}/{job_id}.json"

    if not os.path.exists(path):
        return {"percent": 0, "message": "Waiting"}

    with open(path, "r") as f:
        return json.load(f)
    
@router.post("/upscale")
async def upscale(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    scale: int = Form(4),
    job_id: str = Form(...)
):
    if scale not in [2, 4, 8]:
        scale = 4

    ext = os.path.splitext(file.filename)[1].lower()
    input_path = f"temp_{uuid.uuid4().hex}{ext}"

    try:
        update_progress(job_id, 5, "Uploading image")

        # save file
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        update_progress(job_id, 15, "Processing started")

        # run AI upscale
        output_path = upscale_image(input_path, scale, job_id)

        update_progress(job_id, 90, "Finalizing")

        abs_output_path = os.path.abspath(output_path)

        if not os.path.exists(abs_output_path):
            return JSONResponse(
                status_code=500,
                content={"error": "Output not found"}
            )

        # read result
        with open(abs_output_path, "rb") as f:
            image_bytes = f.read()

        # schedule cleanup AFTER response
        background_tasks.add_task(
            clean_files,
            input_path,
            output_path,
            job_id
        )

        return Response(
            content=image_bytes,
            media_type="image/png"
        )

    except Exception as e:
        update_progress(job_id, 0, f"Error: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})