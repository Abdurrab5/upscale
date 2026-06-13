import subprocess
import os

def upscale_image(input_path):

    

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    exe_path = os.path.join(
    BASE_DIR,
    "realesrgan",
    "realesrgan-ncnn-vulkan.exe"
    )

    name, _ = os.path.splitext(input_path)

    output_path = f"{name}_upscaled.png"

   # exe_path = os.path.join(BASE_DIR, "realesrgan-ncnn-vulkan")
    print("EXE PATH:", exe_path)
    print("EXISTS:", os.path.exists(exe_path))
    print("INPUT EXISTS:", os.path.exists(input_path))
    print("INPUT SIZE:", os.path.getsize(input_path))

    command = [
        exe_path,
        "-i", input_path,
        "-o", output_path,
        "-n", "realesrgan-x4plus",
    ]

    # result = subprocess.run(
    # command,
    # capture_output=True,
    # text=True,
    # cwd=BASE_DIR,
    # timeout=120
    #     )

    # print("RETURN CODE:", result.returncode)
    # print("STDERR:", result.stderr)
    print("COMMAND:", command)

    result = subprocess.run(
    command,
    capture_output=True,
    text=True,
    cwd=BASE_DIR,
  
    )

    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    print("RETURN CODE:", result.returncode)

    if result.returncode != 0:
        raise Exception(result.stderr or result.stdout)

    return output_path