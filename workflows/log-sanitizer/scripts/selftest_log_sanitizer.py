#!/usr/bin/env python3
from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "sanitize_export.py"


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        inp = base / "input"
        out = base / "out"
        inp.mkdir()
        fake_sk = "sk-" + "testSECRETSECRETSECRET"
        sample = {"token": fake_sk, "path": "/Users/example/private/project", "ticket": "PRIVATE-TICKET-42"}
        (inp / "events.jsonl").write_text(json.dumps(sample) + "\n", encoding="utf-8")
        db = inp / "log.sqlite"
        con = sqlite3.connect(db)
        con.execute("CREATE TABLE logs(message TEXT)")
        fake_bearer = "Bearer " + "abcdefghijklmnopqrstuvwxyz"
        con.execute("INSERT INTO logs VALUES (?)", (fake_bearer + " PRIVATE-TICKET-99",))
        con.commit(); con.close()
        policy = base / "policy.json"
        policy.write_text(json.dumps({
            "extra_literals": ["/Users/example/private/project"],
            "extra_regexes": [{"name": "ticket", "pattern": "PRIVATE-TICKET-[0-9]+", "replacement": "[REDACTED:ticket]"}],
        }), encoding="utf-8")
        proc = subprocess.run([sys.executable, str(SCRIPT), "--input", str(inp), "--policy", str(policy), "--output-dir", str(out)], text=True, capture_output=True)
        if proc.returncode != 0:
            print(proc.stdout)
            print(proc.stderr, file=sys.stderr)
            return proc.returncode
        manifest = json.loads((out / "REDACTION_MANIFEST.json").read_text(encoding="utf-8"))
        if manifest["summary"]["errors"]:
            print(json.dumps(manifest, indent=2), file=sys.stderr)
            return 1
        text = (out / "events.jsonl").read_text(encoding="utf-8")
        if fake_sk in text or "/Users/example" in text or "PRIVATE-TICKET" in text:
            print("text redaction failed", file=sys.stderr)
            return 1
        con = sqlite3.connect(out / "log.sqlite")
        value = con.execute("SELECT message FROM logs").fetchone()[0]
        con.close()
        if fake_bearer in value or "PRIVATE-TICKET" in value:
            print("sqlite redaction failed", file=sys.stderr)
            return 1
    print("SELFTEST PASS: log sanitizer redacted text and sqlite samples.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
