from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
import shutil
import uuid
import os
import traceback
import json
from fastapi.responses import Response
from services.upscale_service import upscale_image

router = APIRouter()

PROGRESS_DIR = "progress"
os.makedirs(PROGRESS_DIR, exist_ok=True)
def update_progress(job_id, percent, message):

    with open(
    os.path.join(PROGRESS_DIR, f"{job_id}.json"),
    "w"
    )as f:

        json.dump({
            "percent": percent,
            "message": message
        }, f)

@router.get("/progress/{job_id}")

def progress(job_id: str):

    path = os.path.join(
    PROGRESS_DIR,
    f"{job_id}.json"
    )

    if not os.path.exists(path):
        return {
            "percent": 0,
            "message": "Waiting"
        }

    with open(path, "r") as f:
        return json.load(f)
@router.post("/upscale")
async def upscale(
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

        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        update_progress(job_id, 10, "Image received")

        output_path = upscale_image(input_path, scale, job_id)

        update_progress(job_id, 100, "Completed")

        # 🔥 FIX: convert to absolute path
        abs_output_path = os.path.abspath(output_path)

        if not os.path.exists(abs_output_path):
            return JSONResponse(
                status_code=500,
                content={"error": "Output file not found", "path": abs_output_path}
            )

        

        with open(abs_output_path, "rb") as f:
            image_bytes = f.read()

            return Response(
             content=image_bytes,
             media_type="image/png"
                )

    except Exception as e:
        traceback.print_exc()

        update_progress(job_id, 0, f"Error: {str(e)}")

        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

    finally:
        if os.path.exists(input_path):
            os.remove(input_path)