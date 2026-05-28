from typing import Optional
from datetime import date, datetime, timedelta, timezone
from uuid import UUID
import asyncpg

CHINA_TZ = timezone(timedelta(hours=8))


def local_now(clock=None) -> datetime:
    now = clock() if clock else datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return now.astimezone(CHINA_TZ).replace(tzinfo=None)


def local_today(clock=None) -> date:
    return local_now(clock).date()


def month_prefix(year: int, month: int) -> str:
    return f"{year}-{month:02d}"


def db_date(value: date | str) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)


def db_datetime(value: datetime | str | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if value.tzinfo is None:
        return value
    return value.astimezone(CHINA_TZ).replace(tzinfo=None)


def db_uuid(value: UUID | str) -> UUID:
    if isinstance(value, UUID):
        return value
    return UUID(value)


def round_to_half(minutes: int) -> float:
    return round(minutes / 30) * 0.5

def calc_work_minutes(clock_in: datetime, clock_out: datetime, lunch_minutes: int) -> int:
    diff = (clock_out - clock_in).total_seconds() / 60
    return max(0, int(diff - lunch_minutes))

def calc_total_hours(work_minutes: int) -> float:
    return round_to_half(work_minutes)

def calc_overtime_hours(
    clock_in: datetime,
    clock_out: datetime | None,
    pre_hours: float,
    overtime_start: str,
) -> float:
    """Calculate overtime: morning bonus (before 9am) + evening overtime (after overtime_start)."""
    if clock_out is None:
        return 0.0

    # Morning bonus: clocked in before 9am
    morning_bonus = float(pre_hours) if clock_in.hour < 9 else 0.0

    # Evening overtime: time worked after overtime_start (anchored to clock_in date)
    ost_hour, ost_minute = map(int, overtime_start.split(":"))
    ost_dt = clock_in.replace(hour=ost_hour, minute=ost_minute, second=0, microsecond=0)
    evening_minutes = int((clock_out - ost_dt).total_seconds() / 60)
    evening_overtime = max(0.0, round_to_half(max(0, evening_minutes)))

    return morning_bonus + evening_overtime


def default_clock_in_time(current: datetime) -> datetime:
    return current.replace(hour=8, minute=0, second=0, microsecond=0)


def build_update_statement(table: str, updates: dict) -> str:
    if not updates:
        raise ValueError("updates must not be empty")
    sets = ", ".join([f"{key} = ${index}" for index, key in enumerate(updates.keys(), start=1)])
    return f"UPDATE {table} SET {sets}, updated_at = NOW() WHERE id = ${len(updates) + 1}"


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
            db_date(record["date"]), db_datetime(record["clock_in"]), db_datetime(record.get("clock_out")),
            record.get("total_hours"), record.get("overtime_hours"), record.get("note")
        )

async def update_record(pool: asyncpg.Pool, id: str, updates: dict):
    async with pool.acquire() as conn:
        updates = updates.copy()
        if "date" in updates:
            updates["date"] = db_date(updates["date"])
        if "clock_in" in updates:
            updates["clock_in"] = db_datetime(updates["clock_in"])
        if "clock_out" in updates:
            updates["clock_out"] = db_datetime(updates["clock_out"])
        vals = list(updates.values())
        await conn.execute(
            build_update_statement("work_records", updates),
            *vals, db_uuid(id)
        )

async def delete_record(pool: asyncpg.Pool, id: str):
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM work_records WHERE id = $1", db_uuid(id))

async def get_settings(pool: asyncpg.Pool) -> dict:
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM settings WHERE id = 1")
        if not row:
            return {"standard_hours": 8.0, "lunch_break_minutes": 60, "pre_hours": 1.0, "overtime_start": "18:00"}
        return {
            "standard_hours": float(row["standard_hours"]),
            "lunch_break_minutes": int(row["lunch_break_minutes"]),
            "pre_hours": float(row["pre_hours"]),
            "overtime_start": str(row["overtime_start"]),
        }

async def save_settings(pool: asyncpg.Pool, s: dict):
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO settings (id, standard_hours, lunch_break_minutes, pre_hours, overtime_start)
               VALUES (1, $1, $2, $3, $4)
               ON CONFLICT (id) DO UPDATE SET
               standard_hours = $1, lunch_break_minutes = $2, pre_hours = $3, overtime_start = $4""",
            s["standard_hours"], s["lunch_break_minutes"], s["pre_hours"], s["overtime_start"]
        )

async def recalculate_all_overtime(pool: asyncpg.Pool) -> int:
    """Recalculate overtime_hours for all completed records using current settings."""
    settings = await get_settings(pool)
    async with pool.acquire() as conn:
        records = await conn.fetch(
            "SELECT * FROM work_records WHERE clock_out IS NOT NULL"
        )
        count = 0
        for r in records:
            oh = calc_overtime_hours(
                r["clock_in"], r["clock_out"],
                settings["pre_hours"], settings["overtime_start"],
            )
            await conn.execute(
                "UPDATE work_records SET overtime_hours = $1, updated_at = NOW() WHERE id = $2",
                oh, r["id"],
            )
            count += 1
        return count


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
            oh = calc_overtime_hours(clock_in, clock_out, settings["pre_hours"], settings["overtime_start"])
            total_h += th
            overtime_h += oh
        return {"work_days": work_days, "total_hours": round(total_h, 2), "overtime_hours": round(overtime_h, 2)}
