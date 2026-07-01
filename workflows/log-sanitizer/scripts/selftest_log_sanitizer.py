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

# A raw literal the sanitizer is asked to remove. It must never reappear in the
# shareable manifest (blocker #1: share-safe manifest).
PRIVATE_PATH_LITERAL = "/Users/example/private/project"


def run(inp: Path, out: Path, policy: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--input", str(inp), "--policy", str(policy), "--output-dir", str(out)],
        text=True,
        capture_output=True,
    )


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        inp = base / "input"
        out = base / "out"
        inp.mkdir()
        fake_sk = "sk-" + "testSECRETSECRETSECRET"
        sample = {"token": fake_sk, "path": PRIVATE_PATH_LITERAL, "ticket": "PRIVATE-TICKET-42"}
        (inp / "events.jsonl").write_text(json.dumps(sample) + "\n", encoding="utf-8")
        # Extra missed-pattern shapes from the review (basic auth, cookie, AWS/GH/Slack).
        # Build fake tokens at runtime so source scanners do not flag static fixture strings.
        fake_aws = "AKIA" + "IOSFODNN7" + "EXAMPLE"
        fake_gh = "ghp_" + "0123456789abcdef" + "0123456789abcdef0123"
        fake_slack = "xoxb-" + "1111-2222-" + "abcdefghijkl"
        (inp / "headers.log").write_text(
            "Authorization: Basic dXNlcjpwYXNzd29yZDEyMzQ1Ng==\n"
            "Set-Cookie: sessionid=abcdef0123456789abcdef; HttpOnly\n"
            f"aws={fake_aws} gh={fake_gh} slack={fake_slack}\n",
            encoding="utf-8",
        )
        db = inp / "log.sqlite"
        con = sqlite3.connect(db)
        con.execute("CREATE TABLE logs(message TEXT)")
        fake_bearer = "Bearer " + "abcdefghijklmnopqrstuvwxyz"
        con.execute("INSERT INTO logs VALUES (?)", (fake_bearer + " PRIVATE-TICKET-99",))
        con.commit(); con.close()
        policy = base / "policy.json"
        policy.write_text(json.dumps({
            "extra_literals": [PRIVATE_PATH_LITERAL],
            "extra_regexes": [{"name": "ticket", "pattern": "PRIVATE-TICKET-[0-9]+", "replacement": "[REDACTED:ticket]"}],
        }), encoding="utf-8")

        proc = run(inp, out, policy)
        if proc.returncode != 0:
            print(proc.stdout)
            print(proc.stderr, file=sys.stderr)
            return proc.returncode
        manifest_raw = (out / "REDACTION_MANIFEST.json").read_text(encoding="utf-8")
        manifest = json.loads(manifest_raw)
        if manifest["summary"]["errors"]:
            print(json.dumps(manifest, indent=2), file=sys.stderr)
            return 1

        # --- Blocker #1: manifest must be share-safe -----------------------------
        # No raw extra literal, no raw policy, no absolute temp paths in the manifest.
        if PRIVATE_PATH_LITERAL in manifest_raw:
            print("manifest leaked raw extra literal", file=sys.stderr)
            return 1
        if str(base) in manifest_raw or td in manifest_raw:
            print("manifest leaked absolute temp/source path", file=sys.stderr)
            return 1
        if "policy" in manifest and manifest.get("manifest_kind") != "share-safe":
            print("manifest embedded raw policy", file=sys.stderr)
            return 1
        if "PRIVATE-TICKET" in manifest_raw:
            print("manifest leaked forbidden ticket literal", file=sys.stderr)
            return 1

        # Text redaction sanity, including the newly-covered header shapes.
        text = (out / "events.jsonl").read_text(encoding="utf-8")
        if fake_sk in text or "/Users/example" in text or "PRIVATE-TICKET" in text:
            print("text redaction failed", file=sys.stderr)
            return 1
        headers = (out / "headers.log").read_text(encoding="utf-8")
        for leaked in ("dXNlcjpwYXNzd29yZDEyMzQ1Ng==", "abcdef0123456789abcdef",
                       fake_aws, fake_gh, fake_slack):
            if leaked in headers:
                print(f"header redaction failed: {leaked[:8]}...", file=sys.stderr)
                return 1

        con = sqlite3.connect(out / "log.sqlite")
        value = con.execute("SELECT message FROM logs").fetchone()[0]
        con.close()
        if fake_bearer in value or "PRIVATE-TICKET" in value:
            print("sqlite redaction failed", file=sys.stderr)
            return 1

        # --- Blocker #2: output overlapping an input dir must be refused ----------
        # Output equal to the input directory (would overwrite originals) -> hard error.
        original = (inp / "events.jsonl").read_bytes()
        overlap = run(inp, inp, policy)
        if overlap.returncode == 0:
            print("output-overlap guard did not refuse output-dir == input-dir", file=sys.stderr)
            return 1
        if "overlap" not in (overlap.stderr + overlap.stdout).lower():
            print("output-overlap refusal message missing", file=sys.stderr)
            return 1
        if (inp / "events.jsonl").read_bytes() != original:
            print("original input was modified by refused overlap run", file=sys.stderr)
            return 1

        # Output nested inside the input directory must also be refused.
        nested = run(inp, inp / "redacted", policy)
        if nested.returncode == 0:
            print("output-overlap guard did not refuse output-dir inside input-dir", file=sys.stderr)
            return 1
        if (inp / "events.jsonl").read_bytes() != original:
            print("original input was modified by refused nested run", file=sys.stderr)
            return 1

        # The exact file-mode footgun: sanitizing one file into its own parent
        # directory must be refused before any output file can overwrite the input.
        file_parent = run(inp / "events.jsonl", inp, policy)
        if file_parent.returncode == 0:
            print("output-overlap guard did not refuse file -> parent directory", file=sys.stderr)
            return 1
        if "input file" not in (file_parent.stderr + file_parent.stdout).lower():
            print("file-parent refusal message missing input-file clue", file=sys.stderr)
            return 1
        if (inp / "events.jsonl").read_bytes() != original:
            print("original input was modified by refused file-parent run", file=sys.stderr)
            return 1

    print("SELFTEST PASS: log sanitizer redacted text and sqlite samples; manifest is share-safe; output-overlap refused.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
