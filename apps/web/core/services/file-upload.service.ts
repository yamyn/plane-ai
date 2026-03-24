/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import type { AxiosRequestConfig } from "axios";
import axios from "axios";
// plane constants
import { API_BASE_URL } from "@plane/constants";
// services
import { APIService } from "@/services/api.service";

export class FileUploadService extends APIService {
  private cancelSource: any;

  constructor() {
    super("");
  }

  async uploadFile(
    url: string,
    data: FormData,
    uploadProgressHandler?: AxiosRequestConfig["onUploadProgress"]
  ): Promise<void> {
    this.cancelSource = axios.CancelToken.source();
    // For relative URLs (our proxy endpoints), prepend API_BASE_URL and use credentials
    // For absolute URLs (external storage like S3), use as-is without credentials
    const isRelativeUrl = url.startsWith("/");
    const finalUrl = isRelativeUrl ? `${API_BASE_URL}${url}` : url;
    return this.post(finalUrl, data, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
      cancelToken: this.cancelSource.token,
      withCredentials: isRelativeUrl,
      onUploadProgress: uploadProgressHandler,
    })
      .then((response) => response?.data)
      .catch((error) => {
        if (axios.isCancel(error)) {
          console.log(error.message);
        } else {
          throw error?.response?.data;
        }
      });
  }

  cancelUpload() {
    this.cancelSource.cancel("Upload canceled");
  }
}
