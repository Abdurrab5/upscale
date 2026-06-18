from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import upscale
import subprocess
from services.upscale_service import EXE_PATH
app = FastAPI(title="Upscale API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upscale.router)



@app.get("/test-esrgan")
def test_esrgan():
    result = subprocess.run(
        [EXE_PATH, "-h"],
        capture_output=True,
        text=True
    )

    return {
        "returncode": result.returncode,
        "stdout": result.stdout[:1000],
        "stderr": result.stderr[:1000]
    }
@app.get("/")
def root():
    return {"status": "Upscale API running"}