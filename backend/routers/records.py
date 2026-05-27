from fastapi import APIRouter, HTTPException
from datetime import datetime, date
import math

from ..database import get_pool
from ..models import WorkRecordIn, WorkRecordOut, StatsOut
from .. import crud

router = APIRouter(prefix="/records", tags=["records"])

def _record_from_row(row) -> dict:
    return {
        "id": str(row["id"]),
        "date": str(row["date"]),
        "clock_in": row["clock_in"],
        "clock_out": row["clock_out"],
        "total_hours": float(row["total_hours"]) if row["total_hours"] else None,
        "overtime_hours": float(row["overtime_hours"]) if row["overtime_hours"] else None,
        "note": row["note"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }

@router.get("", response_model=list[WorkRecordOut])
async def list_records(year: int, month: int):
    pool = await get_pool()
    rows = await crud.get_records_by_month(pool, year, month)
    return [_record_from_row(r) for r in rows]


@router.get("/all", response_model=list[WorkRecordOut])
async def list_all_records():
    pool = await get_pool()
    rows = await crud.get_all_records(pool)
    return [_record_from_row(r) for r in rows]

@router.get("/today", response_model=WorkRecordOut | None)
async def get_today():
    pool = await get_pool()
    today = crud.local_today()
    row = await crud.get_today_record(pool, today)
    return _record_from_row(row) if row else None

@router.post("/clock-in", response_model=WorkRecordOut)
async def clock_in():
    pool = await get_pool()
    today = crud.local_today()
    existing = await crud.get_today_record(pool, today)
    if existing:
        return _record_from_row(existing)
    clock_in_time = crud.default_clock_in_time(crud.local_now())
    settings = await crud.get_settings(pool)
    th = 0.0
    oh = crud.calc_overtime_hours(clock_in_time, th, settings["standard_hours"], settings["pre_hours"])
    record_id = await crud.create_record(pool, {
        "date": today, "clock_in": clock_in_time,
        "total_hours": th, "overtime_hours": oh
    })
    row = await pool.fetchrow("SELECT * FROM work_records WHERE id = $1", crud.db_uuid(record_id))
    return _record_from_row(row)

@router.post("/clock-out", response_model=WorkRecordOut)
async def clock_out():
    pool = await get_pool()
    today = crud.local_today()
    existing = await crud.get_today_record(pool, today)
    if not existing:
        raise HTTPException(404, "No clock-in record for today")
    if existing["clock_out"]:
        raise HTTPException(400, "Already clocked out")
    clock_out_time = crud.local_now()
    settings = await crud.get_settings(pool)
    clock_in_dt: datetime = existing["clock_in"]
    work_min = crud.calc_work_minutes(clock_in_dt, clock_out_time, settings["lunch_break_minutes"])
    total_h = crud.calc_total_hours(work_min)
    overtime = crud.calc_overtime_hours(clock_in_dt, total_h, settings["standard_hours"], settings["pre_hours"])
    await crud.update_record(pool, str(existing["id"]), {
        "clock_out": clock_out_time, "total_hours": total_h, "overtime_hours": overtime
    })
    row = await pool.fetchrow("SELECT * FROM work_records WHERE id = $1", existing["id"])
    return _record_from_row(row)

@router.post("/add", response_model=WorkRecordOut)
async def add_record(r: WorkRecordIn):
    pool = await get_pool()
    settings = await crud.get_settings(pool)
    clock_in_dt = crud.db_datetime(r.clock_in)
    if r.clock_out:
        clock_out_dt = crud.db_datetime(r.clock_out)
        work_min = crud.calc_work_minutes(clock_in_dt, clock_out_dt, settings["lunch_break_minutes"])
        total_h = crud.calc_total_hours(work_min)
        overtime = crud.calc_overtime_hours(clock_in_dt, total_h, settings["standard_hours"], settings["pre_hours"])
    else:
        total_h = None
        overtime = None
        clock_out_dt = None
    record_id = await crud.create_record(pool, {
        "date": r.date, "clock_in": clock_in_dt, "clock_out": clock_out_dt,
        "total_hours": total_h, "overtime_hours": overtime, "note": r.note
    })
    row = await pool.fetchrow("SELECT * FROM work_records WHERE id = $1", crud.db_uuid(record_id))
    return _record_from_row(row)

@router.put("/{id}", response_model=WorkRecordOut)
async def edit_record(id: str, r: WorkRecordIn):
    pool = await get_pool()
    settings = await crud.get_settings(pool)
    clock_in_dt = crud.db_datetime(r.clock_in)
    if r.clock_out:
        clock_out_dt = crud.db_datetime(r.clock_out)
        work_min = crud.calc_work_minutes(clock_in_dt, clock_out_dt, settings["lunch_break_minutes"])
        total_h = crud.calc_total_hours(work_min)
        overtime = crud.calc_overtime_hours(clock_in_dt, total_h, settings["standard_hours"], settings["pre_hours"])
    else:
        clock_out_dt = None
        total_h = None
        overtime = None
    await crud.update_record(pool, id, {
        "clock_in": clock_in_dt, "clock_out": clock_out_dt,
        "total_hours": total_h, "overtime_hours": overtime, "note": r.note
    })
    row = await pool.fetchrow("SELECT * FROM work_records WHERE id = $1", crud.db_uuid(id))
    return _record_from_row(row)

@router.delete("/{id}")
async def delete_record(id: str):
    pool = await get_pool()
    await crud.delete_record(pool, id)
    return {"ok": True}

@router.get("/stats", response_model=StatsOut)
async def get_stats(year: int, month: int):
    pool = await get_pool()
    settings = await crud.get_settings(pool)
    return await crud.get_stats(pool, year, month, settings)
