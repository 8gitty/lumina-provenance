import requests
import os
import sys

url = "https://github.com/serengil/deepface_models/releases/download/v1.0/vgg_face_weights.h5"
dest = r"C:\Users\SAHARSH J\.deepface\weights\vgg_face_weights.h5"

print("Starting download...")
response = requests.get(url, stream=True)
total_size = int(response.headers.get('content-length', 0))

os.makedirs(os.path.dirname(dest), exist_ok=True)

downloaded = 0
with open(dest, "wb") as f:
    for chunk in response.iter_content(chunk_size=1024*1024):
        if chunk:
            f.write(chunk)
            downloaded += len(chunk)
            print(f"Downloaded {downloaded / (1024*1024):.2f} MB of {total_size / (1024*1024):.2f} MB", flush=True)

print("Download complete.")
