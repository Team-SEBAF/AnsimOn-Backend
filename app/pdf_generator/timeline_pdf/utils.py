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


def extract_event_item_data(time: str, evidence: dict) -> dict:
    """
    time과 evidence(dict)에서 draw_event_item에 필요한 값 추출.

    Args:
        time: event의 time
        evidence: evidence 1개 (title, description, evidences_numstring_s3_key_list 포함)

    Returns:
        time_text: time
        title: evidence의 title (없으면 "-")
        description: evidence의 description (없으면 "-")
        evidence_text: evidences_numstring_s3_key_list keys를 ', '로 연결
    """
    title = evidence.get("title", "-")
    description = evidence.get("description", "-")

    numstring_map = evidence.get("evidences_numstring_s3_key_list") or {}
    evidence_text = ", ".join(numstring_map.keys())

    return {
        "time_text": time,
        "title": title,
        "description": description,
        "evidence_text": "증거 번호 " + evidence_text,
    }
