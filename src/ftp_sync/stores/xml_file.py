"""Read/write helpers shared by the XML-backed stores (FileZilla, NppFTP)."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path


def child(parent: ET.Element, tag: str) -> ET.Element:
    """Return the first `tag` child, creating it if absent."""
    found = parent.find(tag)
    return found if found is not None else ET.SubElement(parent, tag)


def write_root(tree: ET.ElementTree[ET.Element], path: Path, indent: str) -> None:
    ET.indent(tree, space=indent)
    tree.write(path, encoding="UTF-8", xml_declaration=True)
