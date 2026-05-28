import unittest
import sys
import types
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal
from uuid import UUID

sys.modules.setdefault("asyncpg", types.SimpleNamespace(Pool=object, Record=object))
from backend import crud


class RoundToHalfTests(unittest.TestCase):
    """工时精确到 0.5h 的取整规则"""

    def test_exact_hour(self):
        # round_to_half takes MINUTES and returns HOURS
        self.assertEqual(crud.round_to_half(0), 0.0)
        self.assertEqual(crud.round_to_half(60), 1.0)
        self.assertEqual(crud.round_to_half(120), 2.0)
        self.assertEqual(crud.round_to_half(480), 8.0)

    def test_exact_half_hour(self):
        self.assertEqual(crud.round_to_half(30), 0.5)
        self.assertEqual(crud.round_to_half(90), 1.5)
        self.assertEqual(crud.round_to_half(150), 2.5)
        self.assertEqual(crud.round_to_half(510), 8.5)

    def test_round_up_to_half(self):
        # 16-29 min → 0.5h
        self.assertEqual(crud.round_to_half(16), 0.5)
        self.assertEqual(crud.round_to_half(29), 0.5)
        # 46-59 min → 1.0h
        self.assertEqual(crud.round_to_half(46), 1.0)
        self.assertEqual(crud.round_to_half(59), 1.0)

    def test_round_down_to_half(self):
        # 1-14 min → 0.0h
        self.assertEqual(crud.round_to_half(1), 0.0)
        self.assertEqual(crud.round_to_half(14), 0.0)
        # 31-44 min → 0.5h
        self.assertEqual(crud.round_to_half(31), 0.5)
        self.assertEqual(crud.round_to_half(44), 0.5)

    def test_boundary_exact_15_minutes(self):
        # 15/30 = 0.5, round(0.5) = 0 (banker's rounding), 0*0.5 = 0.0
        self.assertEqual(crud.round_to_half(15), 0.0)

    def test_boundary_exact_45_minutes(self):
        self.assertEqual(crud.round_to_half(45), 1.0)

    def test_typical_workday(self):
        self.assertEqual(crud.round_to_half(480), 8.0)
        self.assertEqual(crud.round_to_half(510), 8.5)
        self.assertEqual(crud.round_to_half(540), 9.0)
        self.assertEqual(crud.round_to_half(570), 9.5)


class CalcWorkMinutesTests(unittest.TestCase):
    """实际工作时间 = (下班 - 上班) - 午休，最少 0"""

    def test_standard_8h_with_1h_lunch(self):
        """标准 9:00-18:00，扣除1h午休 = 480min(8h)"""
        ci = datetime(2026, 5, 26, 9, 0)
        co = datetime(2026, 5, 26, 18, 0)
        self.assertEqual(crud.calc_work_minutes(ci, co, 60), 480)

    def test_no_lunch_break(self):
        """午休=0，不扣除"""
        ci = datetime(2026, 5, 26, 9, 0)
        co = datetime(2026, 5, 26, 18, 0)
        self.assertEqual(crud.calc_work_minutes(ci, co, 0), 540)

    def test_short_lunch_30min(self):
        ci = datetime(2026, 5, 26, 9, 0)
        co = datetime(2026, 5, 26, 18, 0)
        self.assertEqual(crud.calc_work_minutes(ci, co, 30), 510)

    def test_long_lunch_2h(self):
        ci = datetime(2026, 5, 26, 9, 0)
        co = datetime(2026, 5, 26, 18, 0)
        self.assertEqual(crud.calc_work_minutes(ci, co, 120), 420)

    def test_half_day(self):
        """半天工作"""
        ci = datetime(2026, 5, 26, 9, 0)
        co = datetime(2026, 5, 26, 12, 0)
        self.assertEqual(crud.calc_work_minutes(ci, co, 60), 120)

    def test_overtime_evening(self):
        """加班到 22:00"""
        ci = datetime(2026, 5, 26, 9, 0)
        co = datetime(2026, 5, 26, 22, 0)
        self.assertEqual(crud.calc_work_minutes(ci, co, 60), 720)

    def test_cross_midnight(self):
        """通宵（跨天）"""
        ci = datetime(2026, 5, 26, 9, 0)
        co = datetime(2026, 5, 27, 9, 0)
        self.assertEqual(crud.calc_work_minutes(ci, co, 60), 1380)

    def test_lunch_longer_than_work(self):
        """午休比工时还长 → 结果为 0"""
        ci = datetime(2026, 5, 26, 9, 0)
        co = datetime(2026, 5, 26, 9, 30)
        self.assertEqual(crud.calc_work_minutes(ci, co, 60), 0)

    def test_clock_out_equals_clock_in(self):
        """刚打卡就下班 → 0"""
        ci = datetime(2026, 5, 26, 9, 0)
        co = datetime(2026, 5, 26, 9, 0)
        self.assertEqual(crud.calc_work_minutes(ci, co, 0), 0)

    def test_one_minute_work(self):
        ci = datetime(2026, 5, 26, 9, 0)
        co = datetime(2026, 5, 26, 9, 1)
        self.assertEqual(crud.calc_work_minutes(ci, co, 0), 1)


class CalcTotalHoursTests(unittest.TestCase):
    """总工时 = round_to_half(work_minutes)"""

    def test_exact_8h(self):
        self.assertEqual(crud.calc_total_hours(480), 8.0)

    def test_half_hour(self):
        self.assertEqual(crud.calc_total_hours(510), 8.5)

    def test_round_up(self):
        self.assertEqual(crud.calc_total_hours(469), 8.0)  # 469min → 7h49m → rounds to 8.0
        self.assertEqual(crud.calc_total_hours(470), 8.0)

    def test_zero(self):
        self.assertEqual(crud.calc_total_hours(0), 0.0)

    def test_negative_is_impossible_but_handled(self):
        result = crud.calc_total_hours(-10)
        self.assertEqual(result, -0.0)


class CalcOvertimeHoursTests(unittest.TestCase):
    """新加班公式: 早班加成(9点前) + 晚间加班(overtime_start之后)"""

    def test_no_clock_out_returns_zero(self):
        self.assertEqual(crud.calc_overtime_hours(
            datetime(2026, 5, 26, 9, 0), None, 1.0, "18:00"), 0.0)

    def test_standard_day_no_overtime(self):
        """9:00-18:00, overtime_start=18:00, pre=1 → 0h (过了9点无早班加成, 18点准时下班)"""
        self.assertEqual(crud.calc_overtime_hours(
            datetime(2026, 5, 26, 9, 0), datetime(2026, 5, 26, 18, 0), 1.0, "18:00"), 0.0)

    def test_morning_bonus_only(self):
        """8:00-17:00, ot_start=18:00, pre=1 → 1h (早班加成1h, 18点前下班无晚间加班)"""
        self.assertEqual(crud.calc_overtime_hours(
            datetime(2026, 5, 26, 8, 0), datetime(2026, 5, 26, 17, 0), 1.0, "18:00"), 1.0)

    def test_evening_overtime_only(self):
        """9:00-20:00, ot_start=18:00, pre=1 → 2h (无早班加成, 2h晚间加班)"""
        self.assertEqual(crud.calc_overtime_hours(
            datetime(2026, 5, 26, 9, 0), datetime(2026, 5, 26, 20, 0), 1.0, "18:00"), 2.0)

    def test_morning_plus_evening(self):
        """8:00-22:00, ot_start=18:00, pre=1 → 5h (1h早班 + 4h晚间)"""
        self.assertEqual(crud.calc_overtime_hours(
            datetime(2026, 5, 26, 8, 0), datetime(2026, 5, 26, 22, 0), 1.0, "18:00"), 5.0)

    def test_overtime_start_19(self):
        """9:00-20:00, ot_start=19:00, pre=1 → 1h (晚间从19点开始算)"""
        self.assertEqual(crud.calc_overtime_hours(
            datetime(2026, 5, 26, 9, 0), datetime(2026, 5, 26, 20, 0), 1.0, "19:00"), 1.0)

    def test_overtime_start_18_30(self):
        """9:00-18:44, ot_start=18:30 → 0h (14min < 15min rounds down)"""
        self.assertEqual(crud.calc_overtime_hours(
            datetime(2026, 5, 26, 9, 0), datetime(2026, 5, 26, 18, 44), 1.0, "18:30"), 0.0)

    def test_overtime_start_18_30_rounds_up(self):
        """9:00-18:46, ot_start=18:30 → 0.5h (16min rounds up)"""
        self.assertEqual(crud.calc_overtime_hours(
            datetime(2026, 5, 26, 9, 0), datetime(2026, 5, 26, 18, 46), 1.0, "18:30"), 0.5)

    def test_exact_nine_no_morning_bonus(self):
        """9:00整 → 无早班加成"""
        self.assertEqual(crud.calc_overtime_hours(
            datetime(2026, 5, 26, 9, 0), datetime(2026, 5, 26, 22, 0), 1.0, "18:00"), 4.0)

    def test_8_59_gets_morning_bonus(self):
        """8:59 → 有早班加成"""
        self.assertEqual(crud.calc_overtime_hours(
            datetime(2026, 5, 26, 8, 59), datetime(2026, 5, 26, 22, 0), 1.0, "18:00"), 5.0)

    def test_pre_hours_zero(self):
        """pre_hours=0 → 无早班加成"""
        self.assertEqual(crud.calc_overtime_hours(
            datetime(2026, 5, 26, 8, 0), datetime(2026, 5, 26, 20, 0), 0.0, "18:00"), 2.0)

    def test_decimal_pre_hours(self):
        """Decimal类型的pre_hours也能正常计算"""
        self.assertEqual(crud.calc_overtime_hours(
            datetime(2026, 5, 26, 8, 0), datetime(2026, 5, 26, 18, 0),
            Decimal("1.5"), "18:00"), 1.5)

    def test_cross_midnight(self):
        """跨天：overtime_start锚定在clock_in日期"""
        self.assertEqual(crud.calc_overtime_hours(
            datetime(2026, 5, 26, 9, 0), datetime(2026, 5, 27, 2, 0), 1.0, "18:00"), 8.0)

    def test_large_evening_overtime(self):
        """通宵到第二天早上"""
        result = crud.calc_overtime_hours(
            datetime(2026, 5, 26, 9, 0), datetime(2026, 5, 27, 8, 0), 0.0, "18:00")
        # 18:00 → 次日8:00 = 14h → 14*60/30*0.5 = 14.0h
        self.assertEqual(result, 14.0)


class MonthPrefixTests(unittest.TestCase):
    def test_single_digit_month_zero_padded(self):
        self.assertEqual(crud.month_prefix(2026, 5), "2026-05")
        self.assertEqual(crud.month_prefix(2026, 1), "2026-01")
        self.assertEqual(crud.month_prefix(2026, 9), "2026-09")

    def test_double_digit_month(self):
        self.assertEqual(crud.month_prefix(2026, 12), "2026-12")
        self.assertEqual(crud.month_prefix(2025, 10), "2025-10")

    def test_different_years(self):
        self.assertEqual(crud.month_prefix(2024, 1), "2024-01")
        self.assertEqual(crud.month_prefix(2027, 12), "2027-12")


class DbDateTests(unittest.TestCase):
    def test_converts_iso_string_to_date(self):
        self.assertEqual(crud.db_date("2026-05-25"), date(2026, 5, 25))
        self.assertEqual(crud.db_date("2025-01-01"), date(2025, 1, 1))

    def test_keeps_date_values(self):
        value = date(2026, 5, 25)
        self.assertIs(crud.db_date(value), value)


class DbDatetimeTests(unittest.TestCase):
    def test_converts_aware_utc_to_naive_china_time(self):
        value = datetime(2026, 5, 26, 10, 5, tzinfo=timezone.utc)
        self.assertEqual(crud.db_datetime(value), datetime(2026, 5, 26, 18, 5))

    def test_converts_iso_z_string_to_naive_china_time(self):
        self.assertEqual(
            crud.db_datetime("2026-05-26T10:05:00Z"),
            datetime(2026, 5, 26, 18, 5),
        )

    def test_keeps_naive_local_datetime(self):
        value = datetime(2026, 5, 26, 18, 5)
        self.assertIs(crud.db_datetime(value), value)

    def test_none_returns_none(self):
        self.assertIsNone(crud.db_datetime(None))

    def test_iso_string_with_timezone_offset(self):
        self.assertEqual(
            crud.db_datetime("2026-05-26T08:00:00+08:00"),
            datetime(2026, 5, 26, 8, 0),
        )

    def test_midnight_utc_to_china(self):
        value = datetime(2026, 5, 26, 0, 0, tzinfo=timezone.utc)
        self.assertEqual(crud.db_datetime(value), datetime(2026, 5, 26, 8, 0))


class DbUuidTests(unittest.TestCase):
    def test_converts_string_to_uuid(self):
        value = "e8bdab79-e1ac-4cda-89d7-1e4e34d195af"
        self.assertEqual(crud.db_uuid(value), UUID(value))

    def test_keeps_uuid_values(self):
        value = UUID("e8bdab79-e1ac-4cda-89d7-1e4e34d195af")
        self.assertIs(crud.db_uuid(value), value)


class BuildUpdateStatementTests(unittest.TestCase):
    def test_numbers_placeholders_after_values(self):
        sql = crud.build_update_statement(
            "work_records",
            {"clock_out": object(), "total_hours": object(), "overtime_hours": object()},
        )
        self.assertIn("clock_out = $1", sql)
        self.assertIn("total_hours = $2", sql)
        self.assertIn("overtime_hours = $3", sql)
        self.assertIn("WHERE id = $4", sql)

    def test_single_field(self):
        sql = crud.build_update_statement("work_records", {"note": object()})
        self.assertIn("note = $1", sql)
        self.assertIn("WHERE id = $2", sql)

    def test_empty_updates_raises(self):
        with self.assertRaises(ValueError):
            crud.build_update_statement("work_records", {})

    def test_two_fields(self):
        sql = crud.build_update_statement("work_records", {"a": object(), "b": object()})
        self.assertIn("a = $1", sql)
        self.assertIn("b = $2", sql)
        self.assertIn("WHERE id = $3", sql)


class DefaultClockInTimeTests(unittest.TestCase):
    def test_is_eight_am_on_current_day(self):
        current = datetime(2026, 5, 25, 20, 49, 55)
        self.assertEqual(
            crud.default_clock_in_time(current),
            datetime(2026, 5, 25, 8, 0, 0),
        )

    def test_midnight(self):
        current = datetime(2026, 5, 26, 0, 0, 0)
        self.assertEqual(
            crud.default_clock_in_time(current),
            datetime(2026, 5, 26, 8, 0, 0),
        )

    def test_preserves_date_only_changes_time(self):
        current = datetime(2025, 12, 31, 23, 59, 59)
        self.assertEqual(
            crud.default_clock_in_time(current),
            datetime(2025, 12, 31, 8, 0, 0),
        )


class LocalNowTests(unittest.TestCase):
    def test_returns_naive_china_time(self):
        current_utc = datetime(2026, 5, 26, 14, 14, 48, tzinfo=timezone.utc)
        self.assertEqual(
            crud.local_now(lambda: current_utc),
            datetime(2026, 5, 26, 22, 14, 48),
        )

    def test_midnight_utc(self):
        current_utc = datetime(2026, 5, 26, 0, 0, 0, tzinfo=timezone.utc)
        self.assertEqual(
            crud.local_now(lambda: current_utc),
            datetime(2026, 5, 26, 8, 0, 0),
        )

    def test_just_before_midnight_china(self):
        current_utc = datetime(2026, 5, 26, 15, 59, 59, tzinfo=timezone.utc)
        self.assertEqual(
            crud.local_now(lambda: current_utc),
            datetime(2026, 5, 26, 23, 59, 59),
        )

    def test_result_has_no_tzinfo(self):
        current_utc = datetime(2026, 5, 26, 14, 0, tzinfo=timezone.utc)
        result = crud.local_now(lambda: current_utc)
        self.assertIsNone(result.tzinfo)


class LocalTodayTests(unittest.TestCase):
    def test_uses_china_date(self):
        current_utc = datetime(2026, 5, 25, 16, 30, tzinfo=timezone.utc)
        self.assertEqual(crud.local_today(lambda: current_utc), date(2026, 5, 26))

    def test_match_local_now_date(self):
        current_utc = datetime(2026, 5, 26, 14, 0, tzinfo=timezone.utc)
        local = crud.local_now(lambda: current_utc)
        today = crud.local_today(lambda: current_utc)
        self.assertEqual(local.date(), today)

    def test_just_before_china_midnight(self):
        """UTC 15:59:59 = 北京时间 23:59:59，还在当天"""
        current_utc = datetime(2026, 5, 26, 15, 59, 59, tzinfo=timezone.utc)
        self.assertEqual(crud.local_today(lambda: current_utc), date(2026, 5, 26))

    def test_just_after_china_midnight(self):
        """UTC 16:00:00 = 北京时间 00:00:00，跨天"""
        current_utc = datetime(2026, 5, 26, 16, 0, 0, tzinfo=timezone.utc)
        self.assertEqual(crud.local_today(lambda: current_utc), date(2026, 5, 27))


if __name__ == "__main__":
    unittest.main()
