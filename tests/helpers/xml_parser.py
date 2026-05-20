"""
Layer 1: Standalone XML structure parser for .drawio files.

This module is completely independent of the skill's own scripts/.
It parses mxGraph XML and runs structural integrity checks.
"""

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class XmlReport:
    """Results from XML structural validation."""
    vertices: int = 0
    edges: int = 0
    duplicate_ids: list = field(default_factory=list)
    orphan_parents: list = field(default_factory=list)
    missing_edge_geometry: list = field(default_factory=list)
    dangling_edge_endpoints: list = field(default_factory=list)
    overflow_children: list = field(default_factory=list)
    parse_error: str | None = None

    @property
    def total_elements(self):
        return self.vertices + self.edges

    @property
    def is_valid_xml(self):
        return self.parse_error is None

    @property
    def has_structural_errors(self):
        return bool(
            self.duplicate_ids
            or self.orphan_parents
            or self.missing_edge_geometry
            or self.dangling_edge_endpoints
        )


def parse_drawio(path: str | Path) -> XmlReport:
    """Parse a .drawio file and run structural checks. Returns an XmlReport."""
    report = XmlReport()
    path = Path(path)

    # Parse XML
    try:
        tree = ET.parse(path)
        root = tree.getroot()
    except ET.ParseError as e:
        report.parse_error = str(e)
        return report
    except FileNotFoundError:
        report.parse_error = f"File not found: {path}"
        return report

    # Collect all mxCell elements
    cells = []
    for model in root.iter("mxGraphModel"):
        for r in model.iter("root"):
            for c in r.findall("mxCell"):
                cells.append(c)
            # Also handle <object> wrappers
            for obj in r.findall("object"):
                inner = obj.find("mxCell")
                if inner is not None:
                    inner.set("id", obj.get("id", inner.get("id", "")))
                    cells.append(inner)

    # Index cells
    seen_ids = set()
    by_id = {}
    for c in cells:
        cid = c.get("id")
        if cid is None:
            continue
        if cid in seen_ids:
            report.duplicate_ids.append(cid)
        else:
            seen_ids.add(cid)
            by_id[cid] = c

    # Count vertices and edges
    for cid, c in by_id.items():
        if c.get("vertex") == "1":
            report.vertices += 1
        if c.get("edge") == "1":
            report.edges += 1

    # Check parent refs
    for cid, c in by_id.items():
        parent = c.get("parent")
        if parent is not None and parent not in by_id and parent not in ("0", "1"):
            report.orphan_parents.append((cid, parent))

    # Check edge geometry and endpoints
    for cid, c in by_id.items():
        if c.get("edge") != "1":
            continue

        # Edge must have <mxGeometry relative="1"> child
        geom = c.find("mxGeometry")
        if geom is None:
            report.missing_edge_geometry.append(cid)

        # Edge source/target must exist
        src = c.get("source")
        tgt = c.get("target")
        if src is not None and src not in by_id:
            report.dangling_edge_endpoints.append((cid, "source", src))
        if tgt is not None and tgt not in by_id:
            report.dangling_edge_endpoints.append((cid, "target", tgt))

    # Check container overflow (children outside parent bounds)
    def _geom(cell):
        g = cell.find("mxGeometry")
        if g is None:
            return None
        try:
            return (
                float(g.get("x", 0)),
                float(g.get("y", 0)),
                float(g.get("width", 0)),
                float(g.get("height", 0)),
            )
        except (TypeError, ValueError):
            return None

    for cid, c in by_id.items():
        if c.get("vertex") != "1":
            continue
        parent_id = c.get("parent")
        if parent_id not in by_id:
            continue
        parent = by_id[parent_id]
        parent_style = parent.get("style", "") or ""
        is_container = "swimlane" in parent_style or "container=1" in parent_style
        if not is_container:
            continue
        pg = _geom(parent)
        cg = _geom(c)
        if pg is None or cg is None:
            continue
        _, _, pw, ph = pg
        cx, cy, cw, ch = cg
        if cx + cw > pw + 2 or cy + ch > ph + 2:
            report.overflow_children.append((cid, parent_id))

    return report


def extract_labels(path: str | Path) -> list[str]:
    """Extract all visible text labels from shapes in a .drawio file."""
    import re
    path = Path(path)
    try:
        tree = ET.parse(path)
        root = tree.getroot()
    except (ET.ParseError, FileNotFoundError):
        return []

    labels = []
    for model in root.iter("mxGraphModel"):
        for r in model.iter("root"):
            for c in r.findall("mxCell"):
                if c.get("vertex") == "1":
                    val = c.get("value", "") or ""
                    if val.strip():
                        # Strip HTML tags
                        clean = re.sub(r"<[^>]+>", " ", val)
                        clean = clean.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
                        clean = re.sub(r"&[a-z]+;|&#x?[0-9a-f]+;", " ", clean, flags=re.IGNORECASE)
                        clean = re.sub(r"\s+", " ", clean).strip()
                        if clean:
                            labels.append(clean.lower())
            for obj in r.findall("object"):
                val = obj.get("label", "") or obj.get("value", "") or ""
                if val.strip():
                    clean = re.sub(r"<[^>]+>", " ", val)
                    clean = clean.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
                    clean = re.sub(r"\s+", " ", clean).strip()
                    if clean:
                        labels.append(clean.lower())
    return labels
