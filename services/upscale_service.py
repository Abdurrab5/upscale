import os
import platform
import subprocess
import json
import shutil
from PIL import Image

# =========================
# BASE PATH
# =========================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

# =========================
# DETECT GPU / VULKAN
# =========================

def has_vulkan():
    try:
        result = subprocess.run(
            ["vulkaninfo"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return result.returncode == 0
    except:
        return False


# =========================
# ENGINE SELECTOR
# =========================

def get_exe():
    system = platform.system()

    gpu_path = os.path.join(
        BASE_DIR,
        "realesrgan",
        "gpu_vulkan",
        "realesrgan-ncnn-vulkan"
    )

    cpu_path = os.path.join(
        BASE_DIR,
        "realesrgan",
        "cpu",
        "realesrgan-ncnn-cpu"
    )

    if system == "Windows":
        return gpu_path + ".exe"

    # Linux / servers
    if os.path.exists(gpu_path) and has_vulkan():
        return gpu_path

    return cpu_path


EXE_PATH = get_exe()


# =========================
# PROGRESS
# =========================

def update_progress(job_id, percent, message):
    os.makedirs("progress", exist_ok=True)

    with open(f"progress/{job_id}.json", "w") as f:
        json.dump(
            {"percent": percent, "message": message},
            f
        )


# =========================
# IMAGE NORMALIZATION
# =========================

def normalize_image(path):
    ext = os.path.splitext(path)[1].lower()

    if ext in [".png", ".jpg", ".jpeg", ".webp"]:
        return path

    img = Image.open(path).convert("RGB")

    out = path + "_normalized.png"
    img.save(out, "PNG")

    return out


# =========================
# REAL ESRGAN RUNNER (OPTIMIZED)
# =========================

def run_realesrgan(input_path, output_path):

    if not os.path.exists(EXE_PATH):
        raise Exception(f"Engine not found: {EXE_PATH}")

    cmd = [
        EXE_PATH,
        "-i", input_path,
        "-o", output_path,
        "-n", "realesrgan-x4plus",
        "-s", "4",
        "-t", "256",          # tile size (IMPORTANT for large images)
        "-j", "4:4:4",        # threads optimization
    ]

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:
        raise Exception(result.stderr)

    return output_path


# =========================
# MULTI SCALE GENERATION
# =========================

def generate_multi_scale(x4_path, base):

    img = Image.open(x4_path)
    w, h = img.size

    out_2x = base + "_2x.png"
    out_4x = base + "_4x.png"
    out_8x = base + "_8x.png"

    img.resize((w // 2, h // 2), Image.LANCZOS).save(out_2x)
    img.save(out_4x)
    img.resize((w * 2, h * 2), Image.LANCZOS).save(out_8x)

    return {
        "2x": out_2x,
        "4x": out_4x,
        "8x": out_8x
    }


# =========================
# MAIN UPSCALE PIPELINE
# =========================

def upscale_image(input_path, scale, job_id):

    update_progress(job_id, 5, "Starting")

    input_path = normalize_image(input_path)

    update_progress(job_id, 20, "Processing image")

    name, _ = os.path.splitext(input_path)
    x4_output = f"{name}_x4.png"

    run_realesrgan(input_path, x4_output)

    update_progress(job_id, 70, "Generating scales")

    outputs = generate_multi_scale(x4_output, name)

    selected = outputs.get(f"{scale}x", outputs["4x"])

    update_progress(job_id, 100, "Done")

    return selected