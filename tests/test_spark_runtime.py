from __future__ import annotations

import unittest

from spark_runtime.session import has_pyspark


class SparkRuntimeTest(unittest.TestCase):
    def test_has_pyspark_returns_bool(self) -> None:
        self.assertIsInstance(has_pyspark(), bool)


if __name__ == "__main__":
    unittest.main()
