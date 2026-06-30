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
    ("openai_style_key", re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"), "[REDACTED:sk-key]"),
    ("telegram_bot_token", re.compile(r"\b\d{8,12}:[A-Za-z0-9_-]{20,}\b"), "[REDACTED:telegram-token]"),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"), "[REDACTED:jwt]"),
    ("key_value_secret", re.compile(r"(?i)\b(api[_-]?key|secret|token|password|passwd|authorization)\b([\s:=\"']+)([^\s\"',;{}\[]{8,})"), r"\1\2[REDACTED:secret-value]"),
]
EMAIL_PATTERN = ("email", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "[REDACTED:email]")

TEXT_SUFFIXES = {".txt", ".md", ".json", ".jsonl", ".log", ".csv", ".yaml", ".yml", ".toml", ".html", ".xml"}
SQLITE_SUFFIXES = {".sqlite", ".sqlite3", ".db"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


@dataclass
class Rule:
    name: str
    pattern: re.Pattern[str]
    replacement: str


def load_policy(path: Path | None) -> dict:
    if path is None:
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_rules(policy: dict) -> list[Rule]:
    rules = [Rule(name, pattern, repl) for name, pattern, repl in SECRET_PATTERNS]
    if policy.get("redact_emails"):
        name, pattern, repl = EMAIL_PATTERN
        rules.append(Rule(name, pattern, repl))
    for literal in policy.get("extra_literals", []) or []:
        if not literal:
            continue
        rules.append(Rule(f"literal:{literal[:40]}", re.compile(re.escape(str(literal))), "[REDACTED:literal]"))
    for item in policy.get("extra_regexes", []) or []:
        rules.append(Rule(str(item["name"]), re.compile(str(item["pattern"])), str(item.get("replacement", "[REDACTED:regex]"))))
    return rules


def apply_rules(text: str, rules: list[Rule]) -> tuple[str, dict[str, int]]:
    counts: dict[str, int] = {}
    for rule in rules:
        text, n = rule.pattern.subn(rule.replacement, text)
        if n:
            counts[rule.name] = counts.get(rule.name, 0) + n
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
        generic += len(pattern.findall(text))
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


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", action="append", required=True, help="Input file or directory. May be repeated.")
    ap.add_argument("--policy", help="JSON redaction policy.")
    ap.add_argument("--output-dir", required=True, help="Fresh output directory for redacted files.")
    args = ap.parse_args(argv)

    policy = load_policy(Path(args.policy)) if args.policy else {}
    rules = build_rules(policy)
    inputs = collect_inputs([Path(x).resolve() for x in args.input])
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    base = Path(os.path.commonpath([str(p.parent if p.is_file() else p) for p in inputs])) if inputs else Path.cwd()
    manifest = {"policy": policy, "inputs": [], "summary": {"files": 0, "errors": 0}}

    for src in inputs:
        rel = src.relative_to(base) if src.is_relative_to(base) else Path(src.name)
        dst = output_dir / rel
        record = {"source": str(src), "output": str(dst), "source_size": src.stat().st_size, "source_sha256": sha256(src)}
        try:
            if src.suffix.lower() in SQLITE_SUFFIXES:
                result = sanitize_sqlite_file(src, dst, rules)
            elif is_probably_text(src):
                result = sanitize_text_file(src, dst, rules)
            else:
                record["skipped"] = "unsupported_binary"
                manifest["inputs"].append(record)
                continue
            record.update(result)
            record["output_size"] = dst.stat().st_size
            record["output_sha256"] = sha256(dst)
            record["verification"] = verification_counts(dst, rules, policy)
            if record["verification"]["generic_secret_hits"] or record["verification"]["forbidden_literal_hits"]:
                manifest["summary"]["errors"] += 1
        except Exception as exc:  # noqa: BLE001 - manifest should record exact failing file.
            record["error"] = f"{type(exc).__name__}: {exc}"
            manifest["summary"]["errors"] += 1
        manifest["inputs"].append(record)

    manifest["summary"]["files"] = len(manifest["inputs"])
    manifest_path = output_dir / "REDACTION_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 1 if manifest["summary"]["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
