from PIL import Image
import pillow_heif
import os


pillow_heif.register_heif_opener()


SOURCE_FOLDER = "files"
DESTINATION_FOLDER = "files/converted"

if not os.path.exists(DESTINATION_FOLDER):
    os.makedirs(DESTINATION_FOLDER)


for file in os.listdir(SOURCE_FOLDER):
    file_path = f"{SOURCE_FOLDER}/{file}"

    if file.endswith(".HEIC") and os.path.isfile(file_path):

        print(f"Converting {file} to JPEG")

        img = Image.open(file_path)

        new_file_path = f"{DESTINATION_FOLDER}/{file.replace('.HEIC', '.jpg')}"

        if os.path.exists(new_file_path):
            os.remove(new_file_path)

        img.save(
            f"{DESTINATION_FOLDER}/{file.replace('.HEIC', '.jpg')}",
            format("JPEG"),
        )
