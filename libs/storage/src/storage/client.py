import logging
import io
from minio import Minio
from minio.error import S3Error
from typing import cast
from .settings import MinioSettings
from .schemas import MinioInput, MinioOutput

logger = logging.getLogger(__name__)


class MinioService:
    def __init__(self, settings: MinioSettings):
        self.settings = settings
        logger.info(f"MinioService configured for endpoint: {self.settings.endpoint}")

    @property
    def _client(self) -> Minio:
        return Minio(
            endpoint=self.settings.endpoint,
            access_key=self.settings.access_key,
            secret_key=self.settings.secret_key,
            secure=self.settings.secure,
        )

    def bucket_exists(self, bucket_name: str) -> bool:
        """
        Checks if a bucket exists in MinIO.

        Args:
            bucket_name (str): The name of the bucket to check.

        Returns:
            bool: True if the bucket exists, False otherwise.
        """
        return self._client.bucket_exists(bucket_name)

    def upload_file(self, input: MinioInput) -> MinioOutput:
        """
        Uploads data (bytes or BytesIO) to a MinIO bucket.
        Auto-creates the bucket if it does not exist.

        Args:
            input (MinioInput): The Pydantic model containing bucket_name,
                                object_name, data, and content_type.

        Returns:
            MinioOutput: An empty output object indicating success.
        """
        if not self.bucket_exists(input.bucket_name):
            logger.warning(f"Bucket '{input.bucket_name}' does not exist. Creating it.")
            self._client.make_bucket(input.bucket_name)

        if isinstance(input.data, bytes):
            data_to_upload = io.BytesIO(input.data)
            data_length = len(input.data)
        elif isinstance(input.data, io.BytesIO):
            data_to_upload = input.data
            data_length = data_to_upload.getbuffer().nbytes
        else:
            raise TypeError("Input 'data' must be bytes or BytesIO.")

        try:
            self._client.put_object(
                bucket_name=input.bucket_name,
                object_name=input.object_name,
                data=data_to_upload,
                length=data_length,
                content_type=input.content_type,
            )
            logger.info(f"File '{input.object_name}' uploaded to MinIO.")
            return MinioOutput()
        except S3Error as e:
            logger.exception(
                f"Minio S3 error while uploading {input.object_name}",
                extra={'bucket': input.bucket_name},
            )
            raise e

    def get_file(self, bucket_name: str, object_name: str) -> io.BytesIO:
        """
        Downloads a file from MinIO and returns it as an in-memory BytesIO object.
        """
        try:
            response = self._client.get_object(bucket_name, object_name)
            # Đọc toàn bộ nội dung file vào BytesIO
            file_data = io.BytesIO(response.read())
            response.close()
            response.release_conn()
            logger.info(f"Successfully retrieved file '{object_name}' from MinIO.")
            return file_data
        except S3Error as e:
            logger.exception(
                f"Minio S3 error while getting file {object_name}",
                extra={'bucket': bucket_name},
            )
            raise e

    def delete_file(self, input: MinioInput) -> MinioOutput:
        """
        Deletes a file from MinIO.
        """
        if not self.bucket_exists(input.bucket_name):
            logger.warning(
                f"Bucket '{input.bucket_name}' does not exist. Skipping deletion.",
            )
            return MinioOutput()

        try:
            self._client.remove_object(
                bucket_name=input.bucket_name,
                object_name=input.object_name,
            )
            logger.info(f"File '{input.object_name}' deleted from MinIO.")
            return MinioOutput()
        except S3Error as e:
            logger.exception(
                f"Minio S3 error while deleting {input.object_name}",
                extra={'bucket': input.bucket_name},
            )
            raise e
