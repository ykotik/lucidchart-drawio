"""
Layer 1 Tests: XML structural validation.

These tests use the standalone xml_parser (NOT the skill's own validate.py)
to check structural integrity of generated .drawio files.
"""

from helpers.xml_parser import parse_drawio


class TestXmlStructure:
    """Structural XML checks — Layer 1."""

    def test_valid_xml(self, drawio_path):
        """The .drawio file must be well-formed XML."""
        report = parse_drawio(drawio_path)
        assert report.is_valid_xml, f"XML parse error: {report.parse_error}"

    def test_no_duplicate_ids(self, drawio_path, thresholds):
        """All mxCell ids must be unique."""
        report = parse_drawio(drawio_path)
        max_dupes = thresholds.get("xml", {}).get("max_duplicate_ids", 0)
        assert len(report.duplicate_ids) <= max_dupes, (
            f"Found {len(report.duplicate_ids)} duplicate IDs: {report.duplicate_ids[:5]}"
        )

    def test_no_orphan_parents(self, drawio_path, thresholds):
        """Every cell's parent must exist in the document."""
        report = parse_drawio(drawio_path)
        max_orphans = thresholds.get("xml", {}).get("max_orphan_parents", 0)
        assert len(report.orphan_parents) <= max_orphans, (
            f"Found {len(report.orphan_parents)} orphan parents: {report.orphan_parents[:5]}"
        )

    def test_edge_geometry_present(self, drawio_path, thresholds):
        """Every edge must have <mxGeometry> child."""
        report = parse_drawio(drawio_path)
        max_missing = thresholds.get("xml", {}).get("max_missing_edge_geometry", 0)
        assert len(report.missing_edge_geometry) <= max_missing, (
            f"Edges missing geometry: {report.missing_edge_geometry[:5]}"
        )

    def test_no_dangling_endpoints(self, drawio_path):
        """Edge source/target must reference existing cells."""
        report = parse_drawio(drawio_path)
        assert len(report.dangling_edge_endpoints) == 0, (
            f"Dangling edge endpoints: {report.dangling_edge_endpoints[:5]}"
        )

    def test_minimum_vertices(self, drawio_path, thresholds):
        """Diagram must have enough shapes (complexity check)."""
        report = parse_drawio(drawio_path)
        min_v = thresholds.get("xml", {}).get("min_vertices", 30)
        assert report.vertices >= min_v, (
            f"Only {report.vertices} vertices, need at least {min_v}"
        )

    def test_minimum_edges(self, drawio_path, thresholds):
        """Diagram must have enough connections."""
        report = parse_drawio(drawio_path)
        min_e = thresholds.get("xml", {}).get("min_edges", 10)
        assert report.edges >= min_e, (
            f"Only {report.edges} edges, need at least {min_e}"
        )

    def test_minimum_total_elements(self, drawio_path):
        """Diagram must have 30+ total elements (shapes + edges)."""
        report = parse_drawio(drawio_path)
        assert report.total_elements >= 30, (
            f"Only {report.total_elements} elements (shapes + edges), need at least 30"
        )
