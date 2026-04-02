import json

import boto3
from botocore.exceptions import ClientError

from app.core.settings import settings


def get_cognito_client():
    return boto3.client(
        "cognito-idp",
        region_name=settings.AWS_REGION,
    )


def get_s3_client():
    return boto3.client(
        "s3",
        region_name=settings.AWS_REGION,
        endpoint_url=f"https://s3.{settings.AWS_REGION}.amazonaws.com",
    )


def upload_fileobj(
    fileobj,
    bucket: str,
    key: str,
    content_type: str,
):
    get_s3_client().upload_fileobj(
        Fileobj=fileobj,
        Bucket=bucket,
        Key=key,
        ExtraArgs={
            "ContentType": content_type,
        },
    )


def delete_s3_objects(bucket: str, keys: list[str]) -> None:
    """지정한 키의 S3 객체 삭제."""
    if not keys:
        return
    client = get_s3_client()
    client.delete_objects(
        Bucket=bucket,
        Delete={"Objects": [{"Key": k} for k in keys], "Quiet": True},
    )


def delete_s3_by_prefixes(bucket: str, prefixes: list[str]) -> None:
    """prefix 목록에 대해 각 prefix 하위 객체 전체 삭제 (빈 폴더 placeholder 포함)."""
    for prefix in prefixes:
        delete_s3_objects_by_prefix(bucket, prefix)


def delete_s3_objects_by_prefix(bucket: str, prefix: str) -> None:
    """prefix로 시작하는 모든 객체 삭제. S3는 폴더 개념이 없어 prefix 매칭으로 삭제."""
    client = get_s3_client()
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        if contents := page.get("Contents"):
            client.delete_objects(
                Bucket=bucket,
                Delete={"Objects": [{"Key": obj["Key"]} for obj in contents], "Quiet": True},
            )


def generate_presigned_put_url(
    bucket: str,
    key: str,
    content_type: str,
    expires_in: int = 3600,
) -> str:
    """S3 PUT 업로드용 presigned URL 생성. 프론트에서 직접 업로드 시 사용."""
    client = get_s3_client()
    return client.generate_presigned_url(
        ClientMethod="put_object",
        Params={
            "Bucket": bucket,
            "Key": key,
            "ContentType": content_type,
        },
        ExpiresIn=expires_in,
    )


def generate_presigned_get_url(
    bucket: str,
    key: str,
    expires_in: int = 3600,
    response_content_disposition: str | None = None,
) -> str:
    """S3 GET 다운로드용 presigned URL 생성.
    response_content_disposition: 다운로드 시 브라우저에 전달할 Content-Disposition (예: attachment; filename="파일명.zip")
    """
    client = get_s3_client()
    params: dict = {"Bucket": bucket, "Key": key}
    if response_content_disposition:
        params["ResponseContentDisposition"] = response_content_disposition
    return client.generate_presigned_url(
        ClientMethod="get_object",
        Params=params,
        ExpiresIn=expires_in,
    )


def download_s3_object(bucket: str, key: str) -> bytes:
    """S3 객체 다운로드."""
    client = get_s3_client()
    response = client.get_object(Bucket=bucket, Key=key)
    return response["Body"].read()


def download_s3_object_with_metadata(bucket: str, key: str) -> tuple[bytes, dict]:
    """S3 객체 다운로드 + 메타데이터(ContentType 등) 반환."""
    client = get_s3_client()
    response = client.get_object(Bucket=bucket, Key=key)
    body = response["Body"].read()
    meta = {
        "ContentType": response.get("ContentType"),
        **response.get("Metadata", {}),
    }
    return body, meta


def head_s3_object(bucket: str, key: str) -> dict | None:
    """S3 객체 존재 여부 및 메타데이터 확인. 없으면 None."""
    try:
        client = get_s3_client()
        return client.head_object(Bucket=bucket, Key=key)
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code == "404":
            return None
        if code == "403":
            return None  # 객체 없을 때 일부 설정에서 403 반환
        raise


def get_sqs_client():
    return boto3.client(
        "sqs",
        region_name=settings.AWS_REGION,
    )


def send_sqs_message(message: dict):
    get_sqs_client().send_message(
        QueueUrl=settings.SQS_QUEUE_URL,
        MessageBody=json.dumps(message),
    )
