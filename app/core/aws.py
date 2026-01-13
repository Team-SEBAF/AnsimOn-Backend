import boto3

from app.core.settings import settings


def get_cognito_client():
    return boto3.client(
        "cognito-idp",
        region_name=settings.AWS_REGION,
    )
