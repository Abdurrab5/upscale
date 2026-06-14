import os
import subprocess
import json
from PIL import Image


# ----------------------------
# Progress updater
# ----------------------------
def update_progress(job_id, percent, message):
    os.makedirs("progress", exist_ok=True)

    with open(f"progress/{job_id}.json", "w") as f:
        json.dump({
            "percent": percent,
            "message": message
        }, f)


# ----------------------------
# Normalize image (ensures compatibility)
# ----------------------------
def normalize_image(input_path):
    img = Image.open(input_path).convert("RGB")

    normalized_path = input_path + "_normalized.png"
    img.save(normalized_path, "PNG")

    return normalized_path


# ----------------------------
# Real-ESRGAN single run
# ----------------------------
def run_realesrgan(exe_path, input_path, output_path, scale):
    command = [
        exe_path,
        "-i", input_path,
        "-o", output_path,
        "-s", str(scale),
        "-n", "realesrgan-x4plus"
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise Exception(
            f"RealESRGAN failed\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )

    return output_path


# ----------------------------
# 8x pipeline (2x + 4x or 4x + 2x)
# ----------------------------
def upscale_8x(exe_path, img_path):
    # step 1: 4x
    mid = img_path + "_4x.png"
    run_realesrgan(exe_path, img_path, mid, 4)

    # step 2: 2x on result = 8x total
    final = img_path + "_8x.png"
    run_realesrgan(exe_path, mid, final, 2)

    return final


# ----------------------------
# Main service
# ----------------------------
def upscale_image(input_path, scale, job_id):
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    exe_path = os.path.join(
        BASE_DIR,
        "realesrgan",
        "realesrgan-ncnn-vulkan.exe"
    )

    if not os.path.exists(exe_path):
        raise Exception("Real-ESRGAN executable not found")

    update_progress(job_id, 10, "Normalizing image")

    input_path = normalize_image(input_path)

    update_progress(job_id, 30, "Running AI upscale")

    name, _ = os.path.splitext(input_path)

    # ----------------------------
    # 2x / 4x direct
    # ----------------------------
    if scale in [2, 4]:
        output_path = f"{name}_{scale}x.png"
        run_realesrgan(exe_path, input_path, output_path, scale)

    # ----------------------------
    # 8x pipeline
    # ----------------------------
    elif scale == 8:
        update_progress(job_id, 50, "Running 4x stage")
        output_path = upscale_8x(exe_path, input_path)

    else:
        raise Exception("Unsupported scale. Use 2, 4, or 8")

    update_progress(job_id, 90, "Finalizing output")

    if not os.path.exists(output_path):
        raise Exception(f"Output not created: {output_path}")

    update_progress(job_id, 100, "Completed")

    return output_path