from __future__ import annotations

from datetime import datetime
import uuid

from models.schemas import CategoryRule, ConfidenceLevel


def get_default_rules() -> list[CategoryRule]:
    now = datetime.utcnow()
    return [
        CategoryRule(
            id=str(uuid.uuid4()),
            name="Fuel Vendors",
            target_field="payee",
            contains_text="shell",
            suggested_category="Fuel",
            confidence=ConfidenceLevel.HIGH,
            active=True,
            created_at=now,
            updated_at=now,
        ),
        CategoryRule(
            id=str(uuid.uuid4()),
            name="AWS Services",
            target_field="description",
            contains_text="amazon web services",
            suggested_category="Software",
            confidence=ConfidenceLevel.HIGH,
            active=True,
            created_at=now,
            updated_at=now,
        ),
    ]
