from fastapi import APIRouter
from ..database import get_pool
from ..models import SettingsIn
from .. import crud

router = APIRouter(prefix="/settings", tags=["settings"])

@router.get("", response_model=SettingsIn)
async def get_settings():
    pool = await get_pool()
    s = await crud.get_settings(pool)
    return SettingsIn(**s)

@router.put("")
async def save_settings(s: SettingsIn):
    pool = await get_pool()
    await crud.save_settings(pool, s.model_dump())
    count = await crud.recalculate_all_overtime(pool)
    return {"ok": True, "updated": count}


@router.post("/recalculate")
async def recalculate_overtime():
    pool = await get_pool()
    count = await crud.recalculate_all_overtime(pool)
    return {"ok": True, "updated": count}