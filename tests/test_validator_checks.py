"""
Unit tests for new validator warning codes W109–W113.

Each test uses a minimal inline XML fixture — no file I/O needed.
Run with: pytest tests/test_validator_checks.py -v
"""
import sys
import os
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "skill", "scripts"))
from validate import validate_model, Diag  # noqa: E402


def _run(xml_str):
    """Parse xml_str as an mxGraphModel and return a populated Diag."""
    model = ET.fromstring(xml_str)
    d = Diag()
    validate_model(model, d)
    return d


# ─────────────────────────────────────────────────────────────── W111 fixtures

# Hub with 4 outgoing edges, no exitX/Y on any of them
W111_TRIGGERS = """<mxGraphModel>
  <root>
    <mxCell id="0"/><mxCell id="1" parent="0"/>
    <mxCell id="hub" value="Hub" vertex="1" parent="1">
      <mxGeometry x="200" y="200" width="120" height="50" as="geometry"/>
    </mxCell>
    <mxCell id="n1" value="A" vertex="1" parent="1"><mxGeometry x="40" y="80"  width="100" height="40" as="geometry"/></mxCell>
    <mxCell id="n2" value="B" vertex="1" parent="1"><mxGeometry x="40" y="160" width="100" height="40" as="geometry"/></mxCell>
    <mxCell id="n3" value="C" vertex="1" parent="1"><mxGeometry x="40" y="240" width="100" height="40" as="geometry"/></mxCell>
    <mxCell id="n4" value="D" vertex="1" parent="1"><mxGeometry x="40" y="320" width="100" height="40" as="geometry"/></mxCell>
    <mxCell id="e1" edge="1" source="hub" target="n1" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <mxCell id="e2" edge="1" source="hub" target="n2" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <mxCell id="e3" edge="1" source="hub" target="n3" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <mxCell id="e4" edge="1" source="hub" target="n4" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
  </root>
</mxGraphModel>"""

# Same topology but every edge has an explicit exitX/Y — should NOT warn
W111_PASSES = """<mxGraphModel>
  <root>
    <mxCell id="0"/><mxCell id="1" parent="0"/>
    <mxCell id="hub" value="Hub" vertex="1" parent="1">
      <mxGeometry x="200" y="200" width="120" height="50" as="geometry"/>
    </mxCell>
    <mxCell id="n1" value="A" vertex="1" parent="1"><mxGeometry x="40" y="80"  width="100" height="40" as="geometry"/></mxCell>
    <mxCell id="n2" value="B" vertex="1" parent="1"><mxGeometry x="40" y="160" width="100" height="40" as="geometry"/></mxCell>
    <mxCell id="n3" value="C" vertex="1" parent="1"><mxGeometry x="40" y="240" width="100" height="40" as="geometry"/></mxCell>
    <mxCell id="n4" value="D" vertex="1" parent="1"><mxGeometry x="40" y="320" width="100" height="40" as="geometry"/></mxCell>
    <mxCell id="e1" edge="1" source="hub" target="n1" style="exitX=0.25;exitY=1.0;" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <mxCell id="e2" edge="1" source="hub" target="n2" style="exitX=0.5;exitY=1.0;"  parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <mxCell id="e3" edge="1" source="hub" target="n3" style="exitX=0.75;exitY=1.0;" parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
    <mxCell id="e4" edge="1" source="hub" target="n4" style="exitX=1.0;exitY=0.5;"  parent="1"><mxGeometry relative="1" as="geometry"/></mxCell>
  </root>
</mxGraphModel>"""


def test_w111_triggers_on_convergence_without_ports():
    d = _run(W111_TRIGGERS)
    codes = [c for c, _ in d.warnings]
    assert "W111" in codes, f"Expected W111, got warnings: {d.warnings}"


def test_w111_passes_when_ports_assigned():
    d = _run(W111_PASSES)
    codes = [c for c, _ in d.warnings]
    assert "W111" not in codes, f"W111 should not fire when ports set, got: {d.warnings}"


# ─────────────────────────────────────────────────────────────── W109 fixtures

# Edge A→C midpoint ≈ (255,200) lands inside shape B at (150,175,200,50)
W109_TRIGGERS = """<mxGraphModel>
  <root>
    <mxCell id="0"/><mxCell id="1" parent="0"/>
    <mxCell id="A" value="A" vertex="1" parent="1"><mxGeometry x="40"  y="180" width="100" height="40" as="geometry"/></mxCell>
    <mxCell id="B" value="B" vertex="1" parent="1"><mxGeometry x="150" y="175" width="200" height="50" as="geometry"/></mxCell>
    <mxCell id="C" value="C" vertex="1" parent="1"><mxGeometry x="420" y="180" width="100" height="40" as="geometry"/></mxCell>
    <mxCell id="e1" value="connects" edge="1" source="A" target="C" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
  </root>
</mxGraphModel>"""

# Same layout but edge mxGeometry has y=-20 offset — should NOT warn
W109_PASSES = """<mxGraphModel>
  <root>
    <mxCell id="0"/><mxCell id="1" parent="0"/>
    <mxCell id="A" value="A" vertex="1" parent="1"><mxGeometry x="40"  y="180" width="100" height="40" as="geometry"/></mxCell>
    <mxCell id="B" value="B" vertex="1" parent="1"><mxGeometry x="150" y="175" width="200" height="50" as="geometry"/></mxCell>
    <mxCell id="C" value="C" vertex="1" parent="1"><mxGeometry x="420" y="180" width="100" height="40" as="geometry"/></mxCell>
    <mxCell id="e1" value="connects" edge="1" source="A" target="C" parent="1">
      <mxGeometry relative="1" x="0" y="-20" as="geometry"/>
    </mxCell>
  </root>
</mxGraphModel>"""

# Edge has no label value — should NOT warn even if midpoint is on a shape
W109_NO_LABEL = """<mxGraphModel>
  <root>
    <mxCell id="0"/><mxCell id="1" parent="0"/>
    <mxCell id="A" value="A" vertex="1" parent="1"><mxGeometry x="40"  y="180" width="100" height="40" as="geometry"/></mxCell>
    <mxCell id="B" value="B" vertex="1" parent="1"><mxGeometry x="150" y="175" width="200" height="50" as="geometry"/></mxCell>
    <mxCell id="C" value="C" vertex="1" parent="1"><mxGeometry x="420" y="180" width="100" height="40" as="geometry"/></mxCell>
    <mxCell id="e1" value="" edge="1" source="A" target="C" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
  </root>
</mxGraphModel>"""


def test_w109_triggers_when_label_midpoint_on_shape():
    d = _run(W109_TRIGGERS)
    codes = [c for c, _ in d.warnings]
    assert "W109" in codes, f"Expected W109, got: {d.warnings}"


def test_w109_passes_when_label_has_offset():
    d = _run(W109_PASSES)
    codes = [c for c, _ in d.warnings]
    assert "W109" not in codes, f"W109 should not fire with y-offset, got: {d.warnings}"


def test_w109_skips_edges_without_labels():
    d = _run(W109_NO_LABEL)
    codes = [c for c, _ in d.warnings]
    assert "W109" not in codes, f"W109 should not fire for unlabelled edges, got: {d.warnings}"


# ─────────────────────────────────────────────────────────────── W110 fixtures

# Edge A→C: centers at (90,200) and (410,200), straight path at y=200
# Shape B at (150,170,100,60) spans y=170..230, x=150..250 — path passes through it
W110_TRIGGERS = """<mxGraphModel>
  <root>
    <mxCell id="0"/><mxCell id="1" parent="0"/>
    <mxCell id="A" value="A" vertex="1" parent="1"><mxGeometry x="40"  y="180" width="100" height="40" as="geometry"/></mxCell>
    <mxCell id="B" value="B" vertex="1" parent="1"><mxGeometry x="150" y="170" width="100" height="60" as="geometry"/></mxCell>
    <mxCell id="C" value="C" vertex="1" parent="1"><mxGeometry x="360" y="180" width="100" height="40" as="geometry"/></mxCell>
    <mxCell id="e1" edge="1" source="A" target="C" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
  </root>
</mxGraphModel>"""

# Edge A→C routes well above shape B — path does NOT pass through B
W110_PASSES = """<mxGraphModel>
  <root>
    <mxCell id="0"/><mxCell id="1" parent="0"/>
    <mxCell id="A" value="A" vertex="1" parent="1"><mxGeometry x="40"  y="40"  width="100" height="40" as="geometry"/></mxCell>
    <mxCell id="B" value="B" vertex="1" parent="1"><mxGeometry x="150" y="170" width="100" height="60" as="geometry"/></mxCell>
    <mxCell id="C" value="C" vertex="1" parent="1"><mxGeometry x="360" y="40"  width="100" height="40" as="geometry"/></mxCell>
    <mxCell id="e1" edge="1" source="A" target="C" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
  </root>
</mxGraphModel>"""


def test_w110_triggers_when_edge_passes_through_shape():
    d = _run(W110_TRIGGERS)
    codes = [c for c, _ in d.warnings]
    assert "W110" in codes, f"Expected W110, got: {d.warnings}"


def test_w110_passes_when_edge_clears_shapes():
    d = _run(W110_PASSES)
    codes = [c for c, _ in d.warnings]
    assert "W110" not in codes, f"W110 should not fire, got: {d.warnings}"


# ─────────────────────────────────────────────────────────────── W112 fixtures

# Container h=500, startSize=30 → usable=470; child bottom at y=90 → 81% dead
W112_TRIGGERS = """<mxGraphModel>
  <root>
    <mxCell id="0"/><mxCell id="1" parent="0"/>
    <mxCell id="cont" value="Big Container" vertex="1" parent="1"
      style="swimlane;startSize=30;">
      <mxGeometry x="40" y="40" width="300" height="500" as="geometry"/>
    </mxCell>
    <mxCell id="s1" value="Shape" vertex="1" parent="cont">
      <mxGeometry x="60" y="50" width="120" height="40" as="geometry"/>
    </mxCell>
  </root>
</mxGraphModel>"""

# Container h=150, startSize=30 → usable=120; child bottom at 50+40=90 → 25% dead
W112_PASSES = """<mxGraphModel>
  <root>
    <mxCell id="0"/><mxCell id="1" parent="0"/>
    <mxCell id="cont" value="Right-Sized" vertex="1" parent="1"
      style="swimlane;startSize=30;">
      <mxGeometry x="40" y="40" width="300" height="150" as="geometry"/>
    </mxCell>
    <mxCell id="s1" value="Shape" vertex="1" parent="cont">
      <mxGeometry x="60" y="50" width="120" height="40" as="geometry"/>
    </mxCell>
  </root>
</mxGraphModel>"""


def test_w112_triggers_on_excessive_dead_space():
    d = _run(W112_TRIGGERS)
    codes = [c for c, _ in d.warnings]
    assert "W112" in codes, f"Expected W112, got: {d.warnings}"


def test_w112_passes_on_appropriately_sized_container():
    d = _run(W112_PASSES)
    codes = [c for c, _ in d.warnings]
    assert "W112" not in codes, f"W112 should not fire on right-sized container, got: {d.warnings}"


# ─────────────────────────────────────────────────────────────── W113 fixtures

# VPC container + 3 orphan shapes directly on canvas
W113_TRIGGERS = """<mxGraphModel>
  <root>
    <mxCell id="0"/><mxCell id="1" parent="0"/>
    <mxCell id="vpc" value="AWS VPC" vertex="1" parent="1" style="swimlane;startSize=30;">
      <mxGeometry x="40" y="120" width="800" height="600" as="geometry"/>
    </mxCell>
    <mxCell id="r53"    value="Route53"    vertex="1" parent="1"><mxGeometry x="40"  y="40" width="120" height="40" as="geometry"/></mxCell>
    <mxCell id="cfront" value="CloudFront" vertex="1" parent="1"><mxGeometry x="200" y="40" width="120" height="40" as="geometry"/></mxCell>
    <mxCell id="cog"    value="Cognito"    vertex="1" parent="1"><mxGeometry x="360" y="40" width="120" height="40" as="geometry"/></mxCell>
  </root>
</mxGraphModel>"""

# Orphans are inside an "Internet Layer" boundary — should NOT warn
W113_PASSES = """<mxGraphModel>
  <root>
    <mxCell id="0"/><mxCell id="1" parent="0"/>
    <mxCell id="vpc" value="AWS VPC" vertex="1" parent="1" style="swimlane;startSize=30;">
      <mxGeometry x="40" y="200" width="800" height="600" as="geometry"/>
    </mxCell>
    <mxCell id="inet" value="Internet Layer" vertex="1" parent="1" style="swimlane;startSize=26;dashed=1;">
      <mxGeometry x="40" y="40" width="600" height="120" as="geometry"/>
    </mxCell>
    <mxCell id="r53"    value="Route53"    vertex="1" parent="inet"><mxGeometry x="20"  y="40" width="120" height="40" as="geometry"/></mxCell>
    <mxCell id="cfront" value="CloudFront" vertex="1" parent="inet"><mxGeometry x="180" y="40" width="120" height="40" as="geometry"/></mxCell>
    <mxCell id="cog"    value="Cognito"    vertex="1" parent="inet"><mxGeometry x="340" y="40" width="120" height="40" as="geometry"/></mxCell>
  </root>
</mxGraphModel>"""


def test_w113_triggers_on_ungrouped_external_shapes():
    d = _run(W113_TRIGGERS)
    codes = [c for c, _ in d.warnings]
    assert "W113" in codes, f"Expected W113, got: {d.warnings}"


def test_w113_passes_when_external_shapes_are_grouped():
    d = _run(W113_PASSES)
    codes = [c for c, _ in d.warnings]
    assert "W113" not in codes, f"W113 should not fire when shapes are grouped, got: {d.warnings}"
