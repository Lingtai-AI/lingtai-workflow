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

# Blocker #3 (regex replacement re-injection): a careless/malicious custom regex
# replacement that tries to smuggle sensitive text back into the share-safe output.
# The sanitizer must ignore this replacement and use a generic label instead, so the
# fake SSN below must NOT appear in the redacted output.
MALICIOUS_REGEX_MATCH = "ACCT-TRIGGER-7788"
MALICIOUS_REGEX_REPLACEMENT = "[REDACTED:acct=Jane Doe SSN 123-45-6789]"
MALICIOUS_FAKE_SSN = "123-45-6789"


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
        sample = {"token": fake_sk, "path": PRIVATE_PATH_LITERAL, "ticket": "PRIVATE-TICKET-42",
                  "acct": MALICIOUS_REGEX_MATCH}
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
            "extra_regexes": [
                {"name": "ticket", "pattern": "PRIVATE-TICKET-[0-9]+", "replacement": "[REDACTED:ticket]"},
                # Malicious replacement: tries to re-inject a fake SSN into share-safe output.
                {"name": "acct", "pattern": MALICIOUS_REGEX_MATCH, "replacement": MALICIOUS_REGEX_REPLACEMENT},
            ],
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
        # No raw-derived rule/source/pattern fingerprints may reach the share manifest.
        if "pattern_sha256" in manifest_raw:
            print("manifest contains pattern_sha256 fingerprint", file=sys.stderr)
            return 1
        if "source_sha256" in manifest_raw:
            print("manifest contains raw-input source_sha256", file=sys.stderr)
            return 1
        # Custom literal/regex rule_ids must be opaque (e.g. "literal:00"), never a
        # "literal:00:<hash>" / "regex:00:<hash>" raw-derived stable fingerprint form.
        for entry in manifest.get("rule_catalog", []):
            rid = entry.get("rule_id", "")
            if entry.get("origin") in {"literal", "regex"} and rid.count(":") != 1:
                print(f"custom rule_id is not opaque: {rid!r}", file=sys.stderr)
                return 1

        # Text redaction sanity, including the newly-covered header shapes.
        text = (out / "events.jsonl").read_text(encoding="utf-8")
        if fake_sk in text or "/Users/example" in text or "PRIVATE-TICKET" in text:
            print("text redaction failed", file=sys.stderr)
            return 1

        # --- Blocker #3: custom regex replacement must not re-inject sensitive text ---
        # The matched trigger must be gone, the malicious replacement text (and its fake
        # SSN) must NOT appear in the redacted output, and the generic regex label must
        # be used instead. The manifest must also stay clean of the fake SSN.
        if MALICIOUS_REGEX_MATCH in text:
            print("custom regex did not fire on its trigger", file=sys.stderr)
            return 1
        if MALICIOUS_REGEX_REPLACEMENT in text or MALICIOUS_FAKE_SSN in text:
            print("custom regex replacement re-injected sensitive text into output", file=sys.stderr)
            return 1
        if "[REDACTED:regex]" not in text:
            print("custom regex did not use the generic redaction label", file=sys.stderr)
            return 1
        if MALICIOUS_FAKE_SSN in manifest_raw or "Jane Doe" in manifest_raw:
            print("manifest leaked re-injected sensitive text", file=sys.stderr)
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

        # --- Positive overlap case: a sibling output dir must be ALLOWED -----------
        # input `logs/` and output `redacted/` sitting side by side is the intended
        # usage and must not be rejected by the overlap guard.
        sib_base = base / "sibling"
        logs_dir = sib_base / "logs"
        redacted_dir = sib_base / "redacted"
        logs_dir.mkdir(parents=True)
        (logs_dir / "events.jsonl").write_text(json.dumps({"token": fake_sk}) + "\n", encoding="utf-8")
        sibling = run(logs_dir, redacted_dir, policy)
        if sibling.returncode != 0:
            print(sibling.stdout)
            print(sibling.stderr, file=sys.stderr)
            print("sibling output-dir alongside input-dir was wrongly refused", file=sys.stderr)
            return 1
        if not (redacted_dir / "REDACTION_MANIFEST.json").exists():
            print("sibling run produced no manifest", file=sys.stderr)
            return 1

    print("SELFTEST PASS: log sanitizer redacted text and sqlite samples; manifest is share-safe; output-overlap refused; sibling output allowed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
