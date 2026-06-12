from fastapi import APIRouter, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
import shutil
import uuid
import os
from services.upscale_service import upscale_image

router = APIRouter()


@router.post("/upscale")
async def upscale(file: UploadFile = File(...)):
    input_path = f"temp_{uuid.uuid4().hex}.png"

    print("FILE RECEIVED:", file.filename)
    print("INPUT PATH:", input_path)

    try:
        # Save uploaded file
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Process image
        output_path = upscale_image(input_path)

        # Validate output
        if not os.path.exists(output_path):
            raise Exception("Output file missing")

        if os.path.getsize(output_path) < 1000:
            raise Exception("Output file too small (failed generation)")

        return FileResponse(output_path, media_type="image/png")

    except Exception as e:
        print("ERROR:", str(e))
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

    finally:
        if os.path.exists(input_path):
            os.remove(input_path)