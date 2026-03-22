from app.pdf_generator.timeline_pdf.draw.draw_event_item import draw_event_item
from app.pdf_generator.timeline_pdf.draw.draw_group_header import draw_group_header
from app.pdf_generator.timeline_pdf.layout_constants import CONTENT_TOP_Y


def render_pages(c, page):
    timeline_points = []

    y = CONTENT_TOP_Y

    for group in page["groups"]:
        center_y, end_y = draw_group_header(
            c,
            start_y=y,
            date_text=group["header"]["date_text"],
            total_count=group["header"]["total_count"],
            evidence_number=group["header"]["evidence_number"],
        )

        timeline_points.append(
            {
                "y": center_y,
                "type": "group",
            }
        )

        y = end_y

        for event in group["events"]:
            center_y, end_y = draw_event_item(
                c,
                start_y=y,
                time_text=event["time_text"],
                layout=event["layout"],
                on_border=True,
            )

            timeline_points.append(
                {
                    "y": center_y,
                    "type": "event",
                }
            )

            y = end_y

    return timeline_points
