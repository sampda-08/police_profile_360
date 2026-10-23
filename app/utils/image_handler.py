import base64
import io
from PIL import Image

def process_and_encode_image(file_storage, max_dimension=800, quality=75):
    """
    Resizes and compresses an uploaded photo in memory (no disk usage).
    Returns a data URI string ('data:image/jpeg;base64,...') or None.
    """
    if not file_storage or file_storage.filename == '':
        return None

    try:
        # Read directly from in-memory stream
        img = Image.open(file_storage.stream)

        # Convert transparent formats (PNG/RGBA/Palette) to RGB for clean JPEG compression
        if img.mode in ("RGBA", "P", "LA"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")

        # Proportional resize: caps largest edge at 800px without distortion
        img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)

        # Compress into memory buffer
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=quality, optimize=True)
        buffer.seek(0)

        # Encode to Base64 data URI
        encoded_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return f"data:image/jpeg;base64,{encoded_data}"

    except Exception as e:
        print(f"[Image Compression Error]: {e}")
        return None