from __future__ import annotations

from app.domain.document.schemas.form_data import ComplaintFormData

_REP_UNCHECKED_FIELD = "            "


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
    """True: 칠한 사각(■), False: 빈 사각(□)."""
    return "■" if v else "□"


def build_complaint_context(data: ComplaintFormData) -> dict[str, str]:
    s1 = data.section_1_complainant
    s2 = data.section_2_accused
    c1 = s1.contact
    c2 = s2.contact
    r = s1.representative

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
    }
