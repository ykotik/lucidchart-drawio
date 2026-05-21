"""
validators/base.py — Diagnostic dataclass and Validator ABC.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


# ---------------------------------------------------------------- severity tokens
ERR = "ERROR"
WRN = "WARN "
INF = "INFO "


@dataclass
class Diagnostic:
    """A single validator finding."""

    code: str                        # e.g. "E001", "W101", "Q401", "G501", "T801"
    severity: str                    # ERR | WRN | INF
    message: str
    element_id: str = ""             # id of the offending mxCell / plan element
    location: str = ""               # free-form: page index, line, etc.


class Diag:
    """Accumulator for Diagnostic objects — also owns the print/exit-code logic."""

    def __init__(self) -> None:
        self.errors:   list[tuple[str, str]] = []
        self.warnings: list[tuple[str, str]] = []
        self.infos:    list[tuple[str, str]] = []

    # ---------- append helpers (keep same call-site API as original) ----------
    def err(self, code: str, msg: str) -> None:
        self.errors.append((code, msg))

    def warn(self, code: str, msg: str) -> None:
        self.warnings.append((code, msg))

    def info(self, code: str, msg: str) -> None:
        self.infos.append((code, msg))

    def add(self, d: Diagnostic) -> None:
        """Ingest a Diagnostic produced by a pluggable validator."""
        if d.severity == ERR:
            self.errors.append((d.code, d.message))
        elif d.severity == WRN:
            self.warnings.append((d.code, d.message))
        else:
            self.infos.append((d.code, d.message))

    # ---------- output (byte-for-byte compatible with original) ----------
    def print(self, mode: str) -> int:
        for code, msg in self.errors:
            print(f"{ERR} {code}: {msg}")
        if mode != "loose":
            for code, msg in self.warnings:
                print(f"{WRN} {code}: {msg}")
        for code, msg in self.infos:
            print(f"{INF} {code}: {msg}")

        n_e = len(self.errors)
        n_w = len(self.warnings) if mode != "loose" else 0
        n_i = len(self.infos)
        print(f"\nSummary: {n_e} errors, {n_w} warnings, {n_i} infos")

        if mode == "strict":
            return 0 if (n_e == 0 and n_w == 0) else 1
        return 0 if n_e == 0 else 1


class Validator(abc.ABC):
    """
    Abstract base for all pluggable validators.

    Subclass this, implement ``check()``, and register the class with
    ``@register_validator`` (or add it to the ``REGISTRY`` list in
    validators/__init__.py).
    """

    #: Iterable of diagnostic codes this validator can emit (for documentation).
    codes: tuple[str, ...] = ()

    @abc.abstractmethod
    def check(self, model, ctx: dict) -> list[Diagnostic]:
        """
        Run checks against a single mxGraphModel element.

        Parameters
        ----------
        model:
            An ``xml.etree.ElementTree.Element`` for ``<mxGraphModel>``.
        ctx:
            Shared context dict with keys:
                ``features``  — feature-flag dict
                ``by_id``     — {id: mxCell Element}
                ``parents``   — {id: parent_id}
                ``is_vertex`` — {id: bool}
                ``is_edge``   — {id: bool}
                ``geoms``     — {id: (x,y,w,h) | None}
                ``styles``    — {id: {k:v}}

        Returns a (possibly empty) list of Diagnostic objects.
        """
