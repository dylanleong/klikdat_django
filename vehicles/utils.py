from io import BytesIO
from django.core.files import File
from PIL import Image

def compress_image(image_field, max_dimension=1920, quality=75):
    """
    Compresses an uploaded image.
    1. Resizes if dimension > max_dimension (maintaining aspect ratio).
    2. Converts to RGB (strips alpha channel if present).
    3. Saves as JPEG with reduced quality.
    
    Args:
        image_field: The ImageFieldFile to compress.
        max_dimension: Max width or height.
        quality: JPEG compression quality (1-100).
        
    Returns:
        ContentFile: Compressed image file ready to be saved.
    """
    if not image_field:
        return None
        
    try:
        img = Image.open(image_field)
        
        # Orient the image correctly based on EXIF
        try:
            from PIL import ImageOps
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass # Ignore EXIF issues
            
        # Resize if necessary
        width, height = img.size
        if width > max_dimension or height > max_dimension:
            ratio = min(max_dimension / width, max_dimension / height)
            new_size = (int(width * ratio), int(height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            
        # Convert to RGB (in case of RGBA/P)
        if img.mode != 'RGB':
            img = img.convert('RGB')
            
        # Save to buffer
        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=quality)
        buffer.seek(0)
        
        # Return new file
        # We generally want to force .jpg extension for consistency since we converted to JPEG
        original_name = image_field.name.rsplit('.', 1)[0]
        # Handle if name already has path
        original_base = original_name.split('/')[-1]
        new_name = f"{original_base}.jpg"
        
        return File(buffer, name=new_name)
        
    except Exception as e:
        print(f"Error compressing image: {e}")
        return image_field # Return original if compression fails
