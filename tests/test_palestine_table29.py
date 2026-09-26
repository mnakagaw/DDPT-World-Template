"""Coordinate extraction guards for wrapped PCBS locality labels."""

import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "extract_palestine_pcbs_table29.py"
spec = importlib.util.spec_from_file_location("pse_table29", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def cell(text, x_min, x_max, y):
    return {"text": text, "x_min": x_min, "x_max": x_max, "y": y}


class Table29Tests(unittest.TestCase):
    def test_wrapped_name_does_not_shift_numeric_cells(self):
        words = [cell("Wad", 40, 60, 135), cell("Sharqiya)", 40, 85, 145),
                 cell("285", 220, 236, 140), cell("286", 300, 315, 140),
                 cell("571", 380, 393, 140), cell("10235", 450, 472, 140),
                 cell("Dhaher", 40, 65, 154), cell("202", 220, 236, 160),
                 cell("265", 300, 315, 160), cell("467", 380, 393, 160),
                 cell("10240", 450, 472, 158)]
        rows = module.extract_page(words, 117)
        self.assertEqual([(r["locality_code"], r["total"]) for r in rows],
                         [("10235", 571), ("10240", 467)])

    def test_ambiguous_or_missing_number_rejected(self):
        words = [cell("10235", 450, 472, 140), cell("285", 220, 236, 140),
                 cell("286", 300, 315, 140), cell("571", 380, 393, 140)]
        with self.assertRaisesRegex(ValueError, "females cell count 2"):
            module.extract_page(words + [cell("285", 220, 236, 141)], 117)
        with self.assertRaisesRegex(ValueError, "males cell count 0"):
            module.extract_page([w for w in words if w["text"] != "286"], 117)

    def test_arithmetic_mismatch_rejected(self):
        words = [cell("10235", 450, 472, 140), cell("285", 220, 236, 140),
                 cell("286", 300, 315, 140), cell("572", 380, 393, 140)]
        with self.assertRaisesRegex(ValueError, "sex counts differ"):
            module.extract_page(words, 117)


if __name__ == "__main__":
    unittest.main()
