"""Tests for the S3 nail-photo storage service (mocked boto3)."""

from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from src.services import s3_service


class TestUploadNailImage:
    """upload_nail_image — no DB needed."""

    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Override conftest's DB fixture — these are pure unit tests."""
        yield

    @patch("src.services.s3_service.settings")
    @patch("src.services.s3_service._get_s3_client")
    def test_upload_success_returns_key(self, mock_get_client, mock_settings):
        mock_settings.S3_BUCKET = "test-bucket"
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        key = s3_service.upload_nail_image(b"imagebytes", "image/jpeg")

        assert key is not None
        assert key.startswith("nail-photos/")
        assert key.endswith(".jpg")
        mock_client.put_object.assert_called_once()
        call = mock_client.put_object.call_args[1]
        assert call["Bucket"] == "test-bucket"
        assert call["Key"] == key
        assert call["Body"] == b"imagebytes"
        assert call["ContentType"] == "image/jpeg"

    @patch("src.services.s3_service.settings")
    def test_upload_no_bucket_returns_none(self, mock_settings):
        mock_settings.S3_BUCKET = ""
        assert s3_service.upload_nail_image(b"x", "image/png") is None

    @patch("src.services.s3_service.settings")
    @patch("src.services.s3_service._get_s3_client")
    def test_upload_unsupported_type_returns_none(
        self, mock_get_client, mock_settings
    ):
        mock_settings.S3_BUCKET = "test-bucket"
        assert s3_service.upload_nail_image(b"x", "image/tiff") is None
        mock_get_client.return_value.put_object.assert_not_called()

    @patch("src.services.s3_service.settings")
    @patch("src.services.s3_service._get_s3_client")
    def test_upload_extension_matches_content_type(
        self, mock_get_client, mock_settings
    ):
        mock_settings.S3_BUCKET = "test-bucket"
        mock_get_client.return_value = MagicMock()

        assert s3_service.upload_nail_image(b"x", "image/png").endswith(".png")
        assert s3_service.upload_nail_image(b"x", "image/webp").endswith(".webp")

    @patch("src.services.s3_service.settings")
    @patch("src.services.s3_service._get_s3_client")
    def test_upload_client_error_returns_none(self, mock_get_client, mock_settings):
        mock_settings.S3_BUCKET = "test-bucket"
        mock_client = MagicMock()
        mock_client.put_object.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "nope"}}, "PutObject"
        )
        mock_get_client.return_value = mock_client

        # Storage failure must not raise — returns None so booking still works.
        assert s3_service.upload_nail_image(b"x", "image/jpeg") is None


class TestGeneratePresignedUrl:
    @pytest.fixture(autouse=True)
    def setup_database(self):
        yield

    @patch("src.services.s3_service.settings")
    @patch("src.services.s3_service._get_s3_client")
    def test_presigned_success(self, mock_get_client, mock_settings):
        mock_settings.S3_BUCKET = "test-bucket"
        mock_settings.S3_PRESIGNED_URL_TTL = 3600
        mock_client = MagicMock()
        mock_client.generate_presigned_url.return_value = "https://signed.example/x"
        mock_get_client.return_value = mock_client

        url = s3_service.generate_presigned_url("nail-photos/abc.jpg")

        assert url == "https://signed.example/x"
        mock_client.generate_presigned_url.assert_called_once_with(
            "get_object",
            Params={"Bucket": "test-bucket", "Key": "nail-photos/abc.jpg"},
            ExpiresIn=3600,
        )

    @patch("src.services.s3_service.settings")
    def test_presigned_none_key_returns_none(self, mock_settings):
        mock_settings.S3_BUCKET = "test-bucket"
        assert s3_service.generate_presigned_url(None) is None

    @patch("src.services.s3_service.settings")
    def test_presigned_no_bucket_returns_none(self, mock_settings):
        mock_settings.S3_BUCKET = ""
        assert s3_service.generate_presigned_url("nail-photos/abc.jpg") is None

    @patch("src.services.s3_service.settings")
    @patch("src.services.s3_service._get_s3_client")
    def test_presigned_client_error_returns_none(self, mock_get_client, mock_settings):
        mock_settings.S3_BUCKET = "test-bucket"
        mock_settings.S3_PRESIGNED_URL_TTL = 3600
        mock_client = MagicMock()
        mock_client.generate_presigned_url.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "nope"}}, "GetObject"
        )
        mock_get_client.return_value = mock_client

        assert s3_service.generate_presigned_url("nail-photos/abc.jpg") is None
