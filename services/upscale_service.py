import os
import subprocess
import json


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
# OPTIONAL: normalize ONLY if needed
# ----------------------------
def normalize_image(input_path):
    ext = os.path.splitext(input_path)[1].lower()

    # skip conversion if already safe format
    if ext in [".png", ".jpg", ".jpeg"]:
        return input_path

    from PIL import Image

    img = Image.open(input_path).convert("RGB")
    new_path = input_path + "_normalized.png"
    img.save(new_path, "PNG")

    return new_path


# ----------------------------
# Run Real-ESRGAN
# ----------------------------
def run_realesrgan(exe_path, input_path, output_path, scale):
    cmd = [
        exe_path,
        "-i", input_path,
        "-o", output_path,
        "-s", str(scale),
        "-n", "realesrgan-x4plus"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise Exception(result.stderr)

    return output_path


# ----------------------------
# 8x pipeline
# ----------------------------
def upscale_8x(exe_path, img_path):
    mid = img_path + "_4x.png"
    run_realesrgan(exe_path, img_path, mid, 4)

    final = img_path + "_8x.png"
    run_realesrgan(exe_path, mid, final, 2)

    return final


# ----------------------------
# MAIN SERVICE
# ----------------------------
def upscale_image(input_path, scale, job_id):
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    exe_path = os.path.join(
        BASE_DIR,
        "realesrgan",
        "realesrgan-ncnn-vulkan.exe"
    )

    if not os.path.exists(exe_path):
        raise Exception("Real-ESRGAN not found")

    update_progress(job_id, 10, "Preparing image")

    input_path = normalize_image(input_path)

    update_progress(job_id, 30, "Running AI model")

    name, _ = os.path.splitext(input_path)

    if scale in [2, 4]:
        output_path = f"{name}_{scale}x.png"
        run_realesrgan(exe_path, input_path, output_path, scale)

    elif scale == 8:
        update_progress(job_id, 50, "Running 4x stage")
        output_path = upscale_8x(exe_path, input_path)

    else:
        raise Exception("Unsupported scale")

    update_progress(job_id, 100, "Done")

    return output_path