from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class WorkRecordIn(BaseModel):
    date: str
    clock_in: datetime
    clock_out: Optional[datetime] = None
    total_hours: Optional[float] = None
    overtime_hours: Optional[float] = None
    note: Optional[str] = None

class WorkRecordOut(BaseModel):
    id: str
    date: str
    clock_in: datetime
    clock_out: Optional[datetime]
    total_hours: Optional[float]
    overtime_hours: Optional[float]
    note: Optional[str]
    created_at: datetime
    updated_at: datetime

class SettingsIn(BaseModel):
    standard_hours: float = 8.0
    lunch_break_minutes: int = 60
    pre_hours: float = 1.0
    overtime_start: str = "18:00"

class StatsOut(BaseModel):
    work_days: int
    total_hours: float
    overtime_hours: float