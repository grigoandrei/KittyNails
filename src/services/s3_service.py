"""S3 storage for client-uploaded nail inspiration photos.

Photos are uploaded to a private bucket at analyze time; the returned key is
carried through booking and stored on the appointment. The admin panel views
them via short-lived presigned GET URLs so the bucket never needs to be public.

All functions are fault-tolerant: a storage failure must never break the
booking or analysis flow. Upload failures return None (no key persisted);
presigned-URL failures return None (admin simply sees no thumbnail).
"""

import logging
import uuid

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from src.config import settings

logger = logging.getLogger(__name__)

# Maps an accepted image content type to a file extension for the S3 key.
_EXTENSION_BY_CONTENT_TYPE = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif",
}

# Key prefix so nail photos are grouped within the bucket.
_KEY_PREFIX = "nail-photos"


def _get_s3_client():
    return boto3.client("s3", region_name=settings.S3_REGION)


def upload_nail_image(image_bytes: bytes, content_type: str) -> str | None:
    """Upload a nail photo to S3 and return its object key.

    Returns None if S3 is not configured or the upload fails — callers treat a
    missing key as "no photo saved" rather than an error.
    """
    if not settings.S3_BUCKET:
        logger.info("S3_BUCKET not configured — skipping nail image upload")
        return None

    extension = _EXTENSION_BY_CONTENT_TYPE.get(content_type)
    if extension is None:
        logger.warning("Unsupported content type for S3 upload: %s", content_type)
        return None

    key = f"{_KEY_PREFIX}/{uuid.uuid4()}.{extension}"

    try:
        client = _get_s3_client()
        client.put_object(
            Bucket=settings.S3_BUCKET,
            Key=key,
            Body=image_bytes,
            ContentType=content_type,
        )
    except (BotoCoreError, ClientError) as e:
        logger.error("Failed to upload nail image to S3: %s", e)
        return None

    logger.info("Uploaded nail image to s3://%s/%s", settings.S3_BUCKET, key)
    return key


def generate_presigned_url(key: str | None) -> str | None:
    """Return a short-lived presigned GET URL for a stored nail photo.

    Returns None if there is no key, S3 isn't configured, or URL generation
    fails — the admin UI simply renders no thumbnail in that case.
    """
    if not key or not settings.S3_BUCKET:
        return None

    try:
        client = _get_s3_client()
        return client.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.S3_BUCKET, "Key": key},
            ExpiresIn=settings.S3_PRESIGNED_URL_TTL,
        )
    except (BotoCoreError, ClientError) as e:
        logger.error("Failed to generate presigned URL for %s: %s", key, e)
        return None
