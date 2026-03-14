from datetime import datetime


def extract_date_group_header_data(date_group: dict) -> dict:
    """
    date group(dict)에서 draw_group_header에 필요한 값 추출.

    Returns:
        date_text: "YYYY년 MM월 DD일"
        total_count: 해당 date의 모든 events의 모든 evidences 개수 합
        evidence_number: date에서 '-' 제거 (e.g. "2026-02-12" -> "20260212")
    """
    date_str = date_group.get("date", "")

    # date_text
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        date_text = dt.strftime("%Y년 %m월 %d일")
    except (ValueError, TypeError):
        date_text = date_str or "-"

    # total_count: 모든 events의 evidences length 합
    total_count = 0
    for evt in date_group.get("events", []):
        total_count += len(evt.get("evidences", []))

    # evidence_number: date에서 '-' 제거
    evidence_number = date_str.replace("-", "") if date_str else ""

    return {
        "date_text": date_text,
        "total_count": total_count,
        "evidence_number": evidence_number,
    }
