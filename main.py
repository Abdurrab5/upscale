from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import upscale

app = FastAPI(title="Upscale API", version="1.0")

# ✅ ADD THIS CORS CONFIG
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upscale.router)

@app.get("/")
def root():
    return {"status": "Upscale API running"}