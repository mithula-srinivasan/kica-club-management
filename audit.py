import json

from sqlalchemy.orm import Session

from models import AuditLog, Exec


def record_audit(
    db: Session,
    actor: Exec,
    action: str,
    table_name: str,
    record_id: int,
    old_values: dict | None = None,
    new_values: dict | None = None
) -> None:
    db.add(
        AuditLog(
            exec_id=actor.exec_id,
            action=action,
            table_name=table_name,
            record_id=record_id,
            old_values=to_json_safe(old_values),
            new_values=to_json_safe(new_values)
        )
    )


def to_json_safe(values: dict | None) -> dict | None:
    # Dates and Decimal amounts can't go into JSON directly, so store them as exact text
    if values is None:
        return None

    return json.loads(json.dumps(values, default=str))