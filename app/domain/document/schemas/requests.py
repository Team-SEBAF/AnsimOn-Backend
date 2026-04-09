from pydantic import BaseModel, Field

from app.domain.document.schemas.form_data import (
    ComplaintFormSection1Complainant,
    ComplaintFormSection2Accused,
    # ComplaintFormSection3ComplaintPurpose,  # 3. 고소 취지 — PDF 고정 문구 (폼 PATCH 불가)
    ComplaintFormSection4CrimeFacts,
    ComplaintFormSection5ComplaintReason,
    ComplaintFormSection6Evidence,
    ComplaintFormSection7RelatedCases,
    ComplaintFormSection8Other,
    ComplaintFormSubmissionFooter,
)


class PatchComplaintFormDataRequest(BaseModel):
    section_1_complainant: ComplaintFormSection1Complainant | None = Field(
        default=None,
        description="1. 고소인",
    )
    section_2_accused: ComplaintFormSection2Accused | None = Field(
        default=None,
        description="2. 피고소인",
    )
    # section_3_complaint_purpose: ComplaintFormSection3ComplaintPurpose | None = Field(
    #     default=None,
    #     description="3. 고소 취지",
    # )
    section_4_crime_facts: ComplaintFormSection4CrimeFacts | None = Field(
        default=None,
        description="4. 범죄 사실",
    )
    section_5_complaint_reason: ComplaintFormSection5ComplaintReason | None = Field(
        default=None,
        description="5. 고소 이유",
    )
    section_6_evidence: ComplaintFormSection6Evidence | None = Field(
        default=None,
        description="6. 증거 자료",
    )
    section_7_related_cases: ComplaintFormSection7RelatedCases | None = Field(
        default=None,
        description="7. 관련 사건",
    )
    section_8_other: ComplaintFormSection8Other | None = Field(
        default=None,
        description="8. 기타",
    )
    submission_footer: ComplaintFormSubmissionFooter | None = Field(
        default=None,
        description="고소인/제출인·제출처(제출일은 수기)",
    )


class PatchStatementFormDataRequest(BaseModel):
    damage_facts_statement: str | None = Field(default=None, description="피해 사실 진술")
    date_year: int | None = Field(default=None, description="작성 일자 — 연(년)")
    date_month: int | None = Field(default=None, description="작성 일자 — 월")
    date_day: int | None = Field(default=None, description="작성 일자 — 일")
    declarant_name: str | None = Field(default=None, description="진술인 성명(인)")
    submission_target_police_station: str | None = Field(
        default=None,
        description="제출처",
    )
