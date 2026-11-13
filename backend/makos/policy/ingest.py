"""Split procurement manuals into clauses with edition, page and locator.

Manuals use numbered paragraphs (e.g. "9.14.2 Passing of Supplier's Bills").
The parser:
  1. skips table-of-contents pages (many dotted-leader lines),
  2. accepts a numbered line as a heading only if its number comes after the
     previous heading (stops page numbers, amounts and lists being read as headings),
  3. stops at the annexures.
GFR uses "Rule NNN" headings instead.

    python -m makos.policy.ingest            # reads data/raw/policy/*.pdf
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd

from makos.config import DATA_DIR
from makos.policy.editions import EDITIONS, Edition

RAW = DATA_DIR / "raw" / "policy"

HEADING = re.compile(r"^\s*(\d{1,2}(?:\.\d{1,2}){1,3})\.?[ \t]+(\S.*)$")
LEADER = re.compile(r"\.{4,}\s*[ivxlc\d]*\s*$", re.I)
CHAPTER = re.compile(r"^\s*Chapter\s+(\d{1,2})\s*[:\-–]\s*(.+)$", re.I)
ANNEX = re.compile(r"^\s*Annexure\s*[-–:]?\s*\d+\b", re.I)
GFR_RULE = re.compile(r"^\s*Rule\s+(\d{3})\.?\s*(.*)$")


@dataclass
class Clause:
    clause_id: str
    source_id: str
    edition: str
    number: str
    title: str
    chapter: int | None
    parent_title: str
    page_start: int
    page_end: int
    text: str

    def locator(self) -> str:
        return f"{self.source_id} {self.edition}, para {self.number}, p.{self.page_start}"


def extract_pages(pdf: Path) -> list[str]:
    from pypdf import PdfReader

    return [p.extract_text() or "" for p in PdfReader(str(pdf)).pages]


TOC_ENTRY = re.compile(r"^\s*\d{1,2}(?:\.\d{1,2})+\s+\S.*\s\d{1,3}\s*$")


def _is_toc_page(text: str) -> bool:
    """Contents pages: dotted leaders, or many numbered lines ending in a page number."""
    lines = text.splitlines()
    if "table of contents" in text.lower():
        return True
    return (sum(bool(LEADER.search(x)) for x in lines) >= 3
            or sum(bool(TOC_ENTRY.match(x)) for x in lines) >= 5)


def _is_annexure_page(text: str) -> bool:
    """An annexure starts a page with an 'Annexure N' heading in its first few lines."""
    return any(ANNEX.match(x) and len(x.strip()) < 80 for x in text.splitlines()[:6])


def _key(number: str) -> tuple[int, ...]:
    return tuple(int(x) for x in number.split("."))


SMALL_WORDS = {"of", "and", "the", "for", "in", "on", "to", "a", "an", "or", "with", "by", "from", "at", "vis-à-vis"}


def _split_title(rest: str) -> tuple[str, str]:
    """Return (title, first_text_line). A heading line is a title when it is short,
    has no sentence break and most of its significant words are capitalised."""
    rest = rest.strip()
    words = rest.split()
    significant = [w for w in words if w.lower() not in SMALL_WORDS and w[:1].isalpha()]
    caps = sum(w[:1].isupper() for w in significant) / max(len(significant), 1)
    if (len(rest) <= 100 and len(words) <= 14 and ". " not in rest
            and not rest.endswith((".", ";", ",")) and caps >= 0.5):
        return rest.rstrip(":"), ""
    return "", rest


def parse_manual(pages: list[str], ed: Edition) -> list[Clause]:
    clauses: list[Clause] = []
    titles: dict[str, str] = {}
    cur: dict | None = None
    last_key: tuple[int, ...] = (0,)
    chapter: int | None = None
    started = False

    def close():
        if cur:
            text = re.sub(r"[ \t]+", " ", "\n".join(cur["lines"])).strip()
            titles[cur["number"]] = cur["title"] or text.split("\n", 1)[0][:80]
            parent = cur["number"].rsplit(".", 1)[0]
            clauses.append(Clause(
                clause_id=f"{ed.source_id}:{ed.edition}:{cur['number']}", source_id=ed.source_id,
                edition=ed.edition, number=cur["number"], title=cur["title"], chapter=cur["chapter"],
                parent_title=titles.get(parent, "") if "." in parent else "",
                page_start=cur["p0"], page_end=cur["p1"], text=text))

    for pno, page in enumerate(pages, start=1):
        if _is_toc_page(page):
            continue
        if started and last_key[0] >= 9 and _is_annexure_page(page):
            close()
            return clauses
        for line in page.splitlines():
            if LEADER.search(line):
                continue
            m = CHAPTER.match(line)
            if m and not LEADER.search(line):
                chapter = int(m.group(1))
                continue
            h = HEADING.match(line)
            if h:
                number, rest = h.group(1), h.group(2)
                k = _key(number)
                # same chapter and later than the last heading, or the first section of the next chapter
                plausible = (k > last_key and k[0] == last_key[0]) or (k[0] == last_key[0] + 1 and k[1:] == (1,)) \
                    or (not started and k == (1, 1)) \
                    or (started and chapter is not None and k[0] == chapter > last_key[0])  # announced chapter
                if plausible and (started or k == (1, 1)):
                    close()
                    title, first = _split_title(rest)
                    cur = {"number": number, "title": title, "chapter": k[0], "p0": pno, "p1": pno,
                           "lines": [first] if first else []}
                    last_key, started = k, True
                    continue
            if cur is not None:
                if line.strip() and not re.fullmatch(r"\s*[ivxlc\d]+\s*", line, re.I):  # skip bare page numbers
                    cur["lines"].append(line)
                    cur["p1"] = pno
    close()
    return clauses


def parse_gfr(pages: list[str], ed: Edition) -> list[Clause]:
    clauses: list[Clause] = []
    cur: dict | None = None
    for pno, page in enumerate(pages, start=1):
        for line in page.splitlines():
            m = GFR_RULE.match(line)
            if m:
                if cur:
                    clauses.append(cur)
                cur = {"number": m.group(1), "p0": pno, "p1": pno, "lines": [m.group(2)]}
                continue
            if cur is not None and line.strip():
                cur["lines"].append(line)
                cur["p1"] = pno
    if cur:
        clauses.append(cur)
    out, seen = [], {}
    for c in clauses:
        text = re.sub(r"\s+", " ", " ".join(c["lines"])).strip()
        n = c["number"]
        seen[n] = seen.get(n, 0) + 1
        number = f"Rule {n}" if seen[n] == 1 else f"Rule {n} (part {seen[n]})"  # e.g. Rule 172(1), 172(2)
        out.append(Clause(f"{ed.source_id}:{ed.edition}:{number}", ed.source_id, ed.edition,
                          number, text[:80], 6, "", c["p0"], c["p1"], text))
    return out


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ingest(raw_dir: Path = RAW) -> tuple[pd.DataFrame, list[str]]:
    rows, notes = [], []
    for ed in EDITIONS:
        pdf = raw_dir / ed.filename
        if not pdf.exists():
            notes.append(f"missing: {ed.filename} ({ed.title}) - see data/README.md")
            continue
        digest = sha256_of(pdf)
        if ed.sha256 and digest != ed.sha256:
            notes.append(f"checksum differs for {ed.filename}: {digest}")
        pages = extract_pages(pdf)
        clauses = parse_manual(pages, ed) if ed.kind == "manual" else parse_gfr(pages, ed)
        notes.append(f"{ed.title}: {len(pages)} pages, {len(clauses)} clauses")
        for c in clauses:
            row = asdict(c)
            row.update(effective_from=ed.effective_from.isoformat(), locator=c.locator(), file_sha256=digest)
            rows.append(row)
    return pd.DataFrame(rows), notes


def summary_markdown(df: pd.DataFrame, notes: list[str]) -> str:
    lines = ["# Policy corpus", "", *[f"- {n}" for n in notes], ""]
    if not df.empty:
        lines += ["| Source | Edition | In force from | Clauses | Chapters | Median words/clause |",
                  "| --- | --- | --- | --- | --- | --- |"]
        for (src, ed), g in df.groupby(["source_id", "edition"], sort=False):
            words = g["text"].str.split().str.len().median()
            lines.append(f"| {src} | {ed} | {g['effective_from'].iloc[0]} | {len(g)} | "
                         f"{g['chapter'].nunique()} | {words:.0f} |")
    return "\n".join(lines) + "\n"


def check_policy_map(df: pd.DataFrame, path: Path = DATA_DIR / "policy" / "policy_map.yaml") -> list[str]:
    """Every clause cited in policy_map.yaml must exist in the parsed corpus."""
    import yaml

    have = set(zip(df["source_id"], df["edition"], df["number"]))
    loaded = set(zip(df["source_id"], df["edition"]))
    missing = []
    for rule, sources in yaml.safe_load(path.read_text())["rules"].items():
        for src, eds in sources.items():
            for ed, spec in eds.items():
                if (src, str(ed)) not in loaded:
                    continue  # edition not ingested yet (e.g. 2024)
                missing += [f"{rule}: {src} {ed} {n}" for n in spec["clauses"] if (src, str(ed), n) not in have]
    return missing


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw-dir", type=Path, default=RAW)
    args = ap.parse_args()
    df, notes = ingest(args.raw_dir)
    print("\n".join(notes))
    if df.empty:
        sys.exit("no policy PDFs found")
    out = DATA_DIR / "interim"
    out.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out / "policy_clauses.parquet", index=False)
    (DATA_DIR / "profile" / "policy_corpus.md").write_text(summary_markdown(df, notes))
    print(f"wrote {len(df)} clauses to {out / 'policy_clauses.parquet'}")
    missing = check_policy_map(df)
    if missing:
        sys.exit("policy_map.yaml cites clauses that were not found:\n  " + "\n  ".join(missing))
    print("policy_map.yaml: every cited clause found")


if __name__ == "__main__":
    main()
