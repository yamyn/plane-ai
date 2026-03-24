# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import os

from .vercel_blob import VercelBlobStorage


def get_storage(request=None):
    """
    Factory function to get the appropriate storage backend.

    Returns VercelBlobStorage if BLOB_READ_WRITE_TOKEN is set (Vercel environment),
    otherwise returns S3Storage.

    Args:
        request: Optional HTTP request (used by S3Storage for MinIO endpoint)

    Returns:
        Storage instance (VercelBlobStorage or S3Storage)
    """
    if os.environ.get("BLOB_READ_WRITE_TOKEN"):
        return VercelBlobStorage()
    else:
        # Import S3Storage lazily to avoid loading boto3 when not needed
        from plane.settings.storage import S3Storage
        return S3Storage(request=request)


__all__ = ["VercelBlobStorage", "get_storage"]
