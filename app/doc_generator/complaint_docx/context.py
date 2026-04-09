from __future__ import annotations

from app.domain.document.schemas.form_data import ComplaintFormData

_REP_UNCHECKED_FIELD = "            "
_SQ_FILLED = "■"
_SQ_EMPTY = "□"
_EVIDENCE_LIST_BULLET = "\u2022"
_EVIDENCE_LIST_SEP = "\a"


def _nz(v: str | None) -> str:
    return v if v else "불상"


def _contact_line(mobile: str | None, home: str | None, office: str | None) -> str:
    """값이 있는 항목만 라벨 괄호 뒤 공백 한 칸 두고 값을 이어 한 줄로."""
    parts: list[str] = []
    if mobile:
        parts.append(f"(휴대폰) {mobile}")
    if home:
        parts.append(f"(자택) {home}")
    if office:
        parts.append(f"(사무실) {office}")
    return " ".join(parts)


def _bool_square(v: bool) -> str:
    """True: 칠한 사각, False: 빈 사각."""
    return _SQ_FILLED if v else _SQ_EMPTY


def _paired_true_false_squares(value: bool | None) -> tuple[str, str]:
    """(참/있음 쪽, 거짓/없음 쪽). True → (■,□), False → (□,■), None → (□,□)."""
    if value is True:
        return _SQ_FILLED, _SQ_EMPTY
    if value is False:
        return _SQ_EMPTY, _SQ_FILLED
    return _SQ_EMPTY, _SQ_EMPTY


def _evidence_choice_squares(has_beyond: bool | None) -> tuple[str, str]:
    """(증거 없음 문자 옆, 증거 있음 문자 옆). True → (□,■), False → (■,□), None → (□,□)."""
    if has_beyond is True:
        return _SQ_EMPTY, _SQ_FILLED
    if has_beyond is False:
        return _SQ_FILLED, _SQ_EMPTY
    return _SQ_EMPTY, _SQ_EMPTY


def _evidence_list_for_doc(items: list[str]) -> str:
    """증거 목록: 항목마다 bullet + docxtpl \\a(새 단락)로 정렬 맞춤."""
    lines: list[str] = []
    for raw in items:
        text = raw.strip()
        if text:
            lines.append(f"{_EVIDENCE_LIST_BULLET} {text}")
    return _EVIDENCE_LIST_SEP.join(lines)


def build_complaint_context(data: ComplaintFormData) -> dict[str, str]:
    s1 = data.section_1_complainant
    s2 = data.section_2_accused
    c1 = s1.contact
    c2 = s2.contact
    r = s1.representative
    s6 = data.section_6_evidence
    s7 = data.section_7_related_cases
    footer = data.submission_footer

    s6_no, s6_has = _evidence_choice_squares(s6.has_evidence_beyond_statement)
    s7_1_t, s7_1_f = _paired_true_false_squares(s7.is_duplicate_complaint)
    s7_2_t, s7_2_f = _paired_true_false_squares(s7.has_related_criminal_investigation)
    s7_3_t, s7_3_f = _paired_true_false_squares(s7.has_related_civil_lawsuit)

    return {
        "s1_name_or_company": _nz(s1.name_or_company),
        "s1_registration_num": _nz(s1.resident_or_corp_registration_number),
        "s1_address": _nz(s1.address),
        "s1_occupation": _nz(s1.occupation),
        "s1_office_address": _nz(s1.office_address),
        "s1_contact": _contact_line(c1.mobile, c1.home, c1.office),
        "s1_email": _nz(s1.email),
        "is_rep": _bool_square(r.is_legal_representative),
        "rep_n": _nz(r.name) if r.is_legal_representative else _REP_UNCHECKED_FIELD,
        "rep_c": _nz(r.contact) if r.is_legal_representative else _REP_UNCHECKED_FIELD,
        "is_law": _bool_square(r.is_lawyer),
        "law_n": _nz(r.name) if r.is_lawyer else _REP_UNCHECKED_FIELD,
        "law_c": _nz(r.contact) if r.is_lawyer else _REP_UNCHECKED_FIELD,
        "s2_name": _nz(s2.name),
        "s2_registration_num": _nz(s2.resident_registration_number),
        "s2_address": _nz(s2.address),
        "s2_occupation": _nz(s2.occupation),
        "s2_office_address": _nz(s2.office_address),
        "s2_contact": _contact_line(c2.mobile, c2.home, c2.office),
        "s2_email": _nz(s2.email),
        "s2_other_details": _nz(s2.other_details),
        "s4_crime_facts": data.section_4_crime_facts.content or "",
        "s5_complaint_reason": data.section_5_complaint_reason.content or "",
        "s6_no_evidence": s6_no,
        "s6_has_evidence": s6_has,
        "s6_evidence_list": _evidence_list_for_doc(s6.evidence_list_text),
        "s7_1_true": s7_1_t,
        "s7_1_false": s7_1_f,
        "s7_2_true": s7_2_t,
        "s7_2_false": s7_2_f,
        "s7_3_true": s7_3_t,
        "s7_3_false": s7_3_f,
        "s8_other": data.section_8_other.content or "",
        "f_accuser_name": footer.accuser_name or "",
        "f_submitter_name": footer.submitter_name or "",
        "f_police": footer.submission_target_police_station or "",
    }
