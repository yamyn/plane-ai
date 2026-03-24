# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

"""
Vercel Blob Storage Backend for Django

This module provides a Django storage backend for Vercel Blob.
It uses Vercel Blob's REST API to store and retrieve files.

Usage:
    # In settings.py
    DEFAULT_FILE_STORAGE = 'plane.utils.storage.vercel_blob.VercelBlobStorage'

    # Environment variables required:
    BLOB_READ_WRITE_TOKEN=vercel_blob_rw_xxxxx
"""

import os
import requests
from urllib.parse import urljoin
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import Storage


class VercelBlobStorage(Storage):
    """
    Django storage backend for Vercel Blob.

    Vercel Blob REST API documentation:
    https://vercel.com/docs/storage/vercel-blob/using-blob-sdk
    """

    BASE_URL = "https://blob.vercel-storage.com"

    def __init__(self):
        self.token = getattr(settings, 'VERCEL_BLOB_TOKEN', None) or os.environ.get('BLOB_READ_WRITE_TOKEN')
        if not self.token:
            raise ValueError("BLOB_READ_WRITE_TOKEN environment variable is required for Vercel Blob storage")

        self.headers = {
            "Authorization": f"Bearer {self.token}",
        }

    def _get_key_name(self, name):
        """Normalize the file path/name."""
        return name.lstrip('/')

    def _save(self, name, content):
        """
        Save a file to Vercel Blob.

        Args:
            name: The file path/name
            content: The file content (File object)

        Returns:
            The URL of the saved blob
        """
        key = self._get_key_name(name)

        # Read content
        if hasattr(content, 'read'):
            data = content.read()
        else:
            data = content

        # Determine content type
        content_type = getattr(content, 'content_type', 'application/octet-stream')

        # Upload to Vercel Blob
        response = requests.put(
            f"{self.BASE_URL}/{key}",
            headers={
                **self.headers,
                "Content-Type": content_type,
                "x-api-version": "7",
                "x-content-type": content_type,
            },
            data=data,
        )

        if response.status_code not in (200, 201):
            raise Exception(f"Failed to upload to Vercel Blob: {response.status_code} - {response.text}")

        result = response.json()
        # Return the pathname for Django to store
        return result.get('pathname', key)

    def _open(self, name, mode='rb'):
        """
        Open a file from Vercel Blob.

        Args:
            name: The file path/name or full URL
            mode: File mode (ignored, always binary read)

        Returns:
            A ContentFile with the blob content
        """
        url = self.url(name)

        response = requests.get(url, headers=self.headers)

        if response.status_code != 200:
            raise FileNotFoundError(f"Blob not found: {name}")

        return ContentFile(response.content, name=name)

    def delete(self, name):
        """
        Delete a file from Vercel Blob.

        Args:
            name: The file path/name or full URL
        """
        # Vercel Blob delete endpoint
        url = self.url(name)

        response = requests.post(
            f"{self.BASE_URL}/delete",
            headers={
                **self.headers,
                "Content-Type": "application/json",
            },
            json={"urls": [url]},
        )

        if response.status_code not in (200, 204):
            raise Exception(f"Failed to delete from Vercel Blob: {response.status_code} - {response.text}")

    def exists(self, name):
        """
        Check if a file exists in Vercel Blob.

        Args:
            name: The file path/name

        Returns:
            True if the file exists, False otherwise
        """
        try:
            url = self.url(name)
            response = requests.head(url)
            return response.status_code == 200
        except Exception:
            return False

    def url(self, name):
        """
        Get the URL for a file.

        Args:
            name: The file path/name or full URL

        Returns:
            The full URL to access the blob
        """
        if name.startswith('http://') or name.startswith('https://'):
            return name

        key = self._get_key_name(name)
        # Vercel Blob public URL format
        store_id = self.token.split('_')[3] if '_' in self.token else 'store'
        return f"https://{store_id}.public.blob.vercel-storage.com/{key}"

    def size(self, name):
        """
        Get the size of a file.

        Args:
            name: The file path/name

        Returns:
            The file size in bytes
        """
        url = self.url(name)
        response = requests.head(url)

        if response.status_code != 200:
            raise FileNotFoundError(f"Blob not found: {name}")

        return int(response.headers.get('Content-Length', 0))

    def listdir(self, path):
        """
        List contents of a directory/prefix.

        Args:
            path: The directory prefix

        Returns:
            Tuple of (directories, files)
        """
        prefix = self._get_key_name(path)

        response = requests.get(
            f"{self.BASE_URL}",
            headers=self.headers,
            params={"prefix": prefix},
        )

        if response.status_code != 200:
            return ([], [])

        result = response.json()
        blobs = result.get('blobs', [])

        files = [blob['pathname'] for blob in blobs]
        return ([], files)

    def get_accessed_time(self, name):
        raise NotImplementedError("Vercel Blob doesn't track access time")

    def get_created_time(self, name):
        raise NotImplementedError("Vercel Blob doesn't expose creation time via HEAD")

    def get_modified_time(self, name):
        raise NotImplementedError("Vercel Blob doesn't expose modification time via HEAD")

    def generate_presigned_post(self, object_name, file_type, file_size, expiration=None):
        """
        Generate upload data for Vercel Blob.

        Since Vercel Blob doesn't support S3-style presigned POST (CORS blocks Authorization header),
        we return a proxy URL that points to our backend. The frontend uploads to our backend,
        which then uploads to Vercel Blob.

        Args:
            object_name: The file path/name to upload
            file_type: The content type of the file
            file_size: The size of the file in bytes
            expiration: Not used (kept for API compatibility)

        Returns:
            Dict with upload URL and fields for client upload (S3-compatible format)
        """
        key = self._get_key_name(object_name)

        # Return proxy URL - frontend will POST to our backend
        # The backend endpoint /api/assets/v2/upload-proxy/ will handle the actual Vercel upload
        return {
            "url": "/api/assets/v2/upload-proxy/",
            "fields": {
                "key": key,
                "Content-Type": file_type,
            },
        }

    def generate_presigned_url(
        self,
        object_name,
        expiration=None,
        http_method="GET",
        disposition="inline",
        filename=None,
    ):
        """
        Generate a URL to access a Vercel Blob object.

        Vercel Blob URLs are public by default, so no signing is needed.

        Args:
            object_name: The file path/name or full URL
            expiration: Not used (kept for API compatibility)
            http_method: Not used (kept for API compatibility)
            disposition: Not used (Vercel Blob doesn't support this)
            filename: Not used (kept for API compatibility)

        Returns:
            The public URL for the blob
        """
        return self.url(object_name)

    def get_object_metadata(self, object_name):
        """Get the metadata for a Vercel Blob object."""
        url = self.url(object_name)
        response = requests.head(url)

        if response.status_code != 200:
            return None

        return {
            "ContentType": response.headers.get("Content-Type"),
            "ContentLength": int(response.headers.get("Content-Length", 0)),
            "LastModified": response.headers.get("Last-Modified"),
            "ETag": response.headers.get("ETag"),
            "Metadata": {},
        }

    def copy_object(self, object_name, new_object_name):
        """
        Copy a Vercel Blob object to a new location.

        Vercel Blob doesn't have native copy, so we download and re-upload.
        """
        try:
            # Download the source blob
            source_url = self.url(object_name)
            response = requests.get(source_url)

            if response.status_code != 200:
                return None

            # Upload to new location
            new_key = self._get_key_name(new_object_name)
            content_type = response.headers.get("Content-Type", "application/octet-stream")

            upload_response = requests.put(
                f"{self.BASE_URL}/{new_key}",
                headers={
                    **self.headers,
                    "Content-Type": content_type,
                    "x-api-version": "7",
                },
                data=response.content,
            )

            if upload_response.status_code not in (200, 201):
                return None

            return upload_response.json()
        except Exception:
            return None

    def upload_file(
        self,
        file_obj,
        object_name: str,
        content_type: str = None,
        extra_args: dict = {},
    ) -> dict | bool:
        """
        Upload a file directly to Vercel Blob.

        Returns:
            dict with 'url' and 'pathname' on success, False on failure
        """
        try:
            key = self._get_key_name(object_name)

            if hasattr(file_obj, 'read'):
                data = file_obj.read()
            else:
                data = file_obj

            if not content_type:
                content_type = "application/octet-stream"

            response = requests.put(
                f"{self.BASE_URL}/{key}",
                headers={
                    **self.headers,
                    "Content-Type": content_type,
                    "x-api-version": "7",
                },
                data=data,
            )

            if response.status_code in (200, 201):
                return response.json()
            return False
        except Exception:
            return False

    def delete_files(self, object_names):
        """Delete multiple Vercel Blob objects."""
        try:
            urls = [self.url(name) for name in object_names]

            response = requests.post(
                f"{self.BASE_URL}/delete",
                headers={
                    **self.headers,
                    "Content-Type": "application/json",
                },
                json={"urls": urls},
            )

            return response.status_code in (200, 204)
        except Exception:
            return False
