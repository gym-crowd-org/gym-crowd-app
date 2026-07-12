from fastapi import APIRouter, Depends
from supabase import Client

from app.api.schemas import GymOut
from app.api.services import list_gyms
from app.db.client import get_supabase

router = APIRouter(prefix="/gyms", tags=["gyms"])


@router.get("", response_model=list[GymOut])
def get_gyms(supabase: Client = Depends(get_supabase)) -> list[GymOut]:
    rows = list_gyms(supabase)
    return [GymOut.model_validate(row) for row in rows]
