"""
Variation Engine - mostly deterministic per-batch design configuration.

``build_variation_config(batch_name)`` hashes the batch name and picks
independently from the stable variation pools, while the game gallery layout
is allowed to vary between runs.
"""
from __future__ import annotations

import hashlib
import random
import re
from dataclasses import dataclass

from generator.gallery.item_layouts import ITEM_LAYOUTS
from generator.gallery.section_layouts import SECTION_LAYOUTS
from generator.variation_data.animations import ANIMATION_SETS
from generator.variation_data.fonts import FONT_SETS
from generator.variation_data.layouts import (
    CARD_STYLE_OPTIONS,
    FEAT_LAYOUT_OPTIONS,
    FOOTER_LAYOUT_VARIANTS,
    FOOTER_STYLE_OPTIONS,
    GALLERY_BADGE_STYLES,
    GALLERY_CARD_STYLES,
    GAME_LAYOUT_OPTIONS,
    GPT_PERSONAS,
    GPT_TEMPS,
    HEADER_LAYOUT_VARIANTS,
    HERO_HEIGHTS,
    HERO_LAYOUT_OPTIONS,
    IMG_COMPS,
    IMG_STYLES,
    MENU_STYLE_VARIANTS,
    NAV_STYLE_OPTIONS,
    RADIUS_OPTIONS,
    SECTION_DIVIDERS,
    SECTION_PADDINGS,
    SPACING_OPTIONS,
    TYPOGRAPHY_SCALES,
)
from generator.variation_data.palettes import PALETTES
from generator.variation_data.themes import THEMES

_ALL_OPT_SECTIONS = ["stats", "testimonials", "about", "cta_banner"]

_GAME_LAYOUT_FAMILIES: dict[str, tuple[str, ...]] = {
    "grid": ("equal", "showcase", "alternating", "mosaic"),
    "featured": ("featured", "editorial", "showcase", "cinematic"),
    "list": ("stacked", "hero", "cinematic", "editorial"),
}

_CARD_STYLE_VISUALS: dict[str, tuple[str, ...]] = {
    "glass": ("glass", "neon"),
    "glow": ("neon", "poster", "glass"),
    "solid": ("clean", "editorial", "minimal", "poster", "brutal", "playful"),
}

_STOP_WORDS = {
    "the", "and", "for", "with", "game", "games", "play", "online",
    "free", "hero", "quest", "adventure", "world", "battle",
}

_MARTIAL_THEME_MARKERS = {
    "armor", "armour", "armored", "armoured", "warrior", "warriors",
    "knight", "knights", "berserker", "berserkers", "samurai", "ninja",
    "guardian", "guardians", "fighter", "fighters", "assassin", "assassins",
    "raider", "raiders", "pirate", "pirates", "weapon", "weapons", "battle",
    "combat", "gunslinger", "gunslingers", "soldier", "soldiers",
}

_MARTIAL_SIGNAL_MARKERS = {
    "battle", "combat", "war", "warrior", "warriors", "arena", "assault",
    "strike", "siege", "clash", "fighter", "fighters", "pirate", "pirates",
    "ninja", "samurai", "viking", "dragon", "zombie", "demon", "robot",
    "mech", "alien", "horror",
}


def _seeded_pick(options: list, seed: int, shift: int):
    """Deterministically pick one item from *options* using shifted seed bits."""
    return options[(seed >> shift) % len(options)]


def _pick_with_optional_rng(options: list, seed: int, shift: int, rng: random.Random | None = None):
    """Pick randomly when *rng* is supplied, otherwise fall back to seeded selection."""
    if rng is not None:
        return rng.choice(options)
    return _seeded_pick(options, seed, shift)


def _tokenize(text: str) -> set[str]:
    """Normalize text into meaningful lowercase tokens for loose matching."""
    tokens = {
        tok for tok in re.findall(r"[a-z0-9]+", text.lower())
        if len(tok) >= 3 and tok not in _STOP_WORDS
    }
    return tokens


def _pick_theme(seed: int,
                batch_name: str,
                game_names: list[str] | None = None,
                topic: str | None = None,
                tone: str | None = None) -> dict:
    """
    Pick a theme that reflects the supplied game names while staying
    deterministic for the same batch/input set.
    """
    if not game_names and not topic and not tone:
        return _seeded_pick(THEMES, seed, 14)

    signal_text = " ".join([batch_name] + (game_names or []))
    signal_tokens = _tokenize(signal_text)
    martial_signal_count = len(signal_tokens & _MARTIAL_SIGNAL_MARKERS)
    scored: list[tuple[int, dict]] = []

    for theme in THEMES:
        theme_tokens = _tokenize(
            " ".join([
                str(theme.get("name", "")),
                str(theme.get("topic", "")),
                str(theme.get("tone", "")),
                str(theme.get("char_desc", "")),
                str(theme.get("setting_desc", "")),
            ])
        )
        overlap = len(signal_tokens & theme_tokens)
        score = overlap * 5

        if topic and str(theme.get("topic", "")).lower() == topic.lower():
            score += 6
        if tone and str(theme.get("tone", "")).lower() == tone.lower():
            score += 3

        # Reward direct phrase hints from names like "Dragon", "Pirate", etc.
        theme_name = str(theme.get("name", "")).lower()
        for token in signal_tokens:
            if token in theme_name:
                score += 2

        martial_theme_count = len(theme_tokens & _MARTIAL_THEME_MARKERS)
        if martial_theme_count:
            if topic and topic.lower() == "battle":
                score += 2
            elif martial_signal_count == 0:
                score -= martial_theme_count * 3
            else:
                score -= martial_theme_count

        scored.append((score, theme))

    best_score = max(score for score, _theme in scored)
    best = [theme for score, theme in scored if score == best_score]
    return _seeded_pick(best, seed, 14)


def _theme_matches(layout: dict, theme: dict) -> bool:
    """Return True when a gallery layout affinity matches the selected theme."""
    affinities = [str(a).lower() for a in layout.get("theme_affinity", ["all"])]
    if "all" in affinities:
        return True

    topic = str(theme.get("topic", "")).lower()
    tone = str(theme.get("tone", "")).lower()
    name = str(theme.get("name", "")).lower()

    return any(
        affinity and (affinity == topic or affinity == tone or affinity in name)
        for affinity in affinities
    )


def _pick_gallery_section_layout(
    seed: int,
    theme: dict,
    game_layout: str,
    rng: random.Random | None = None,
) -> dict:
    """
    Choose a section layout that stays deterministic per batch while matching
    the batch theme and the intended gallery structure.
    """
    preferred_families = set(_GAME_LAYOUT_FAMILIES.get(game_layout, ()))
    themed = [layout for layout in SECTION_LAYOUTS if _theme_matches(layout, theme)]

    if preferred_families:
        themed_and_family = [
            layout for layout in themed
            if layout.get("family") in preferred_families
        ]
        if themed_and_family:
            return _pick_with_optional_rng(themed_and_family, seed, 121, rng=rng)

    if themed:
        return _pick_with_optional_rng(themed, seed, 121, rng=rng)

    family_only = [
        layout for layout in SECTION_LAYOUTS
        if layout.get("family") in preferred_families
    ]
    if family_only:
        return _pick_with_optional_rng(family_only, seed, 121, rng=rng)

    return _pick_with_optional_rng(SECTION_LAYOUTS, seed, 121, rng=rng)


def _pick_gallery_item_layout(
    seed: int,
    theme: dict,
    card_style: str,
    rng: random.Random | None = None,
) -> dict:
    """
    Choose an item-card layout that matches the batch theme and visual card
    treatment instead of ignoring those higher-level decisions.
    """
    themed = [layout for layout in ITEM_LAYOUTS if _theme_matches(layout, theme)]
    preferred_styles = set(_CARD_STYLE_VISUALS.get(card_style, ()))

    if preferred_styles:
        themed_and_style = [
            layout for layout in themed
            if layout.get("visual_style") in preferred_styles
        ]
        if themed_and_style:
            return _pick_with_optional_rng(themed_and_style, seed, 124, rng=rng)

    if themed:
        return _pick_with_optional_rng(themed, seed, 124, rng=rng)

    style_only = [
        layout for layout in ITEM_LAYOUTS
        if layout.get("visual_style") in preferred_styles
    ]
    if style_only:
        return _pick_with_optional_rng(style_only, seed, 124, rng=rng)

    return _pick_with_optional_rng(ITEM_LAYOUTS, seed, 124, rng=rng)


@dataclass
class VariationConfig:
    """Complete design configuration for one generated site."""

    seed: int

    palette: dict
    font_set: dict
    theme: dict
    animation_set: dict

    header_variant: dict
    footer_variant: dict
    menu_variant: dict

    header_logo_pos: str
    header_nav_style: str
    header_height: tuple
    header_bg: str
    header_font_tx: str
    header_letter_sp: str
    header_cta: str
    header_border: str
    header_scroll: str

    footer_cols: int
    footer_align: str
    footer_bg: str
    footer_border_top: str
    footer_padding: str
    footer_logo_pos: str
    footer_link_style: str

    menu_hover: str
    menu_spacing: str

    gallery_card_style: str
    gallery_badge: str
    section_padding: str
    section_divider: str

    radius: int
    spacing: str
    card_style: str
    hero_height: str
    hero_layout: str
    game_layout: str
    feat_layout: str
    nav_style: str
    footer_style: str
    typography: str

    gpt_temp: float
    gpt_persona: str
    img_style: str
    img_composition: str

    extra_sections: frozenset

    gallery_item_layout: dict
    gallery_section_layout: dict


def build_variation_config(batch_name: str,
                           game_names: list[str] | None = None,
                           topic: str | None = None,
                           tone: str | None = None) -> VariationConfig:
    """
    Derive a :class:`VariationConfig` from *batch_name*.

    Uses the MD5 digest as a 128-bit seed for the stable visual choices.
    Gallery layout picks intentionally use runtime randomness so repeated
    generations can produce different game gallery presentations.
    """
    h = int(hashlib.md5(batch_name.lower().encode()).hexdigest(), 16)
    gallery_rng = random.SystemRandom()

    def pick(opts, shift: int):
        return opts[(h >> shift) % len(opts)]

    extra = frozenset(
        name for i, name in enumerate(_ALL_OPT_SECTIONS)
        if (h >> (110 + i)) & 1
    )

    palette = pick(PALETTES, 0)
    font_set = pick(FONT_SETS, 7)
    theme = _pick_theme(h, batch_name, game_names=game_names, topic=topic, tone=tone)
    animation_set = pick(ANIMATION_SETS, 19)
    header_variant = pick(HEADER_LAYOUT_VARIANTS, 25)
    footer_variant = pick(FOOTER_LAYOUT_VARIANTS, 52)
    menu_variant = pick(MENU_STYLE_VARIANTS, 68)
    card_style = pick(CARD_STYLE_OPTIONS, 90)
    game_layout = gallery_rng.choice(GAME_LAYOUT_OPTIONS)

    return VariationConfig(
        seed=h,
        palette=palette,
        font_set=font_set,
        theme=theme,
        animation_set=animation_set,
        header_variant=header_variant,
        footer_variant=footer_variant,
        menu_variant=menu_variant,
        header_logo_pos=header_variant["logo_pos"],
        header_nav_style=header_variant["nav_style"],
        header_height=header_variant["height"],
        header_bg=header_variant["bg"],
        header_font_tx=header_variant["font_tx"],
        header_letter_sp=header_variant["letter_sp"],
        header_cta=header_variant["cta"],
        header_border=header_variant["border"],
        header_scroll=header_variant["scroll"],
        footer_cols=footer_variant["cols"],
        footer_align=footer_variant["align"],
        footer_bg=footer_variant["bg"],
        footer_border_top=footer_variant["border_top"],
        footer_padding=footer_variant["padding"],
        footer_logo_pos=footer_variant["logo_pos"],
        footer_link_style=footer_variant["link_style"],
        menu_hover=menu_variant["hover"],
        menu_spacing=menu_variant["spacing"],
        gallery_card_style=pick(GALLERY_CARD_STYLES, 73),
        gallery_badge=pick(GALLERY_BADGE_STYLES, 76),
        section_padding=pick(SECTION_PADDINGS, 79),
        section_divider=pick(SECTION_DIVIDERS, 82),
        radius=pick(RADIUS_OPTIONS, 85),
        spacing=pick(SPACING_OPTIONS, 88),
        card_style=card_style,
        hero_height=pick(HERO_HEIGHTS, 92),
        hero_layout=pick(HERO_LAYOUT_OPTIONS, 95),
        game_layout=game_layout,
        feat_layout=pick(FEAT_LAYOUT_OPTIONS, 99),
        nav_style=pick(NAV_STYLE_OPTIONS, 101),
        footer_style=pick(FOOTER_STYLE_OPTIONS, 104),
        typography=pick(TYPOGRAPHY_SCALES, 106),
        gpt_temp=pick(GPT_TEMPS, 108),
        gpt_persona=pick(GPT_PERSONAS, 112),
        img_style=pick(IMG_STYLES, 114),
        img_composition=pick(IMG_COMPS, 117),
        extra_sections=extra,
        gallery_item_layout=_pick_gallery_item_layout(h, theme, card_style, rng=gallery_rng),
        gallery_section_layout=_pick_gallery_section_layout(h, theme, game_layout, rng=gallery_rng),
    )


SiteVariant = VariationConfig
pick_variant = build_variation_config
