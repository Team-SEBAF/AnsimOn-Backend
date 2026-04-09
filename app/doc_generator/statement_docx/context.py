from __future__ import annotations

from app.domain.document.schemas.form_data import StatementFormData


def build_statement_context(data: StatementFormData) -> dict[str, str]:
    return {
        "damage_facts_statement": data.damage_facts_statement or "",
        "declarant_name": data.declarant_name or "",
        "police": data.submission_target_police_station or "",
    }
