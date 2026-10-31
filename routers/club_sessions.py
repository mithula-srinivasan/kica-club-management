from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from audit import record_audit
from dependencies import get_current_exec, get_db
from models import Attendance, ClubSession, Exec, Player
from schemas import (
    AttendanceUpdate,
    SessionCreate,
    SessionDetailResponse,
    SessionResponse,
)


router = APIRouter(
    prefix="/sessions",
    tags=["Sessions and attendance"],
    dependencies=[Depends(get_current_exec)]
)


def get_session_or_404(db: Session, session_id: int) -> ClubSession:
    club_session = db.get(ClubSession, session_id)

    if club_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    return club_session


def session_detail(db: Session, club_session: ClubSession) -> dict:
    present_players = db.scalars(
        select(Player)
        .join(Attendance, Attendance.player_id == Player.player_id)
        .where(
            Attendance.session_id == club_session.session_id,
            Attendance.is_present.is_(True)
        )
        .order_by(Player.name)
    ).all()

    return {
        "session_id": club_session.session_id,
        "session_date": club_session.session_date,
        "present_players": present_players
    }


@router.get("/", response_model=list[SessionResponse])
def list_sessions(db: Session = Depends(get_db)):
    present_count = func.count(Attendance.attendance_id)

    rows = db.execute(
        select(ClubSession, present_count)
        .outerjoin(
            Attendance,
            and_(
                Attendance.session_id == ClubSession.session_id,
                Attendance.is_present.is_(True)
            )
        )
        .group_by(ClubSession.session_id)
        .order_by(ClubSession.session_date.desc())
    ).all()

    return [
        {
            "session_id": club_session.session_id,
            "session_date": club_session.session_date,
            "present_count": count
        }
        for club_session, count in rows
    ]


@router.post("/", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(
    session_data: SessionCreate,
    current_exec: Exec = Depends(get_current_exec),
    db: Session = Depends(get_db)
):
    club_session = ClubSession(session_date=session_data.session_date)
    db.add(club_session)

    try:
        db.flush()

        record_audit(
            db, current_exec, "CREATE", "club_sessions", club_session.session_id,
            new_values={"session_date": session_data.session_date}
        )

        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A session already exists on this date"
        )

    return {
        "session_id": club_session.session_id,
        "session_date": club_session.session_date,
        "present_count": 0
    }


@router.get("/{session_id}", response_model=SessionDetailResponse)
def get_session(
    session_id: int,
    db: Session = Depends(get_db)
):
    club_session = get_session_or_404(db, session_id)

    return session_detail(db, club_session)


@router.put("/{session_id}/attendance", response_model=SessionDetailResponse)
def set_attendance(
    session_id: int,
    attendance: AttendanceUpdate,
    current_exec: Exec = Depends(get_current_exec),
    db: Session = Depends(get_db)
):
    club_session = get_session_or_404(db, session_id)
    new_ids = set(attendance.player_ids)

    # Every player in the list must exist
    found_ids = set(
        db.scalars(select(Player.player_id).where(Player.player_id.in_(new_ids)))
    )
    missing_ids = new_ids - found_ids

    if missing_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Players not found: {sorted(missing_ids)}"
        )

    # Everyone who has ever been marked for this session, present or not
    existing_rows = {
        row.player_id: row
        for row in db.scalars(
            select(Attendance).where(Attendance.session_id == session_id)
        )
    }
    old_ids = {player_id for player_id, row in existing_rows.items() if row.is_present}

    # Newly present players
    for player_id in new_ids - old_ids:
        row = existing_rows.get(player_id)

        if row is None:
            db.add(
                Attendance(
                    session_id=session_id,
                    player_id=player_id,
                    is_present=True,
                    marked_by_exec_id=current_exec.exec_id
                )
            )
        else:
            row.is_present = True
            row.marked_by_exec_id = current_exec.exec_id

    # Players removed from the list
    for player_id in old_ids - new_ids:
        row = existing_rows[player_id]
        row.is_present = False
        row.marked_by_exec_id = current_exec.exec_id

    if new_ids != old_ids:
        record_audit(
            db, current_exec, "UPDATE", "club_sessions", session_id,
            old_values={"present_player_ids": sorted(old_ids)},
            new_values={"present_player_ids": sorted(new_ids)}
        )

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Attendance was changed by someone else at the same time. Please try again."
        )

    return session_detail(db, club_session)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    session_id: int,
    current_exec: Exec = Depends(get_current_exec),
    db: Session = Depends(get_db)
):
    club_session = get_session_or_404(db, session_id)

    present_count = db.scalar(
        select(func.count())
        .select_from(Attendance)
        .where(
            Attendance.session_id == session_id,
            Attendance.is_present.is_(True)
        )
    )

    if present_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Remove all attendance before deleting this session"
        )

    record_audit(
        db, current_exec, "DELETE", "club_sessions", session_id,
        old_values={"session_date": club_session.session_date}
    )

    # Remove leftover "absent" rows first, because they point to this session
    db.execute(delete(Attendance).where(Attendance.session_id == session_id))
    db.delete(club_session)
    db.commit()