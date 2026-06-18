import os
import subprocess
import json
from PIL import Image


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


def normalize_image(input_path):
    ext = os.path.splitext(input_path)[1].lower()

    if ext in [".png", ".jpg", ".jpeg"]:
        return input_path

    img = Image.open(input_path).convert("RGB")

    new_path = input_path + "_normalized.png"

    img.save(new_path, "PNG")

    return new_path


def run_x4(exe_path, input_path, output_path):
    cmd = [
        exe_path,
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

    if result.returncode != 0:
        raise Exception(result.stderr)

    return output_path


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


def upscale_image(input_path, scale, job_id):

    BASE_DIR = os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )

    exe_path = os.path.join(
        BASE_DIR,
        "realesrgan",
        "realesrgan-ncnn-vulkan.exe"
    )

    if not os.path.exists(exe_path):
        raise Exception("RealESRGAN executable not found")

    update_progress(job_id, 10, "Preparing image")

    input_path = normalize_image(input_path)

    update_progress(job_id, 30, "Running AI upscale")

    name, _ = os.path.splitext(input_path)

    x4_output = f"{name}_x4_ai.png"

    run_x4(
        exe_path,
        input_path,
        x4_output
    )

    update_progress(job_id, 70, "Generating requested scale")

    outputs = generate_multi_scale(
        x4_output,
        name
    )

    selected = outputs.get(f"{scale}x")

    if not selected:
        selected = outputs["4x"]

    update_progress(job_id, 100, "Done")

    return selected