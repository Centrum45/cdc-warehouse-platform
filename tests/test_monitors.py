from __future__ import annotations

import unittest

from monitors.field_monitor import extra_columns, missing_columns
from monitors.sensitive_text_monitor import detect_sensitive_text
from monitors.special_value_monitor import find_special_values


class MonitorTest(unittest.TestCase):
    def test_field_diff(self) -> None:
        self.assertEqual(missing_columns(["id", "name"], ["id"]), ["name"])
        self.assertEqual(extra_columns(["id"], ["id", "tmp"]), ["tmp"])

    def test_sensitive_text(self) -> None:
        self.assertEqual(detect_sensitive_text("user@example.com"), ["email"])

    def test_special_value(self) -> None:
        self.assertEqual(find_special_values({"status": -1}, {"status": [-1]}), {"status": -1})


if __name__ == "__main__":
    unittest.main()

