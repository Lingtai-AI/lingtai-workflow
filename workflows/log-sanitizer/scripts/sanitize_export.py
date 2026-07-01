#!/usr/bin/env python3
"""Local log/export sanitizer for LingTai workflow bundles.

This helper redacts common credential shapes plus caller-provided literals or
regexes from text files and SQLite text columns. It writes only to --output-dir
and records a REDACTION_MANIFEST.json. It is not a privacy guarantee; agents must
review the manifest and the sharing contract before sending anything.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

SECRET_PATTERNS = [
    ("private_key_block", re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----.*?-----END [A-Z0-9 ]*PRIVATE KEY-----", re.S), "[REDACTED:private-key]"),
    ("bearer_token", re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{16,}"), "Bearer [REDACTED:bearer-token]"),
    ("basic_auth", re.compile(r"(?i)\bBasic\s+[A-Za-z0-9+/]{16,}={0,2}"), "Basic [REDACTED:basic-auth]"),
    ("cookie_header", re.compile(r"(?im)^(Cookie|Set-Cookie)\s*:\s*\S.*$"), r"\1: [REDACTED:cookie]"),
    ("session_id", re.compile(r"(?i)\b(sessionid|session_id|sid|phpsessid|jsessionid|connect\.sid)\b([\s:=\"']+)([^\s\"',;{}\[]{8,})"), r"\1\2[REDACTED:session]"),
    ("aws_access_key_id", re.compile(r"\b(?:AKIA|ASIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA)[0-9A-Z]{16}\b"), "[REDACTED:aws-access-key-id]"),
    ("aws_secret_access_key", re.compile(r"(?i)\b(aws_secret_access_key)\b([\s:=\"']+)([A-Za-z0-9/+]{40})"), r"\1\2[REDACTED:aws-secret]"),
    ("github_token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr|github_pat)_[A-Za-z0-9_]{20,}\b"), "[REDACTED:github-token]"),
    ("slack_token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"), "[REDACTED:slack-token]"),
    ("openai_style_key", re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"), "[REDACTED:sk-key]"),
    ("telegram_bot_token", re.compile(r"\b\d{8,12}:[A-Za-z0-9_-]{20,}\b"), "[REDACTED:telegram-token]"),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"), "[REDACTED:jwt]"),
    ("key_value_secret", re.compile(r"(?i)\b(api[_-]?key|secret|token|password|passwd|authorization)\b([\s:=\"']+)([^\s\"',;{}\[]{8,})"), r"\1\2[REDACTED:secret-value]"),
]
EMAIL_PATTERN = ("email", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "[REDACTED:email]")

# Marker used by every replacement. Verification must not flag its own redacted
# output (e.g. "Set-Cookie: [REDACTED:cookie]" still matches the cookie pattern).
SENTINEL_RE = re.compile(r"\[REDACTED:[^\]]*\]")

TEXT_SUFFIXES = {".txt", ".md", ".json", ".jsonl", ".log", ".csv", ".yaml", ".yml", ".toml", ".html", ".xml"}
SQLITE_SUFFIXES = {".sqlite", ".sqlite3", ".db"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def short_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def count_bucket(n: int) -> str:
    """Bucket a replacement count so the share-safe manifest does not leak an exact
    literal-derived tally that could be used to fingerprint the removed text."""
    if n <= 0:
        return "0"
    if n <= 5:
        return "1-5"
    if n <= 20:
        return "6-20"
    if n <= 100:
        return "21-100"
    return "100+"


@dataclass
class Rule:
    # ``rule_id`` is the ONLY identifier that may reach the shareable manifest. For
    # built-in patterns it is a stable descriptive name; for caller literals/regexes
    # it is a hash-derived label that never contains the raw literal or pattern text.
    rule_id: str
    pattern: re.Pattern[str]
    replacement: str
    origin: str  # "builtin" | "literal" | "regex" | "email"


def load_policy(path: Path | None) -> dict:
    if path is None:
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_rules(policy: dict) -> list[Rule]:
    rules = [Rule(name, pattern, repl, "builtin") for name, pattern, repl in SECRET_PATTERNS]
    if policy.get("redact_emails"):
        name, pattern, repl = EMAIL_PATTERN
        rules.append(Rule(name, pattern, repl, "email"))
    for idx, literal in enumerate(policy.get("extra_literals", []) or []):
        if not literal:
            continue
        # rule_id is derived from a hash of the literal, NOT the literal text itself.
        rid = f"literal:{idx:02d}:{short_hash(str(literal))}"
        rules.append(Rule(rid, re.compile(re.escape(str(literal))), "[REDACTED:literal]", "literal"))
    for idx, item in enumerate(policy.get("extra_regexes", []) or []):
        pattern = str(item["pattern"])
        # Do not use the caller-provided name verbatim (it may describe or embed the
        # secret); label by index + pattern hash instead.
        rid = f"regex:{idx:02d}:{short_hash(pattern)}"
        rules.append(Rule(rid, re.compile(pattern), str(item.get("replacement", "[REDACTED:regex]")), "regex"))
    return rules


def apply_rules(text: str, rules: list[Rule]) -> tuple[str, dict[str, int]]:
    counts: dict[str, int] = {}
    for rule in rules:
        text, n = rule.pattern.subn(rule.replacement, text)
        if n:
            counts[rule.rule_id] = counts.get(rule.rule_id, 0) + n
    return text, counts


def merge_counts(items: Iterable[dict[str, int]]) -> dict[str, int]:
    out: dict[str, int] = {}
    for d in items:
        for k, v in d.items():
            out[k] = out.get(k, 0) + v
    return out


def is_probably_text(path: Path) -> bool:
    if path.suffix.lower() in TEXT_SUFFIXES:
        return True
    try:
        sample = path.read_bytes()[:4096]
    except OSError:
        return False
    if b"\0" in sample:
        return False
    try:
        sample.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False


def sanitize_text_file(src: Path, dst: Path, rules: list[Rule]) -> dict:
    raw = src.read_text(encoding="utf-8", errors="replace")
    redacted, counts = apply_rules(raw, rules)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(redacted, encoding="utf-8")
    return {"kind": "text", "replacement_counts": counts}


def quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def sanitize_sqlite_file(src: Path, dst: Path, rules: list[Rule]) -> dict:
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_suffix(dst.suffix + ".working")
    shutil.copy2(src, tmp)
    counts: list[dict[str, int]] = []
    con = sqlite3.connect(str(tmp))
    try:
        tables = [row[0] for row in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
        for table in tables:
            columns = con.execute(f"PRAGMA table_info({quote_ident(table)})").fetchall()
            text_cols = [row[1] for row in columns if str(row[2]).upper() in {"TEXT", "", "VARCHAR", "CHAR", "CLOB"}]
            if not text_cols:
                continue
            rowid_col = "rowid"
            selected = ", ".join([rowid_col] + [quote_ident(c) for c in text_cols])
            for row in con.execute(f"SELECT {selected} FROM {quote_ident(table)}"):
                rowid = row[0]
                updates = []
                params = []
                for col, val in zip(text_cols, row[1:]):
                    if not isinstance(val, str):
                        continue
                    new_val, c = apply_rules(val, rules)
                    if new_val != val:
                        updates.append(f"{quote_ident(col)} = ?")
                        params.append(new_val)
                        counts.append(c)
                if updates:
                    params.append(rowid)
                    con.execute(f"UPDATE {quote_ident(table)} SET {', '.join(updates)} WHERE rowid = ?", params)
        con.commit()
        # VACUUM INTO a fresh database so old page content is not left in freelist.
        if dst.exists():
            dst.unlink()
        con.execute("VACUUM INTO ?", (str(dst),))
    finally:
        con.close()
        tmp.unlink(missing_ok=True)
    return {"kind": "sqlite", "replacement_counts": merge_counts(counts)}


def verification_counts(path: Path, rules: list[Rule], policy: dict) -> dict:
    data = path.read_bytes()
    text = data.decode("utf-8", errors="ignore")
    generic = 0
    for name, pattern, _repl in SECRET_PATTERNS:
        for m in pattern.finditer(text):
            # Ignore self-matches on our own redaction output: strip sentinels from the
            # matched span and only count it if a real hit still remains.
            stripped = SENTINEL_RE.sub("", m.group(0))
            if pattern.search(stripped):
                generic += 1
    forbidden = 0
    for literal in policy.get("extra_literals", []) or []:
        if literal:
            forbidden += data.count(str(literal).encode("utf-8"))
    for item in policy.get("extra_regexes", []) or []:
        forbidden += len(re.compile(str(item["pattern"])).findall(text))
    return {"generic_secret_hits": generic, "forbidden_literal_hits": forbidden}


def collect_inputs(paths: list[Path]) -> list[Path]:
    out: list[Path] = []
    for p in paths:
        if p.is_dir():
            for child in sorted(p.rglob("*")):
                if child.is_file():
                    out.append(child)
        elif p.is_file():
            out.append(p)
        else:
            raise FileNotFoundError(str(p))
    return out


class OutputOverlapError(ValueError):
    """Raised when the output directory could overwrite or re-collect inputs."""


def _is_relative_to(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def assert_output_safe(output_dir: Path, input_roots: list[Path], input_files: list[Path]) -> None:
    """Hard-error before any processing if ``output_dir`` overlaps the inputs.

    All paths are already resolved. We refuse when the output directory could
    overwrite an original input, land inside a scanned input directory, or sit at a
    parent/ancestor that would re-collect its own generated files on a later run.
    """
    out = output_dir
    # 1. output dir must not be, contain, or live inside any scanned input directory.
    for root in input_roots:
        if out == root or _is_relative_to(out, root) or _is_relative_to(root, out):
            raise OutputOverlapError(
                f"output-dir overlaps input directory (rel labels only): "
                f"out={out.name!r} input_root={root.name!r}. "
                "Choose an output directory that is not inside, equal to, or an ancestor of any input."
            )
    # 2. output dir must not be the parent of any single input file, and no input
    #    file may already live inside the output tree (which we would collect/overwrite).
    for f in input_files:
        if out == f.parent or _is_relative_to(f, out):
            raise OutputOverlapError(
                f"output-dir is the directory of an input file (rel label only): {f.name!r}. "
                "Original inputs must not be overwritten; pick a separate fresh output directory."
            )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", action="append", required=True, help="Input file or directory. May be repeated.")
    ap.add_argument("--policy", help="JSON redaction policy.")
    ap.add_argument("--output-dir", required=True, help="Fresh output directory for redacted files.")
    args = ap.parse_args(argv)

    policy = load_policy(Path(args.policy)) if args.policy else {}
    rules = build_rules(policy)
    input_roots = [Path(x).resolve() for x in args.input]
    inputs = collect_inputs(input_roots)
    output_dir = Path(args.output_dir).resolve()

    # Refuse overlapping output BEFORE any directory is created or file is written,
    # so a footgun invocation can never overwrite or re-collect the originals.
    input_dir_roots = [p for p in input_roots if p.is_dir()]
    assert_output_safe(output_dir, input_dir_roots, inputs)
    output_dir.mkdir(parents=True, exist_ok=True)

    base = Path(os.path.commonpath([str(p.parent if p.is_file() else p) for p in inputs])) if inputs else Path.cwd()

    # A share-safe rule catalog: only rule_id + origin + a pattern hash. The raw
    # literal/regex text and any secret material never enter the shareable manifest.
    rule_catalog = [
        {
            "rule_id": r.rule_id,
            "origin": r.origin,
            "pattern_sha256": short_hash(r.pattern.pattern),
        }
        for r in rules
    ]
    manifest = {
        "manifest_kind": "share-safe",
        "note": (
            "Share-safe manifest: contains no raw policy, no raw redaction literals, "
            "no absolute local paths, and only bucketed replacement counts. Rules are "
            "referenced by hash-derived rule_id only."
        ),
        "policy_summary": {
            "redact_emails": bool(policy.get("redact_emails")),
            "extra_literal_count": len([x for x in (policy.get("extra_literals") or []) if x]),
            "extra_regex_count": len(policy.get("extra_regexes") or []),
        },
        "rule_catalog": rule_catalog,
        "inputs": [],
        "summary": {"files": 0, "errors": 0},
    }

    for src in inputs:
        rel = src.relative_to(base) if src.is_relative_to(base) else Path(src.name)
        dst = output_dir / rel
        # Relative labels only — no absolute source/output paths in the shareable manifest.
        record = {
            "source_rel": rel.as_posix(),
            "output_rel": (dst.relative_to(output_dir)).as_posix(),
            "source_size": src.stat().st_size,
            "source_sha256": sha256(src),
        }
        try:
            if src.suffix.lower() in SQLITE_SUFFIXES:
                result = sanitize_sqlite_file(src, dst, rules)
            elif is_probably_text(src):
                result = sanitize_text_file(src, dst, rules)
            else:
                record["skipped"] = "unsupported_binary"
                manifest["inputs"].append(record)
                continue
            # Replacement counts are keyed by share-safe rule_id and bucketed so the
            # exact literal-derived tally cannot fingerprint the removed text.
            raw_counts = result.pop("replacement_counts", {})
            record.update(result)
            record["replacement_count_buckets"] = {rid: count_bucket(n) for rid, n in sorted(raw_counts.items())}
            record["output_size"] = dst.stat().st_size
            record["output_sha256"] = sha256(dst)
            record["verification"] = verification_counts(dst, rules, policy)
            if record["verification"]["generic_secret_hits"] or record["verification"]["forbidden_literal_hits"]:
                manifest["summary"]["errors"] += 1
        except Exception as exc:  # noqa: BLE001 - manifest should record the failing file by relative label.
            record["error"] = f"{type(exc).__name__}: {exc}"
            manifest["summary"]["errors"] += 1
        manifest["inputs"].append(record)

    manifest["summary"]["files"] = len(manifest["inputs"])
    manifest_path = output_dir / "REDACTION_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 1 if manifest["summary"]["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
