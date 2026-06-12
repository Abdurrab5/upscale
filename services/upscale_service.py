import subprocess
import os

def upscale_image(input_path):
    output_path = input_path.replace(".png", "_upscaled.png")

    exe_path = r"E:\Quizer Website\tools building\tools\python\upscale\realesrgan\realesrgan-ncnn-vulkan.exe"

    command = [
        exe_path,
        "-i", input_path,
        "-o", output_path,
        "-n", "realesrgan-x4plus",
        "-g", "-1"
    ]

    print("COMMAND:", command)

    result = subprocess.run(command, capture_output=True, text=True)

    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)

    if result.returncode != 0:
        raise Exception(result.stderr)

    if not os.path.exists(output_path):
        raise Exception("Output file not created")

    return output_path