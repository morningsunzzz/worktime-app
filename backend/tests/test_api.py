import pytest
from datetime import datetime, date, timedelta, timezone

CHINA_TZ = timezone(timedelta(hours=8))
VALID_UUID = "550e8400-e29b-41d4-a716-446655440000"


def _row(**kw):
    """Helper: build a mock record row with defaults."""
    defaults = {
        "id": VALID_UUID,
        "date": "2026-05-27",
        "clock_in": datetime(2026, 5, 27, 8, 0),
        "clock_out": None,
        "total_hours": None,
        "overtime_hours": None,
        "note": None,
        "created_at": datetime(2026, 5, 27, 8, 0),
        "updated_at": datetime(2026, 5, 27, 8, 0),
    }
    defaults.update(kw)
    return defaults


def _settings(**kw):
    defaults = {"standard_hours": 8.0, "lunch_break_minutes": 60, "pre_hours": 1.0, "overtime_start": "18:00"}
    defaults.update(kw)
    return defaults


# ── Health ──────────────────────────────────────────────────────────


class TestHealth:
    async def test_health_returns_ok(self, client):
        res = await client.get("/api/health")
        assert res.status_code == 200
        assert res.json() == {"status": "ok"}


# ── Settings ────────────────────────────────────────────────────────


class TestSettings:
    async def test_get_settings_defaults(self, client):
        client._mock_conn.fetchrow.return_value = _settings()

        res = await client.get("/api/settings")
        assert res.status_code == 200
        data = res.json()
        assert data["standard_hours"] == 8.0
        assert data["lunch_break_minutes"] == 60
        assert data["pre_hours"] == 1.0

    async def test_get_settings_custom(self, client):
        client._mock_conn.fetchrow.return_value = _settings(
            standard_hours=7.5, lunch_break_minutes=30, pre_hours=2.0
        )

        res = await client.get("/api/settings")
        assert res.status_code == 200
        data = res.json()
        assert data["standard_hours"] == 7.5
        assert data["lunch_break_minutes"] == 30
        assert data["pre_hours"] == 2.0

    async def test_save_settings_ok(self, client):
        res = await client.put(
            "/api/settings",
            json={"standard_hours": 9.0, "lunch_break_minutes": 45, "pre_hours": 1.5},
        )
        assert res.status_code == 200
        assert res.json()["ok"] is True
        assert "updated" in res.json()

    async def test_save_settings_accepts_zero_lunch(self, client):
        res = await client.put(
            "/api/settings",
            json={"standard_hours": 8.0, "lunch_break_minutes": 0, "pre_hours": 1.0},
        )
        assert res.status_code == 200
        assert res.json()["ok"] is True

    async def test_save_settings_with_defaults_for_missing(self, client):
        """所有字段都有默认值，缺失字段使用默认值，返回 200"""
        res = await client.put(
            "/api/settings",
            json={"standard_hours": 8.0},
        )
        assert res.status_code == 200

    async def test_save_settings_missing_all_required(self, client):
        """所有字段都有默认值，空 JSON 也通过"""
        res = await client.put("/api/settings", json={})
        assert res.status_code == 200


# ── Clock-In ────────────────────────────────────────────────────────


class TestClockIn:
    async def test_first_clock_in_creates_record(self, client):
        """当天无记录时，打卡创建新记录"""
        client._mock_conn.fetchrow.return_value = None
        client._mock_conn.fetchval.return_value = VALID_UUID

        # After create, route calls pool.fetchrow directly
        client._mock_pool.fetchrow.return_value = _row(
            id=VALID_UUID, clock_in=datetime(2026, 5, 27, 8, 0), total_hours=0.0,
            overtime_hours=0.0,
        )

        res = await client.post("/api/records/clock-in")
        assert res.status_code == 200
        data = res.json()
        assert data["id"] == VALID_UUID
        assert data["clock_in"] is not None
        assert data["clock_out"] is None
        # 0.0 is falsy → API serializes as null
        assert data["total_hours"] is None

    async def test_dual_clock_in_returns_existing(self, client):
        """已有打卡时再次打卡返回已有记录"""
        existing = _row(clock_out=None)
        client._mock_conn.fetchrow.return_value = existing

        res = await client.post("/api/records/clock-in")
        assert res.status_code == 200
        assert res.json()["id"] == VALID_UUID

    async def test_clock_in_next_day_creates_new(self, client):
        """新一天重新打卡"""
        client._mock_conn.fetchrow.return_value = None
        client._mock_conn.fetchval.return_value = VALID_UUID
        client._mock_pool.fetchrow.return_value = _row(
            id=VALID_UUID, clock_in=datetime(2026, 5, 27, 8, 0), total_hours=0.0,
            overtime_hours=0.0,
        )

        res = await client.post("/api/records/clock-in")
        assert res.status_code == 200
        assert res.json()["id"] == VALID_UUID


# ── Clock-Out ───────────────────────────────────────────────────────


class TestClockOut:
    async def test_clock_out_normal_day(self, client):
        """标准下班：8:00-18:00，午休1h，工时9h，加班1h"""
        clock_in = datetime(2026, 5, 27, 8, 0)
        clock_out_time = datetime(2026, 5, 27, 18, 0)

        # First fetchrow: get_today_record → existing
        # Second fetchrow (inside get_settings): get settings
        existing = _row(id=VALID_UUID, clock_in=clock_in, clock_out=None)
        client._mock_conn.fetchrow.side_effect = [existing, _settings()]

        # After update, pool.fetchrow called directly
        client._mock_pool.fetchrow.return_value = _row(
            id=VALID_UUID, clock_in=clock_in, clock_out=clock_out_time,
            total_hours=9.0, overtime_hours=1.0,
        )

        res = await client.post("/api/records/clock-out")
        assert res.status_code == 200
        data = res.json()
        assert data["clock_out"] is not None
        assert data["total_hours"] == 9.0
        assert data["overtime_hours"] == 1.0

    async def test_clock_out_without_clock_in_returns_404(self, client):
        client._mock_conn.fetchrow.return_value = None

        res = await client.post("/api/records/clock-out")
        assert res.status_code == 404
        assert "No clock-in" in res.json()["detail"]

    async def test_clock_out_already_done_returns_400(self, client):
        client._mock_conn.fetchrow.return_value = _row(
            clock_out=datetime(2026, 5, 27, 18, 0)
        )

        res = await client.post("/api/records/clock-out")
        assert res.status_code == 400
        assert "Already clocked out" in res.json()["detail"]

    async def test_clock_out_long_day(self, client):
        """加班到22:00：14h-1h午休=13h工时，加班=13-8=5h"""
        clock_in = datetime(2026, 5, 27, 8, 0)
        clock_out_time = datetime(2026, 5, 27, 22, 0)

        existing = _row(id=VALID_UUID, clock_in=clock_in, clock_out=None)
        client._mock_conn.fetchrow.side_effect = [existing, _settings()]

        client._mock_pool.fetchrow.return_value = _row(
            id=VALID_UUID, clock_in=clock_in, clock_out=clock_out_time,
            total_hours=13.0, overtime_hours=5.0,
        )

        res = await client.post("/api/records/clock-out")
        assert res.status_code == 200
        data = res.json()
        assert data["overtime_hours"] == 5.0


# ── Today Record ────────────────────────────────────────────────────


class TestTodayRecord:
    async def test_get_today_when_exists(self, client):
        client._mock_conn.fetchrow.return_value = _row()

        res = await client.get("/api/records/today")
        assert res.status_code == 200
        assert res.json()["date"] == "2026-05-27"

    async def test_get_today_when_not_exists(self, client):
        client._mock_conn.fetchrow.return_value = None

        res = await client.get("/api/records/today")
        assert res.status_code == 200
        assert res.text == "null"


# ── Records List ────────────────────────────────────────────────────


class TestListRecords:
    async def test_list_by_month_empty(self, client):
        client._mock_conn.fetch.return_value = []

        res = await client.get("/api/records?year=2026&month=5")
        assert res.status_code == 200
        assert res.json() == []

    async def test_list_by_month_has_records(self, client):
        r1 = _row(id=VALID_UUID, date="2026-05-01")
        r2 = _row(id="550e8400-e29b-41d4-a716-446655440001", date="2026-05-15",
                   clock_out=datetime(2026, 5, 15, 18, 0))
        client._mock_conn.fetch.return_value = [r1, r2]

        res = await client.get("/api/records?year=2026&month=5")
        assert res.status_code == 200
        assert len(res.json()) == 2

    async def test_list_by_month_missing_params(self, client):
        res = await client.get("/api/records")
        assert res.status_code == 422

    async def test_list_all_records(self, client):
        client._mock_conn.fetch.return_value = [_row(id=VALID_UUID), _row(id="550e8400-e29b-41d4-a716-446655440001")]

        res = await client.get("/api/records/all")
        assert res.status_code == 200
        assert len(res.json()) == 2


# ── Add Record ──────────────────────────────────────────────────────


class TestAddRecord:
    async def test_add_complete_record(self, client):
        """手动添加完整记录"""
        clock_in = datetime(2026, 5, 26, 9, 0)
        clock_out = datetime(2026, 5, 26, 18, 0)

        client._mock_conn.fetchrow.side_effect = [_settings()]
        client._mock_conn.fetchval.return_value = VALID_UUID
        client._mock_pool.fetchrow.return_value = _row(
            id=VALID_UUID, date="2026-05-26",
            clock_in=clock_in, clock_out=clock_out,
            total_hours=8.0, overtime_hours=0.0, note="补卡",
        )

        res = await client.post(
            "/api/records/add",
            json={
                "date": "2026-05-26",
                "clock_in": "2026-05-26T09:00:00",
                "clock_out": "2026-05-26T18:00:00",
                "note": "补卡",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["id"] == VALID_UUID
        assert data["note"] == "补卡"

    async def test_add_record_clock_in_only(self, client):
        """只添加上班时间"""
        client._mock_conn.fetchrow.side_effect = [_settings()]
        client._mock_conn.fetchval.return_value = VALID_UUID
        client._mock_pool.fetchrow.return_value = _row(
            id=VALID_UUID, date="2026-05-26",
            clock_in=datetime(2026, 5, 26, 8, 0),
            clock_out=None, total_hours=None, overtime_hours=None,
        )

        res = await client.post(
            "/api/records/add",
            json={
                "date": "2026-05-26",
                "clock_in": "2026-05-26T08:00:00",
                "clock_out": None,
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["clock_out"] is None
        assert data["total_hours"] is None

    async def test_add_record_missing_date(self, client):
        res = await client.post(
            "/api/records/add",
            json={"clock_in": "2026-05-26T08:00:00"},
        )
        assert res.status_code == 422


# ── Edit Record ─────────────────────────────────────────────────────


class TestEditRecord:
    async def test_edit_record_changes_times(self, client):
        """编辑记录：修改上下班时间"""
        clock_in = datetime(2026, 5, 26, 7, 0)
        clock_out = datetime(2026, 5, 26, 19, 0)

        client._mock_conn.fetchrow.side_effect = [_settings()]
        client._mock_pool.fetchrow.return_value = _row(
            id=VALID_UUID, date="2026-05-26",
            clock_in=clock_in, clock_out=clock_out,
            total_hours=11.0, overtime_hours=2.0,
        )

        res = await client.put(
            f"/api/records/{VALID_UUID}",
            json={
                "date": "2026-05-26",
                "clock_in": "2026-05-26T07:00:00",
                "clock_out": "2026-05-26T19:00:00",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["id"] == VALID_UUID
        assert data["total_hours"] == 11.0

    async def test_edit_record_remove_clock_out(self, client):
        """去掉下班时间，恢复为上班中"""
        clock_in = datetime(2026, 5, 26, 9, 0)

        client._mock_conn.fetchrow.side_effect = [_settings()]
        client._mock_pool.fetchrow.return_value = _row(
            id=VALID_UUID, date="2026-05-26",
            clock_in=clock_in, clock_out=None,
            total_hours=None, overtime_hours=None,
        )

        res = await client.put(
            f"/api/records/{VALID_UUID}",
            json={
                "date": "2026-05-26",
                "clock_in": "2026-05-26T09:00:00",
                "clock_out": None,
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["clock_out"] is None


# ── Delete Record ───────────────────────────────────────────────────


class TestDeleteRecord:
    async def test_delete_record_returns_ok(self, client):
        res = await client.delete(f"/api/records/{VALID_UUID}")
        assert res.status_code == 200
        assert res.json() == {"ok": True}


# ── Stats ───────────────────────────────────────────────────────────


class TestStats:
    async def test_stats_empty_month(self, client):
        client._mock_conn.fetchrow.return_value = _settings()
        client._mock_conn.fetch.return_value = []

        res = await client.get("/api/records/stats?year=2026&month=5")
        assert res.status_code == 200
        data = res.json()
        assert data["work_days"] == 0
        assert data["total_hours"] == 0.0
        assert data["overtime_hours"] == 0.0

    async def test_stats_one_standard_day(self, client):
        """一天标准工作：9:00-18:00，午休1h → 8h工时，0h加班"""
        records = [
            {
                "clock_in": datetime(2026, 5, 27, 9, 0),
                "clock_out": datetime(2026, 5, 27, 18, 0),
            }
        ]
        client._mock_conn.fetchrow.return_value = _settings()
        client._mock_conn.fetch.return_value = records

        res = await client.get("/api/records/stats?year=2026&month=5")
        assert res.status_code == 200
        data = res.json()
        assert data["work_days"] == 1
        assert data["total_hours"] == 8.0
        assert data["overtime_hours"] == 0.0

    async def test_stats_one_overtime_day(self, client):
        """加班到22:00：9:00-22:00=13h，-1h午休=12h，取整12h，加班=12-8=4h"""
        records = [
            {
                "clock_in": datetime(2026, 5, 27, 9, 0),
                "clock_out": datetime(2026, 5, 27, 22, 0),
            }
        ]
        client._mock_conn.fetchrow.return_value = _settings()
        client._mock_conn.fetch.return_value = records

        res = await client.get("/api/records/stats?year=2026&month=5")
        assert res.status_code == 200
        data = res.json()
        assert data["work_days"] == 1
        # 13h * 60 - 60 = 720min → round(720/30)*0.5 = 12.0h
        assert data["total_hours"] == 12.0
        # 12.0 - 8.0 = 4.0h
        assert data["overtime_hours"] == 4.0

    async def test_stats_multiple_days(self, client):
        """多天汇总"""
        records = [
            {
                "clock_in": datetime(2026, 5, 26, 9, 0),
                "clock_out": datetime(2026, 5, 26, 18, 0),
            },
            {
                "clock_in": datetime(2026, 5, 27, 9, 0),
                "clock_out": datetime(2026, 5, 27, 20, 0),
            },
        ]
        client._mock_conn.fetchrow.return_value = _settings()
        client._mock_conn.fetch.return_value = records

        res = await client.get("/api/records/stats?year=2026&month=5")
        assert res.status_code == 200
        data = res.json()
        assert data["work_days"] == 2
        # Day1: 9h-1h=8h, OT=0 | Day2: 11h-1h=10h, OT=2h
        assert data["total_hours"] == 18.0
        assert data["overtime_hours"] == 2.0


# ── End-to-End Flow ─────────────────────────────────────────────────


class TestDailyFlow:
    """模拟完整的每日打卡流程"""

    async def test_full_day_standard_work(self, client):
        """标准工作日：上班打卡 → 下班打卡"""
        clock_in = datetime(2026, 5, 27, 8, 0)
        clock_out = datetime(2026, 5, 27, 18, 0)

        # 上班打卡：无已有记录
        client._mock_conn.fetchrow.return_value = None
        client._mock_conn.fetchval.return_value = VALID_UUID
        client._mock_pool.fetchrow.return_value = _row(
            id=VALID_UUID, clock_in=clock_in, clock_out=None,
            total_hours=0.0, overtime_hours=0.0,
        )

        res = await client.post("/api/records/clock-in")
        assert res.status_code == 200
        assert res.json()["clock_out"] is None

        # 下班打卡
        existing = _row(id=VALID_UUID, clock_in=clock_in, clock_out=None)
        client._mock_conn.fetchrow.side_effect = [existing, _settings()]
        client._mock_pool.fetchrow.return_value = _row(
            id=VALID_UUID, clock_in=clock_in, clock_out=clock_out,
            total_hours=9.0, overtime_hours=1.0,
        )

        res = await client.post("/api/records/clock-out")
        assert res.status_code == 200
        data = res.json()
        assert data["clock_out"] is not None
        assert data["total_hours"] == 9.0
        assert data["overtime_hours"] == 1.0
