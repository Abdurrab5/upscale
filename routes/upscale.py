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


def update_progress(job_id, percent, message):

    with open(f"{PROGRESS_DIR}/{job_id}.json", "w") as f:
        json.dump(
            {
                "percent": percent,
                "message": message
            },
            f
        )


def clean_files(*paths):

    for path in paths:

        if path and os.path.exists(path):
            try:
                os.remove(path)
            except:
                pass


@router.get("/progress/{job_id}")
def progress(job_id: str):

    path = f"{PROGRESS_DIR}/{job_id}.json"

    if not os.path.exists(path):
        return {
            "percent": 0,
            "message": "Waiting"
        }

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

        update_progress(
            job_id,
            5,
            "Uploading image"
        )

        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(
                file.file,
                buffer
            )

        update_progress(
            job_id,
            15,
            "Processing started"
        )

        output_path = upscale_image(
            input_path,
            scale,
            job_id
        )

        if not os.path.exists(output_path):
            raise Exception(
                f"Output not found: {output_path}"
            )

        with open(output_path, "rb") as f:
            image_bytes = f.read()

        background_tasks.add_task(
            clean_files,
            input_path,
            output_path
        )

        mime = "image/png"

        return Response(
            content=image_bytes,
            media_type=mime
        )

    except Exception as e:

        update_progress(
            job_id,
            0,
            str(e)
        )

        return JSONResponse(
            status_code=500,
            content={
                "error": str(e)
            }
        )