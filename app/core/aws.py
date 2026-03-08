import boto3
from botocore.exceptions import ClientError

from app.core.settings import settings


def get_cognito_client():
    print(f"AWS_REGION: {settings.AWS_REGION}")
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
    client = get_s3_client()
    client.delete_objects(
        Bucket=bucket,
        Delete={"Objects": [{"Key": k} for k in keys], "Quiet": True},
    )


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


def download_s3_object(bucket: str, key: str) -> bytes:
    """S3 객체 다운로드."""
    client = get_s3_client()
    response = client.get_object(Bucket=bucket, Key=key)
    return response["Body"].read()


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
