"""Memory-light reader for IEEE-XES event logs.

BPI 2019 has ~1.6M events, so the file is parsed with iterparse and each
<trace> is cleared after use. Works with .xes, .xes.gz and a .zip holding one .xes.
"""
from __future__ import annotations

import gzip
import zipfile
from pathlib import Path
from typing import IO, Iterator
from xml.etree.ElementTree import Element, iterparse

ATTR_TAGS = {"string", "date", "int", "float", "boolean", "id"}


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _convert(kind: str, value: str):
    if kind == "int":
        return int(value)
    if kind == "float":
        return float(value)
    if kind == "boolean":
        return value.lower() == "true"
    return value  # strings and ISO dates stay as text; pandas parses dates later


def _attrs(elem: Element) -> dict:
    out = {}
    for child in elem:
        kind = _local(child.tag)
        if kind in ATTR_TAGS and "key" in child.attrib:
            out[child.attrib["key"]] = _convert(kind, child.attrib.get("value", ""))
    return out


def open_log(path: str | Path) -> IO[bytes]:
    path = Path(path)
    if path.suffix == ".gz":
        return gzip.open(path, "rb")
    if path.suffix == ".zip":
        zf = zipfile.ZipFile(path)
        names = [n for n in zf.namelist() if n.endswith(".xes")]
        if len(names) != 1:
            raise ValueError(f"expected one .xes inside {path.name}, found {names}")
        return zf.open(names[0])
    return path.open("rb")


def iter_traces(path: str | Path) -> Iterator[tuple[dict, list[dict]]]:
    """Yield (case_attributes, [event_attributes, ...]) for every trace."""
    with open_log(path) as fh:
        for _, elem in iterparse(fh, events=("end",)):
            if _local(elem.tag) != "trace":
                continue
            case = _attrs(elem)
            events = [_attrs(ev) for ev in elem if _local(ev.tag) == "event"]
            yield case, events
            elem.clear()
