import unittest
import sys
import types
from datetime import date
from datetime import datetime
from decimal import Decimal

sys.modules.setdefault("asyncpg", types.SimpleNamespace(Pool=object, Record=object))
from backend import crud


class CrudTests(unittest.TestCase):
    def test_month_prefix_zero_pads_month(self):
        self.assertEqual(crud.month_prefix(2026, 5), "2026-05")
        self.assertEqual(crud.month_prefix(2026, 12), "2026-12")

    def test_db_date_converts_iso_string_to_date(self):
        self.assertEqual(crud.db_date("2026-05-25"), date(2026, 5, 25))

    def test_db_date_keeps_date_values(self):
        value = date(2026, 5, 25)
        self.assertIs(crud.db_date(value), value)

    def test_calc_overtime_accepts_decimal_settings(self):
        result = crud.calc_overtime_hours(
            datetime(2026, 5, 25, 9, 0),
            9.5,
            Decimal("8.0"),
            Decimal("1.0"),
        )
        self.assertEqual(result, 1.5)

    def test_build_update_statement_numbers_placeholders_after_values(self):
        sql = crud.build_update_statement(
            "work_records",
            {"clock_out": object(), "total_hours": object(), "overtime_hours": object()},
        )

        self.assertIn("clock_out = $1", sql)
        self.assertIn("total_hours = $2", sql)
        self.assertIn("overtime_hours = $3", sql)
        self.assertIn("WHERE id = $4", sql)


if __name__ == "__main__":
    unittest.main()
