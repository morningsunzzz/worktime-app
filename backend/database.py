import os
import asyncpg

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://worktime:worktime123@localhost:5432/worktime"
)

pool: asyncpg.Pool | None = None

async def get_pool() -> asyncpg.Pool:
    global pool
    if pool is None:
        pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
    return pool

async def close_pool():
    global pool
    if pool:
        await pool.close()
        pool = None


async def init_db():
    p = await get_pool()
    async with p.acquire() as conn:
        await conn.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS work_records (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                date DATE NOT NULL UNIQUE,
                clock_in TIMESTAMP NOT NULL,
                clock_out TIMESTAMP,
                total_hours DECIMAL(4,2),
                overtime_hours DECIMAL(4,2),
                note TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
            """
        )
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY DEFAULT 1,
                standard_hours DECIMAL(4,2) DEFAULT 8,
                lunch_break_minutes INTEGER DEFAULT 60,
                pre_hours DECIMAL(4,2) DEFAULT 1,
                overtime_start VARCHAR(5) DEFAULT '18:00'
            )
            """
        )
        # Migration: add overtime_start column to existing databases
        await conn.execute(
            """
            ALTER TABLE settings ADD COLUMN IF NOT EXISTS overtime_start VARCHAR(5) DEFAULT '18:00'
            """
        )
        await conn.execute(
            """
            INSERT INTO settings (id, standard_hours, lunch_break_minutes, pre_hours, overtime_start)
            VALUES (1, 8, 60, 1, '18:00')
            ON CONFLICT (id) DO NOTHING
            """
        )
