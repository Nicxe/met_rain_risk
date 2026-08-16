"""Regression tests for sensitive data disclosure in coordinator diagnostics."""

from __future__ import annotations

import ast
from pathlib import Path
import unittest


COORDINATOR = (
    Path(__file__).parents[1]
    / "custom_components"
    / "met_rain_risk"
    / "coordinator.py"
)
SENSITIVE_NAMES = {"url", "headers", "text", "err"}


class SensitiveDiagnosticsTest(unittest.TestCase):
    """Ensure request details and upstream data never enter logs or errors."""

    def test_diagnostics_do_not_expose_sensitive_values(self) -> None:
        source = COORDINATOR.read_text(encoding="utf-8")
        tree = ast.parse(source)

        diagnostic_calls: list[ast.Call] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Attribute) and node.func.attr in {
                "debug",
                "info",
                "warning",
                "error",
                "exception",
                "critical",
            }:
                diagnostic_calls.append(node)
            elif isinstance(node.func, ast.Name) and node.func.id == "UpdateFailed":
                diagnostic_calls.append(node)

        exposed = {
            child.id
            for call in diagnostic_calls
            for child in ast.walk(call)
            if isinstance(child, ast.Name) and child.id in SENSITIVE_NAMES
        }
        self.assertEqual(set(), exposed)


if __name__ == "__main__":
    unittest.main()
