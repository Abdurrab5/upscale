import os
import platform
import subprocess
import json
from PIL import Image

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)


# =========================
# ENGINE SELECTOR
# =========================

def get_exe():
    system = platform.system()

    if system == "Windows":
        exe = os.path.join(
            BASE_DIR,
            "realesrgan",
            "realesrgan-ncnn-vulkan.exe"
        )
    else:
        exe = os.path.join(
            BASE_DIR,
            "realesrgan",
            "realesrgan-ncnn-vulkan"
        )

    if not os.path.isfile(exe):
        raise Exception(
            f"RealESRGAN binary not found.\n"
            f"Expected: {exe}\n"
            f"Platform: {system}"
        )

    # Linux/Railway needs executable permission
    if system != "Windows":
        os.chmod(exe, 0o755)

    return exe

EXE_PATH = get_exe()
# =========================
# PROGRESS
# =========================

def update_progress(job_id, percent, message):

    os.makedirs("progress", exist_ok=True)

    with open(f"progress/{job_id}.json", "w") as f:
        json.dump(
            {
                "percent": percent,
                "message": message
            },
            f
        )


# =========================
# NORMALIZE
# =========================

def normalize_image(path):

    ext = os.path.splitext(path)[1].lower()

    if ext in [".png", ".jpg", ".jpeg", ".webp"]:
        return path

    img = Image.open(path).convert("RGB")

    normalized = path + "_normalized.png"

    img.save(normalized, "PNG")

    return normalized


# =========================
# AUTO TILE SIZE
# =========================

def get_tile_size(image_path):

    img = Image.open(image_path)

    w, h = img.size

    pixels = w * h

    if pixels <= 2_000_000:
        return "128"

    if pixels <= 8_000_000:
        return "256"

    return "512"


# =========================
# REAL ESRGAN
# =========================

def run_realesrgan(input_path, output_path):

    tile_size = get_tile_size(input_path)

    cmd = [
        EXE_PATH,
        "-i", input_path,
        "-o", output_path,
        "-n", "realesrgan-x4plus",
        "-s", "4",
        "-t", tile_size,
        "-j", "4:4:4"
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise Exception(
            f"STDERR:\n{result.stderr}\n\nSTDOUT:\n{result.stdout}"
        )

    if not os.path.exists(output_path):
        raise Exception(
            f"Output not generated: {output_path}"
        )

    return output_path


# =========================
# MAIN
# =========================

def upscale_image(input_path, job_id):

    update_progress(job_id, 5, "Starting")

    normalized_input = normalize_image(input_path)

    update_progress(job_id, 20, "Upscaling image")

    name, _ = os.path.splitext(normalized_input)

    output_path = f"{name}_x4.png"

    run_realesrgan(
        normalized_input,
        output_path
    )

    update_progress(job_id, 100, "Completed")

    return {
        "output_path": output_path,
        "normalized_input": normalized_input
    }
