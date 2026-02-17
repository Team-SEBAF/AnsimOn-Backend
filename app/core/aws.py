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

