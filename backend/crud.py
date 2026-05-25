from typing import Optional
from datetime import date, datetime
import math
import asyncpg


def month_prefix(year: int, month: int) -> str:
    return f"{year}-{month:02d}"


def db_date(value: date | str) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)


def round_to_half(minutes: int) -> float:
    return round(minutes / 30) * 0.5

def calc_work_minutes(clock_in: datetime, clock_out: datetime, lunch_minutes: int) -> int:
    diff = (clock_out - clock_in).total_seconds() / 60
    return max(0, int(diff - lunch_minutes))

def calc_total_hours(work_minutes: int) -> float:
    return round_to_half(work_minutes)

def calc_overtime_hours(clock_in: datetime, total_hours: float, standard_hours: float, pre_hours: float) -> float:
    pre_overtime = pre_hours if clock_in.hour < 9 else 0.0
    return max(0.0, total_hours - standard_hours + pre_overtime)

async def get_today_record(pool: asyncpg.Pool, today: date | str) -> Optional[asyncpg.Record]:
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            "SELECT * FROM work_records WHERE date = $1", db_date(today)
        )

async def get_records_by_month(pool: asyncpg.Pool, year: int, month: int):
    async with pool.acquire() as conn:
        prefix = month_prefix(year, month)
        return await conn.fetch(
            "SELECT * FROM work_records WHERE date::text LIKE $1 || '%' ORDER BY date",
            prefix
        )


async def get_all_records(pool: asyncpg.Pool):
    async with pool.acquire() as conn:
        return await conn.fetch("SELECT * FROM work_records ORDER BY date")


async def create_record(pool: asyncpg.Pool, record: dict) -> str:
    async with pool.acquire() as conn:
        return await conn.fetchval(
            """INSERT INTO work_records (date, clock_in, clock_out, total_hours, overtime_hours, note)
               VALUES ($1, $2, $3, $4, $5, $6) RETURNING id""",
            db_date(record["date"]), record["clock_in"], record.get("clock_out"),
            record.get("total_hours"), record.get("overtime_hours"), record.get("note")
        )

async def update_record(pool: asyncpg.Pool, id: str, updates: dict):
    async with pool.acquire() as conn:
        updates = updates.copy()
        if "date" in updates:
            updates["date"] = db_date(updates["date"])
        sets = ", ".join([f"{k} = ${i+2}" for i, k in enumerate(updates.keys())])
        vals = list(updates.values())
        await conn.execute(
            f"UPDATE work_records SET {sets}, updated_at = NOW() WHERE id = ${len(vals)+1}",
            *vals, id
        )

async def delete_record(pool: asyncpg.Pool, id: str):
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM work_records WHERE id = $1", id)

async def get_settings(pool: asyncpg.Pool) -> dict:
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM settings WHERE id = 1")
        if not row:
            return {"standard_hours": 8.0, "lunch_break_minutes": 60, "pre_hours": 1.0}
        return dict(row)

async def save_settings(pool: asyncpg.Pool, s: dict):
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO settings (id, standard_hours, lunch_break_minutes, pre_hours)
               VALUES (1, $1, $2, $3)
               ON CONFLICT (id) DO UPDATE SET standard_hours = $1, lunch_break_minutes = $2, pre_hours = $3""",
            s["standard_hours"], s["lunch_break_minutes"], s["pre_hours"]
        )

async def get_stats(pool: asyncpg.Pool, year: int, month: int, settings: dict):
    async with pool.acquire() as conn:
        prefix = month_prefix(year, month)
        records = await conn.fetch(
            "SELECT * FROM work_records WHERE date::text LIKE $1 || '%' AND clock_out IS NOT NULL",
            prefix
        )
        work_days = len(records)
        total_h = 0.0
        overtime_h = 0.0
        for r in records:
            clock_in: datetime = r["clock_in"]
            clock_out: datetime = r["clock_out"]
            m = calc_work_minutes(clock_in, clock_out, settings["lunch_break_minutes"])
            th = calc_total_hours(m)
            oh = calc_overtime_hours(clock_in, th, settings["standard_hours"], settings["pre_hours"])
            total_h += th
            overtime_h += oh
        return {"work_days": work_days, "total_hours": round(total_h, 2), "overtime_hours": round(overtime_h, 2)}
