from app.pdf_generator.timeline_pdf.draw.draw_group_header import GROUP_BOX_HEIGHT
from app.pdf_generator.timeline_pdf.layout_constants import (
    CONTENT_BOTTOM_Y,
    CONTENT_TOP_Y,
)
from app.pdf_generator.timeline_pdf.utils import (
    extract_date_group_header_data,
    extract_event_item_data,
)

from .calculate_event_item import calculate_event_item_layout


def layout_pages(timeline_json):
    pages = []
    current_page = {"groups": []}

    current_y = CONTENT_TOP_Y

    items = timeline_json.get("items", [])

    for group in items:
        header_data = extract_date_group_header_data(group)

        page_group = None
        first_event = True

        for event in group["events"]:
            for evidence in event["evidences"]:
                event_data = extract_event_item_data(
                    time=event["time"],
                    evidence=evidence,
                )

                layout = calculate_event_item_layout(
                    title=event_data["title"],
                    description=event_data["description"],
                    evidence_text=event_data["evidence_text"],
                )

                height = layout["height"]

                # -------------------------
                # 첫 event이면 header 포함 검사
                # -------------------------

                required_height = height
                if first_event:
                    required_height += GROUP_BOX_HEIGHT

                if current_y - required_height < CONTENT_BOTTOM_Y:
                    pages.append(current_page)

                    current_page = {"groups": []}
                    current_y = CONTENT_TOP_Y

                    page_group = None
                    first_event = True

                # -------------------------
                # header 출력
                # -------------------------

                if first_event:
                    page_group = {
                        "header": header_data,
                        "events": [],
                    }

                    current_page["groups"].append(page_group)

                    current_y -= GROUP_BOX_HEIGHT

                    first_event = False

                # -------------------------
                # event 추가
                # -------------------------

                page_group["events"].append(
                    {
                        "layout": layout,
                        "time_text": event_data["time_text"],
                        "height": height,
                    }
                )

                current_y -= height

    pages.append(current_page)

    return pages
