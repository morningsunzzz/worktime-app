import unittest
import sys
import types

sys.modules.setdefault("asyncpg", types.SimpleNamespace(Pool=object, Record=object))
from backend import crud


class CrudTests(unittest.TestCase):
    def test_month_prefix_zero_pads_month(self):
        self.assertEqual(crud.month_prefix(2026, 5), "2026-05")
        self.assertEqual(crud.month_prefix(2026, 12), "2026-12")


if __name__ == "__main__":
    unittest.main()
