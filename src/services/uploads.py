"""Shared validation for image uploads."""

from fastapi import UploadFile

from src.exceptions import ValidationError

SUPPORTED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}

# Bedrock caps request payloads at 20 MB. Keep uploads well under that after
# base64 expansion. 5 MB of raw image is plenty for a phone photo of nails.
MAX_UPLOAD_BYTES = 5 * 1024 * 1024


async def read_image(image: UploadFile) -> bytes:
    """Validate type and size, then return the raw bytes."""
    if image.content_type not in SUPPORTED_IMAGE_TYPES:
        raise ValidationError(
            "Unsupported image type. Please upload one of: "
            f"{', '.join(sorted(SUPPORTED_IMAGE_TYPES))}."
        )

    image_bytes = await image.read()
    if not image_bytes:
        raise ValidationError("The uploaded file is empty.")
    if len(image_bytes) > MAX_UPLOAD_BYTES:
        raise ValidationError("Image is too large. Please upload an image under 5 MB.")
    return image_bytes
