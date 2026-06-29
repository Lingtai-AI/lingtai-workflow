#!/usr/bin/env python3
"""Mandatory self-test for the harness diagnostic matrix workflow.

This is intentionally small and dependency-free. An agent using the skill should
run this before applying the workflow to a real harness. Passing this test proves
that the renderer can take a fresh harness diagnosis JSON and produce a concrete
HTML matrix; it does not prove the real diagnosis is correct.
"""
from __future__ import annotations

import html.parser
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RENDERER = ROOT / "scripts" / "render_harness_matrix.py"

SMOKE_MATRIX = {
    "harness": "synthetic-eval-harness",
    "title": "Self-test: Arbitrary Harness Diagnostic Matrix",
    "date": "self-test",
    "scope": "Synthetic evaluation harness; no private data.",
    "footer": "Self-test only: matrix diagnoses; fixes are out of scope.",
    "rows": [
        {
            "symptom": "Metric drift after runner update",
            "site": ["scoring adapter", "fixture boundary"],
            "evidence": [
                "same 20 cases, runner version changed from A to B",
                "pass rate moved by 12 percentage points",
            ],
            "hypothesis": "The scoring adapter or fixture contract changed and the harness is attributing the shift to the model.",
            "differentials": [
                "model output changed",
                "case set changed",
                "random seed or sampling policy changed",
            ],
            "next_evidence": "Compare saved raw model outputs before/after the runner update and attach runner_version plus fixture_hash to score rows.",
            "severity": "high",
            "confidence": "medium",
        },
        {
            "symptom": "Changed scores cannot be traced to a cause",
            "site": ["observability", "run ledger"],
            "evidence": ["score CSV lacks runner_version", "score CSV lacks fixture_hash"],
            "hypothesis": "Missing provenance fields prevent diagnosis of the score movement.",
            "differentials": ["metadata exists in a separate artifact", "export script dropped provenance fields"],
            "next_evidence": "Locate authoritative run metadata and match each score row to a runner version and fixture hash.",
            "severity": "medium",
            "confidence": "high",
        },
    ],
}


class _Parser(html.parser.HTMLParser):
    pass


def main() -> int:
    if not RENDERER.exists():
        print(f"SELFTEST FAIL: renderer missing: {RENDERER}", file=sys.stderr)
        return 2
    with tempfile.TemporaryDirectory(prefix="harness_matrix_selftest_") as td:
        td_path = Path(td)
        matrix_path = td_path / "selftest_matrix.json"
        html_path = td_path / "selftest_matrix.html"
        matrix_path.write_text(json.dumps(SMOKE_MATRIX, ensure_ascii=False, indent=2), encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(RENDERER), str(matrix_path), str(html_path)],
            text=True,
            capture_output=True,
        )
        if proc.returncode != 0:
            print(proc.stdout, end="")
            print(proc.stderr, end="", file=sys.stderr)
            print("SELFTEST FAIL: renderer exited non-zero", file=sys.stderr)
            return proc.returncode or 3
        html = html_path.read_text(encoding="utf-8")
        _Parser().feed(html)
        required_fragments = [
            "Self-test: Arbitrary Harness Diagnostic Matrix",
            "Metric drift after runner update",
            "scoring adapter",
            "Changed scores cannot be traced to a cause",
            "Missing provenance fields prevent diagnosis",
        ]
        missing = [frag for frag in required_fragments if frag not in html]
        if missing:
            print(f"SELFTEST FAIL: rendered HTML missing fragments: {missing}", file=sys.stderr)
            return 4
        # Diagnosis quality gate: every row must carry evidence and a next evidence question.
        for idx, row in enumerate(SMOKE_MATRIX["rows"], 1):
            if not row.get("evidence") or not row.get("hypothesis") or not row.get("next_evidence"):
                print(f"SELFTEST FAIL: row {idx} lacks evidence/hypothesis/next_evidence", file=sys.stderr)
                return 5
        print(f"SELFTEST PASS: rendered {html_path.name} from a fresh arbitrary harness input ({len(SMOKE_MATRIX['rows'])} rows).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
