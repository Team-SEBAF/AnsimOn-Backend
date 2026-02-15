import datetime

from pydantic import BaseModel, Field, field_serializer


class EvidenceIncidentLogFormDataDTO(BaseModel):
    filename: str = Field(..., description="사건 일지 파일명", examples=["사건 일지 파일명"])
    date: datetime.date = Field(
        ..., description="날짜(YYYY-MM-DD)", examples=[datetime.date(2024, 1, 1)]
    )
    time: datetime.time = Field(..., description="시간(HH:MM)", examples=["12:00"])
    location: str = Field(..., description="장소", examples=["서울특별시 강남구 역삼동"])
    description: str = Field(..., description="설명", examples=["그 남자가 계속 나를 쫓아왔다"])
    witness: str = Field(..., description="목격자", examples=["주변 사람"])
    perceived_risk: str = Field(
        ...,
        description="느낀 위험 정도",
        examples=["매우 높음", "높음", "보통", "낮음", "매우 낮음"],
    )

    @field_serializer("time")
    def serialize_time(self, v: datetime.time) -> str:
        return v.strftime("%H:%M")
