from fastapi import APIRouter

from countries import COUNTRY_CHOICES

# Public (no login): the Join form needs the list too
router = APIRouter(
    prefix="/countries",
    tags=["Countries"]
)


@router.get("/")
def list_countries():
    return COUNTRY_CHOICES