from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from dependencies import get_db, require_admin
from models import AuditLog, Exec
from schemas import AuditLogResponse


router = APIRouter(
    prefix="/audit-logs",
    tags=["Audit log"],
    dependencies=[Depends(require_admin)]
)


@router.get("/", response_model=list[AuditLogResponse])
def list_audit_logs(
    table_name: str | None = None,
    record_id: int | None = None,
    exec_id: int | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    statement = select(AuditLog)

    if table_name is not None:
        statement = statement.where(AuditLog.table_name == table_name)

    if record_id is not None:
        statement = statement.where(AuditLog.record_id == record_id)

    if exec_id is not None:
        statement = statement.where(AuditLog.exec_id == exec_id)

    statement = statement.order_by(AuditLog.audit_id.desc()).limit(limit)

    entries = db.scalars(statement).all()
    exec_names = dict(db.execute(select(Exec.exec_id, Exec.name)).all())

    return [
        {
            "audit_id": entry.audit_id,
            "exec_id": entry.exec_id,
            "exec_name": exec_names[entry.exec_id],
            "action": entry.action,
            "table_name": entry.table_name,
            "record_id": entry.record_id,
            "old_values": entry.old_values,
            "new_values": entry.new_values,
            "created_at": entry.created_at
        }
        for entry in entries
    ]