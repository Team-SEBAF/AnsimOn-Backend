from pydantic import Field

from app.base.base_response import BaseResponse


class DownloadZipResponse(BaseResponse):
    """다운로드 ZIP presigned URL 응답 (타임라인·고소장/진술서 공통)."""

    download_url: str = Field(..., description="ZIP 다운로드용 presigned URL")
