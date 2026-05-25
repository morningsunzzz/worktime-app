import unittest
import sys
import types
from datetime import date

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


if __name__ == "__main__":
    unittest.main()
