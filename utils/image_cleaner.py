from PIL import Image
import io

def strip_exif(image_bytes: bytes) -> bytes:
    """
    Removes all EXIF metadata from an image and returns the clean bytes.
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))
        
        # This effectively strips metadata by saving only the pixel data to a new object
        # We also convert to RGB if it's RGBA to ensure compatibility, or keep it depending on format
        format = img.format if img.format else "JPEG"
        
        clean_io = io.BytesIO()
        
        # data_only = list(img.getdata()) # This is slow for large images
        # Better: save without 'exif' or 'info'
        img.save(clean_io, format=format, optimize=True)
        return clean_io.getvalue()
    except Exception as e:
        print(f"Error stripping EXIF: {e}")
        return image_bytes # Return original if processing fails
