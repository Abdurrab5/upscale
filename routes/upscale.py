from fastapi import APIRouter, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
import shutil
import uuid
import os
from services.upscale_service import upscale_image

router = APIRouter()


@router.post("/upscale")
async def upscale(file: UploadFile = File(...)):

    ext = os.path.splitext(file.filename)[1].lower()
    input_path = f"temp_{uuid.uuid4().hex}{ext}"

    output_path = None

    try:

        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        output_path = upscale_image(input_path)

        return FileResponse(
            output_path,
            media_type="image/png"
        )

    except Exception as e:

        print("ERROR:", str(e))

        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

    finally:

        if os.path.exists(input_path):
            os.remove(input_path)

        