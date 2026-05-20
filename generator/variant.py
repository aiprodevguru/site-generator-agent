"""
Backward-compatibility shim.

All variation logic now lives in ``generator.variation_engine``.
Importing from here still works — existing code needs no changes.
"""
from generator.variation_engine import (   # noqa: F401
    VariationConfig,
    VariationConfig as SiteVariant,
    build_variation_config,
    build_variation_config as pick_variant,
)

__all__ = ["SiteVariant", "VariationConfig", "pick_variant", "build_variation_config"]
