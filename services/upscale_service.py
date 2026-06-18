import os
import platform
import subprocess
import json
from PIL import Image

# ----------------------------
# Paths
# ----------------------------

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if platform.system() == "Windows":
    EXE_NAME = "realesrgan-ncnn-vulkan.exe"
else:
    EXE_NAME = "realesrgan-ncnn-vulkan"

EXE_PATH = os.path.join(
    BASE_DIR,
    "realesrgan",
    EXE_NAME
)

# Linux execute permission
if platform.system() != "Windows" and os.path.exists(EXE_PATH):
    os.chmod(EXE_PATH, 0o755)


# ----------------------------
# Progress updater
# ----------------------------

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


# ----------------------------
# Normalize image
# ----------------------------

def normalize_image(input_path):
    ext = os.path.splitext(input_path)[1].lower()

    if ext in [".png", ".jpg", ".jpeg"]:
        return input_path

    img = Image.open(input_path).convert("RGB")

    normalized_path = input_path + "_normalized.png"

    img.save(normalized_path, "PNG")

    return normalized_path


# ----------------------------
# Run RealESRGAN x4
# ----------------------------

def run_x4(input_path, output_path):

    print("Executable:", EXE_PATH)
    print("Exists:", os.path.exists(EXE_PATH))

    if not os.path.exists(EXE_PATH):
        raise Exception(
            f"RealESRGAN executable not found: {EXE_PATH}"
        )

    cmd = [
        EXE_PATH,
        "-i", input_path,
        "-o", output_path,
        "-s", "4",
        "-n", "realesrgan-x4plus",
        "-j", "4:4:4"
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)

    if result.returncode != 0:
        raise Exception(
            f"RealESRGAN failed:\n{result.stderr}"
        )

    return output_path


# ----------------------------
# Generate 2x / 4x / 8x
# ----------------------------

def generate_multi_scale(x4_image_path, base_path):

    img = Image.open(x4_image_path)

    w, h = img.size

    path_2x = base_path + "_2x.png"
    path_4x = base_path + "_4x.png"
    path_8x = base_path + "_8x.png"

    img.resize(
        (w // 2, h // 2),
        Image.LANCZOS
    ).save(path_2x)

    img.save(path_4x)

    img.resize(
        (w * 2, h * 2),
        Image.LANCZOS
    ).save(path_8x)

    return {
        "2x": path_2x,
        "4x": path_4x,
        "8x": path_8x
    }


# ----------------------------
# Main Upscale Function
# ----------------------------

def upscale_image(input_path, scale, job_id):

    update_progress(
        job_id,
        10,
        "Preparing image"
    )

    input_path = normalize_image(input_path)

    update_progress(
        job_id,
        30,
        "Running AI upscale"
    )

    name, _ = os.path.splitext(input_path)

    x4_output = f"{name}_x4_ai.png"

    run_x4(
        input_path,
        x4_output
    )

    update_progress(
        job_id,
        70,
        "Generating requested scale"
    )

    outputs = generate_multi_scale(
        x4_output,
        name
    )

    selected = outputs.get(
        f"{scale}x",
        outputs["4x"]
    )

    update_progress(
        job_id,
        100,
        "Done"
    )

    return selected