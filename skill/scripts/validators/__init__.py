"""
validators/__init__.py — validator registry and run_all().

Registry
--------
Built-in validators are auto-registered at import time.
External plugins can be registered at runtime via ``register_validator()``.

Decorator usage::

    from validators import register_validator
    from validators.base import Validator, Diagnostic

    @register_validator
    class MyValidator(Validator):
        codes = ("X901",)
        def check(self, model, ctx):
            ...

Or the ``@validates_code`` shorthand::

    @validates_code("X901")
    class MyValidator(Validator):
        ...

Both styles add the class to REGISTRY.

Plugin interface
----------------
A plugin file must define at least one ``Validator`` subclass decorated with
``@register_validator`` or ``@validates_code``.  The CLI loads it via::

    python3 validate.py diagram.drawio --validator-plugin /path/to/myplugin.py
"""

from __future__ import annotations

import importlib.util
import sys
from typing import Callable, Type

from .base import Validator, Diagnostic, Diag

__all__ = [
    "REGISTRY",
    "register_validator",
    "validates_code",
    "run_all",
    "load_plugin",
]

# ---------------------------------------------------------------- registry
REGISTRY: list[type[Validator]] = []


def register_validator(cls: type[Validator]) -> type[Validator]:
    """Register a Validator subclass.  Returns the class unchanged."""
    if cls not in REGISTRY:
        REGISTRY.append(cls)
    return cls


def validates_code(*codes: str) -> Callable[[type[Validator]], type[Validator]]:
    """Decorator that tags a validator with specific codes and registers it."""
    def decorator(cls: type[Validator]) -> type[Validator]:
        cls.codes = codes  # type: ignore[assignment]
        return register_validator(cls)
    return decorator


# ---------------------------------------------------------------- built-in registration
from .structure   import StructureValidator    # noqa: E402
from .quality     import QualityValidator      # noqa: E402
from .grounding   import GroundingValidator    # noqa: E402
from .text_checks import TextMetricsValidator  # noqa: E402
from .features    import FeatureFlagValidator  # noqa: E402

register_validator(StructureValidator)
register_validator(QualityValidator)
register_validator(GroundingValidator)
register_validator(TextMetricsValidator)
register_validator(FeatureFlagValidator)


# ---------------------------------------------------------------- run_all
def run_all(model, ctx: dict) -> list[Diagnostic]:
    """
    Run every registered validator against *model* and return all diagnostics.

    Parameters
    ----------
    model:
        ``<mxGraphModel>`` Element (may be None for plan-only validators).
    ctx:
        Shared context dict (see ``base.Validator.check`` docstring for keys).
    """
    results: list[Diagnostic] = []
    for validator_cls in REGISTRY:
        instance = validator_cls()
        results.extend(instance.check(model, ctx))
    return results


# ---------------------------------------------------------------- plugin loader
def load_plugin(path: str) -> None:
    """
    Dynamically import a plugin file and register any Validator subclasses it defines.

    The plugin must contain at least one class decorated with ``@register_validator``
    or ``@validates_code``, OR manually append to ``validators.REGISTRY``.
    """
    spec = importlib.util.spec_from_file_location("_validator_plugin", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load plugin from {path!r}")
    module = importlib.util.module_from_spec(spec)
    # Expose this package so the plugin can do `from validators import ...`
    sys.modules.setdefault("validators", sys.modules[__name__])
    spec.loader.exec_module(module)  # type: ignore[union-attr]
