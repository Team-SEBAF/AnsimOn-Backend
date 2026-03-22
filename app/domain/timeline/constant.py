from enum import Enum
from uuid import UUID

# AI 연결 전까지 시드 데이터 조회용 (seed_timeline_evidence.sql과 동일)
SEED_USER_SUB = UUID("f47ac10b-58cc-4372-a567-0e02b2c3d479")
SEED_COMPLAINT_ID = UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")


class TimelineTag(str, Enum):
    """타임라인 증거 태그. 5가지 고정 값."""

    REPEAT = "REPEAT"  # 반복
    PHYSICAL_HARM = "PHYSICAL_HARM"  # 신체 피해 (경고 아이콘)
    THREAT_COERCION = "THREAT_COERCION"  # 위협·강압 (경고 아이콘)
    SEXUAL_INSULT = "SEXUAL_INSULT"  # 성적 모욕
    REFUSAL_INTENT = "REFUSAL_INTENT"  # 거절 의사
