#!/usr/bin/env python3
"""Validate workflows/*/SKILL.md as installable LingTai skill bundles.

This is a *portable, advisory* repo check. It uses only the Python standard
library so it runs anywhere (`python3 scripts/validate_workflow_skills.py`) with
no install step. It does not talk to the LingTai runtime or kernel, and it is not
a marketplace protocol: it only checks that each accepted workflow directory is a
self-contained skill bundle that a human could copy into an agent's skill library.

FAIL (exit 1) means a real packaging defect: missing SKILL.md, unparseable or
incomplete frontmatter, no advisory marker, missing attribution, a bundle that
reaches outside its own directory, or a bundle the README index never links.

WARN (exit 0) means a portability nit worth a human glance but not a blocker:
an over-long description or file, a missing last_verified date, or a frontmatter
`name` that does not match the directory slug.

Usage:
    python3 scripts/validate_workflow_skills.py [--repo-root DIR] [--quiet]
"""

from __future__ import annotations

import argparse
import os
import sys

# Soft thresholds. These only ever produce warnings, never failures, matching the
# repo's stance that long descriptions / long files are acceptable but noteworthy.
DESCRIPTION_WARN_CHARS = 500
FILE_WARN_LINES = 400

BUNDLE_SUBDIRS = ("assets", "references", "scripts")


class Frontmatter:
    """A tolerant reader for the small, flat YAML frontmatter these bundles use.

    We deliberately avoid PyYAML (not in the stdlib). The frontmatter in this repo
    is flat scalars, block scalars (``description: >-``), and simple ``- item``
    lists, so a line-oriented parser is enough and keeps the script dependency-free.
    """

    def __init__(self):
        self.keys: set[str] = set()
        self.scalars: dict[str, str] = {}

    @classmethod
    def parse(cls, text: str) -> "Frontmatter | None":
        lines = text.splitlines()
        if not lines or lines[0].strip() != "---":
            return None
        end = None
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                end = i
                break
        if end is None:
            return None

        fm = cls()
        i = 1
        while i < end:
            raw = lines[i]
            stripped = raw.strip()
            i += 1
            if not stripped or stripped.startswith("#"):
                continue
            # Only treat top-level (unindented) keys as fields; indented lines are
            # list items or block-scalar continuations owned by the last key.
            if raw[:1] in (" ", "\t") or ":" not in stripped:
                continue
            key, _, rest = stripped.partition(":")
            key = key.strip()
            rest = rest.strip()
            fm.keys.add(key)

            if rest in (">-", ">", "|", "|-", ">+", "|+"):
                # Block scalar: gather following more-indented lines.
                block: list[str] = []
                while i < end:
                    nxt = lines[i]
                    if nxt.strip() == "":
                        block.append("")
                        i += 1
                        continue
                    if nxt[:1] in (" ", "\t"):
                        block.append(nxt.strip())
                        i += 1
                    else:
                        break
                fm.scalars[key] = " ".join(p for p in block if p != "").strip()
            elif rest == "":
                # Bare key: likely a list. Value stays empty; presence is recorded.
                fm.scalars.setdefault(key, "")
            else:
                fm.scalars[key] = rest.strip().strip('"').strip("'")
        return fm


class Report:
    def __init__(self):
        self.failures: list[str] = []
        self.warnings: list[str] = []

    def fail(self, msg: str) -> None:
        self.failures.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def is_within(base: str, target: str) -> bool:
    base_r = os.path.realpath(base)
    target_r = os.path.realpath(target)
    return target_r == base_r or target_r.startswith(base_r + os.sep)


def check_bundle_contained(bundle_dir: str, rep: Report) -> None:
    """Fail if any file in the bundle is a symlink escaping the bundle directory."""
    for root, dirs, files in os.walk(bundle_dir):
        for entry in list(dirs) + files:
            full = os.path.join(root, entry)
            if os.path.islink(full) and not is_within(bundle_dir, full):
                rep.fail(
                    f"supporting path escapes the bundle: "
                    f"{os.path.relpath(full, bundle_dir)} -> {os.path.realpath(full)}"
                )


def check_skill(bundle_dir: str, slug: str, readme_text: str, rep: Report) -> None:
    skill_path = os.path.join(bundle_dir, "SKILL.md")
    if not os.path.isfile(skill_path):
        rep.fail("missing SKILL.md")
        return

    text = read_text(skill_path)
    fm = Frontmatter.parse(text)
    if fm is None:
        rep.fail("SKILL.md has no parseable YAML frontmatter block")
        return

    name = fm.scalars.get("name", "").strip()
    if "name" not in fm.keys or not name:
        rep.fail("frontmatter is missing a non-empty `name`")

    description = fm.scalars.get("description", "").strip()
    if "description" not in fm.keys or not description:
        rep.fail("frontmatter is missing a non-empty `description`")

    # Advisory marker: either the frontmatter flag or an explicit advisory line in
    # the body blockquote. Both are used across the repo; accept either.
    body = text.split("---", 2)[-1].lower()
    advisory_flag = fm.scalars.get("advisory", "").lower() == "true"
    advisory_body = "advisory only" in body or "advisory-only" in body
    if not (advisory_flag or advisory_body):
        rep.fail("no advisory marker (`advisory: true` or an 'Advisory only' note)")

    # Attribution must survive packaging.
    if not fm.scalars.get("author", "").strip():
        rep.fail("frontmatter is missing `author` attribution")

    # README index must link the bundle so a human can discover and install it.
    # Accept a link to the directory, or the slug / frontmatter name appearing in
    # the index table.
    linked = (
        f"workflows/{slug}/" in readme_text
        or f"workflows/{slug}" in readme_text
        or (name and name in readme_text)
        or slug in readme_text
    )
    if not linked:
        rep.fail("not linked from the README workflow index")

    check_bundle_contained(bundle_dir, rep)

    # ---- warnings only below this line ----

    if description and len(description) > DESCRIPTION_WARN_CHARS:
        rep.warn(
            f"description is long ({len(description)} chars > {DESCRIPTION_WARN_CHARS})"
        )

    if "last_verified" not in fm.keys or not fm.scalars.get("last_verified", "").strip():
        rep.warn("frontmatter has no `last_verified` date")

    if name and name != slug:
        rep.warn(f"frontmatter `name` ({name!r}) differs from directory slug ({slug!r})")

    for root, _dirs, files in os.walk(bundle_dir):
        for fn in files:
            full = os.path.join(root, fn)
            try:
                with open(full, "r", encoding="utf-8", errors="ignore") as fh:
                    line_count = sum(1 for _ in fh)
            except OSError:
                continue
            if line_count > FILE_WARN_LINES:
                rel = os.path.relpath(full, bundle_dir)
                rep.warn(f"{rel} is long ({line_count} lines > {FILE_WARN_LINES})")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        help="repository root (default: parent of scripts/)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="only print failing bundles and the final summary",
    )
    args = parser.parse_args(argv)

    repo_root = os.path.abspath(args.repo_root)
    workflows_dir = os.path.join(repo_root, "workflows")
    readme_path = os.path.join(repo_root, "README.md")

    if not os.path.isdir(workflows_dir):
        print(f"FAIL: no workflows/ directory under {repo_root}", file=sys.stderr)
        return 1

    readme_text = read_text(readme_path) if os.path.isfile(readme_path) else ""
    if not readme_text:
        print("FAIL: README.md missing; cannot verify workflow index links", file=sys.stderr)
        return 1

    slugs = sorted(
        d
        for d in os.listdir(workflows_dir)
        if os.path.isdir(os.path.join(workflows_dir, d)) and not d.startswith(".")
    )
    if not slugs:
        print(f"FAIL: no workflow bundles under {workflows_dir}", file=sys.stderr)
        return 1

    total_failures = 0
    total_warnings = 0
    for slug in slugs:
        bundle_dir = os.path.join(workflows_dir, slug)
        rep = Report()
        check_skill(bundle_dir, slug, readme_text, rep)
        total_failures += len(rep.failures)
        total_warnings += len(rep.warnings)

        if rep.failures:
            print(f"FAIL  workflows/{slug}")
            for msg in rep.failures:
                print(f"        - {msg}")
            for msg in rep.warnings:
                print(f"        ! {msg}")
        elif rep.warnings and not args.quiet:
            print(f"PASS  workflows/{slug}  ({len(rep.warnings)} warning(s))")
            for msg in rep.warnings:
                print(f"        ! {msg}")
        elif not args.quiet:
            print(f"PASS  workflows/{slug}")

    print()
    verdict = "FAIL" if total_failures else "PASS"
    print(
        f"{verdict}: {len(slugs)} bundle(s), "
        f"{total_failures} failure(s), {total_warnings} warning(s)"
    )
    return 1 if total_failures else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
