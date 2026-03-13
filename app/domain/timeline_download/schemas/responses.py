from pydantic import Field

from app.base.base_response import BaseResponse


class TimelineDownloadZipResponse(BaseResponse):
    """다운로드 ZIP presigned URL 응답."""

    download_url: str = Field(..., description="ZIP 다운로드용 presigned URL")
