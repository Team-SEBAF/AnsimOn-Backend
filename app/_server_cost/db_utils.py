import boto3
from fastapi import HTTPException

from app.core.settings import settings


def _get_rds_client():
    return boto3.client(
        "rds",
        region_name=settings.AWS_REGION,
    )


RDS_INSTANCE_TAGS = {
    "Env": "dev",
    "Project": "Ansimon",
}


def _match_tags(tag_list: list[dict]) -> bool:
    tag_map = {t["Key"]: t["Value"] for t in tag_list}
    return all(tag_map.get(k) == v for k, v in RDS_INSTANCE_TAGS.items())


def _get_rds_instance_by_tags():
    rds = _get_rds_client()
    resp = rds.describe_db_instances()

    for db in resp["DBInstances"]:
        arn = db["DBInstanceArn"]
        tags = rds.list_tags_for_resource(ResourceName=arn)["TagList"]

        if _match_tags(tags):
            return db

    raise HTTPException(
        status_code=404,
        detail="태그 조건에 맞는 RDS 인스턴스를 찾을 수 없습니다.",
    )
