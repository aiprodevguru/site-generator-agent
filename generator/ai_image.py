"""
AI image generation using DALL-E 3.

Generates five categories of assets:
  1. Hero image        (1792×1024 — wide, cinematic)
  2. Background image  (1024×1024 — subtle, tileable texture)
  3. Game banner ×2    (1024×1024 — one per game)
  4. Icons ×6          (1024×1024 each — displayed at 72×72 in CSS)

All images are downloaded as raw bytes and returned so the caller can
write them to disk.  Every generation call has retry logic applied.
"""
from __future__ import annotations

import re
import time
import uuid
from typing import NamedTuple

import openai
import requests

from generator.config import (
    OPENAI_API_KEY,
    BANNED_WORDS,
    OPENAI_IMAGE_MODEL,
    OPENAI_IMAGE_SIZE_HERO,
    OPENAI_IMAGE_SIZE_STD,
    OPENAI_IMAGE_QUALITY,
    MAX_RETRIES,
    RETRY_BACKOFF,
    TOPIC_KEYWORDS,
)
from generator.variation_data.icons import sample_icon_subjects
from generator.logger import get_logger
from generator.utils import contains_banned_words, retry

log = get_logger("ai_image")
_OPENAI_CLIENT: openai.OpenAI | None = None
_GENERATION_NONCE: str = uuid.uuid4().hex[:12]

# Courteous delay between icon generation calls to stay inside rate limits
_ICON_DELAY: float = 0.6

_SAFE_GAME_LABELS: dict[str, str] = {
    "fantasy": "a fantasy adventure title",
    "sci-fi": "a futuristic sci-fi title",
    "battle": "an action-focused battle title",
    "legend": "a mythic legend title",
    "sports": "a competitive sports title",
    "horror": "a moody horror title",
    "adventure": "an exploration adventure title",
    "colorful": "a bright arcade-style title",
    "rpg": "a role-playing adventure title",
    "strategy": "a strategy-focused title",
    "puzzle": "a puzzle challenge title",
    "arcade": "a retro arcade title",
    "racing": "a high-speed racing title",
}

_PROMPT_CLEANUPS: tuple[tuple[str, str], ...] = (
    (r"\blightning-powered\b", "electric"),
    (r"\bstorm[- ]armou?r\b", "streamlined racing gear"),
    (r"\briding electrical current vortexes\b", "surfing luminous energy trails"),
    (r"\bwarriors?\b", "champions"),
    (r"\bwielding\b", "equipped with"),
    (r"\bfire-breathing\b", "towering"),
    (r"\bcombat\b", "action"),
    (r"\bweapon(?:s)?\b", "equipment"),
)


def _client() -> openai.OpenAI:
    global _OPENAI_CLIENT
    if not OPENAI_API_KEY:
        raise EnvironmentError(
            "OPENAI_API_KEY is not set.  Add it to your .env file."
        )
    if _OPENAI_CLIENT is None:
        _OPENAI_CLIENT = openai.OpenAI(api_key=OPENAI_API_KEY)
    return _OPENAI_CLIENT


def reset_openai_state() -> None:
    """Drop the cached client and rotate the fresh-generation nonce."""
    global _OPENAI_CLIENT, _GENERATION_NONCE
    _OPENAI_CLIENT = None
    _GENERATION_NONCE = uuid.uuid4().hex[:12]


def _is_content_policy_violation(exc: openai.BadRequestError) -> bool:
    """Return True when the image API rejected a prompt for policy reasons."""
    body = getattr(exc, "body", None)
    if isinstance(body, dict):
        error = body.get("error")
        if isinstance(error, dict) and error.get("code") == "content_policy_violation":
            return True
    return "content_policy_violation" in str(exc).lower()


def _compact_prompt(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _sanitize_prompt_text(text: str) -> str:
    """Soften phrases that regularly trip image moderation."""
    cleaned = text
    for pattern, replacement in _PROMPT_CLEANUPS:
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
    return _compact_prompt(cleaned)


def _build_prompt_variants(prompt: str, fallback_prompts: list[str] | None = None) -> list[str]:
    candidates = [prompt, _sanitize_prompt_text(prompt)]
    for extra in fallback_prompts or []:
        candidates.append(extra)
        candidates.append(_sanitize_prompt_text(extra))

    seen: set[str] = set()
    variants: list[str] = []
    for candidate in candidates:
        normalized = _compact_prompt(candidate)
        if normalized and normalized not in seen:
            variants.append(normalized)
            seen.add(normalized)
    return variants


def _safe_game_reference(game_name: str, fallback_topic: str) -> str:
    """Avoid sending gambling-like game titles directly into image prompts."""
    violations = contains_banned_words(game_name, BANNED_WORDS)
    if not violations:
        return f"'{game_name}'"

    topic_name = _infer_game_topic(game_name, fallback_topic)
    safe_label = _SAFE_GAME_LABELS.get(topic_name, "a featured game title")
    log.info(
        f"Sanitizing image prompt title {game_name!r} due to banned terms: "
        f"{', '.join(violations)}"
    )
    return safe_label


def _build_banner_brief(game_name: str, fallback_topic: str) -> tuple[str, str]:
    """
    Return a safe title clause plus brief text for a game banner prompt.
    """
    violations = contains_banned_words(game_name, BANNED_WORDS)
    if not violations:
        return (
            f"a game called '{game_name}'",
            (
                f"Use the game name itself as the creative brief: infer the characters, "
                f"creatures, sport, vehicle, world, or action implied by '{game_name}' "
                "and make that the unmistakable focal point of the image."
            ),
        )

    topic_name = _infer_game_topic(game_name, fallback_topic)
    safe_label = _SAFE_GAME_LABELS.get(topic_name, "a featured game title")
    log.info(
        f"Using a generic banner brief for {game_name!r} due to banned terms: "
        f"{', '.join(violations)}"
    )
    return (
        "a featured title",
        (
            f"Use this creative brief instead of the raw title: {safe_label}. "
            "Center the artwork on the sport, vehicle, environment, or activity "
            "implied by the surrounding scene direction."
        ),
    )


@retry(
    max_attempts=MAX_RETRIES,
    backoff=RETRY_BACKOFF,
    exceptions=(openai.OpenAIError, requests.RequestException, AssertionError),
)
def _generate_one(prompt: str, size: str = OPENAI_IMAGE_SIZE_STD) -> bytes:
    """
    Generate a single DALL-E 3 image and return its raw bytes.

    The URL returned by the API is immediately downloaded — DALL-E URLs are
    temporary, so we never store them.
    """
    log.debug(f"DALL-E prompt ({size}): {prompt[:90]}…")
    prompt = (
        f"{prompt} Fresh creative pass token {_GENERATION_NONCE}. "
        "Create a distinct composition for this request."
    )
    response = _client().images.generate(
        model          = OPENAI_IMAGE_MODEL,
        prompt         = prompt,
        size           = size,          # type: ignore[arg-type]
        quality        = OPENAI_IMAGE_QUALITY,
        n              = 1,
        response_format= "url",
    )
    url = response.data[0].url
    assert url, "DALL-E returned an empty URL"

    dl = requests.get(url, timeout=60)
    dl.raise_for_status()
    return dl.content


# ── Prompt helpers ─────────────────────────────────────────────────────────────

_TONE_DESC: dict[str, str] = {
    "dark":     "dark, cinematic, moody blue lighting",
    "fierce":   "fierce, high-energy, dramatic red and orange lighting",
    "warm":     "warm, inviting, golden-hour amber lighting",
    "colorful": "vibrant, colourful, playful neon tones",
    "horror":   "eerie, atmospheric, dim sickly-green lighting",
    "neon":     "electric neon glow, vivid cyan and magenta highlights, cyberpunk lighting",
    "epic":     "grandiose epic scale, god-rays and volumetric light, monumental atmosphere",
}

_TOPIC_DESC: dict[str, str] = {
    "fantasy":   "high-fantasy magical realm with ancient ruins and arcane energy",
    "sci-fi":    "futuristic science-fiction environment with holographic interfaces",
    "battle":    "epic battlefield with warriors clashing amid smoke and fire",
    "legend":    "legendary ancient world with mythic monuments and divine light",
    "sports":    "dynamic sports arena packed with energy and motion blur",
    "horror":    "haunted horror setting with creeping fog and decay",
    "adventure": "lush adventurous landscape of jungles, seas, and lost temples",
    "colorful":  "vibrant candy-themed world with saturated pastels and sparkle",
    "rpg":       "dark dungeon RPG world with torchlit corridors and mystical artefacts",
    "strategy":  "grand strategy war-map with fortress cities and marching armies",
    "puzzle":    "surreal puzzle dimension with floating geometric shapes and glowing clues",
    "arcade":    "retro arcade dimension with pixel-art neon grids and 8-bit elements",
    "racing":    "high-speed racing circuit with motion blur, tarmac, and exhaust flames",
}

# Icon background colours per topic — injected into DALL-E icon prompts
_ICON_BG_DESC: dict[str, str] = {
    "fantasy":   "deep midnight purple square background",
    "sci-fi":    "dark void-black square background with faint electric blue edge glow",
    "battle":    "charcoal gunmetal dark square background",
    "legend":    "deep navy blue square background with faint gold border",
    "sports":    "near-black dark green square background",
    "horror":    "pure black square background",
    "adventure": "dark earthy brown square background",
    "colorful":  "very dark desaturated purple square background",
    "rpg":       "dark sepia-toned square background",
    "strategy":  "dark slate grey square background",
    "puzzle":    "deep teal-black square background",
    "arcade":    "jet-black CRT-dark square background",
    "racing":    "dark asphalt-grey square background",
}

_BANNER_SCENE_RULES: list[tuple[tuple[str, ...], str, str]] = [
    (("soccer", "football", "goal", "league", "cup"), "sports", "association football match scene with players contesting the ball, green stadium pitch, goal net, boots, floodlights, and crowd energy"),
    (("basketball", "hoops", "dunk", "court"), "sports", "basketball action scene with airborne player, indoor arena court markings, hoop, backboard, and dramatic crowd lighting"),
    (("tennis", "ace", "racket"), "sports", "tennis match scene with player swinging a racket, bright court surface, net, and fast-traveling ball"),
    (("golf", "fairway", "putt"), "sports", "golf scene with golfer mid-swing, manicured fairway, flagstick, and tournament atmosphere"),
    (("racing", "race", "rally", "drift", "nitro", "turbo", "lap", "prix", "speedway"), "racing", "high-speed motorsport scene with aggressive race car, tarmac track, tire smoke, motion blur, sparks, and track lights"),
    (("pirate", "treasure", "island", "voyage", "ocean", "sea"), "adventure", "pirate adventure scene with ocean spray, ship deck or hidden island, treasure map energy, cutlasses, and storm-lit skies"),
    (("dragon", "wyrm", "drake"), "fantasy", "dragon-focused fantasy scene with a massive dragon, scorched sky, claws, scales, and elemental breath"),
    (("wizard", "mage", "sorcerer", "spell", "magic"), "fantasy", "arcane fantasy scene with spellcaster, glowing runes, magical staff or hands, and supernatural energy effects"),
    (("zombie", "undead", "dead", "grave", "crypt"), "horror", "horror scene with undead figures, ruined streets or graveyard, fog, decay, and tense survival action"),
    (("ghost", "haunt", "phantom", "spirit"), "horror", "haunted supernatural scene with spectral figures, mist, ruined architecture, and eerie moonlit glow"),
    (("alien", "space", "galaxy", "star", "nova", "cosmic"), "sci-fi", "science-fiction scene with starships or space explorers, cosmic backdrop, planets, energy trails, and futuristic technology"),
    (("cyber", "neon", "robot", "mech", "quantum"), "sci-fi", "cyberpunk sci-fi scene with neon city lights, high-tech armor or machines, holograms, and electric glow"),
    (("jungle", "temple", "relic", "safari", "expedition"), "adventure", "adventure scene with dense jungle foliage, lost temple ruins, explorer gear, and discovery-focused action"),
    (("puzzle", "maze", "riddle", "cipher", "logic"), "puzzle", "surreal puzzle-world scene with glowing mechanisms, shifting geometry, maze architecture, and mystery clues"),
    (("arcade", "pixel", "retro", "8bit", "joystick"), "arcade", "retro arcade scene with pixel energy, CRT glow, arcade machines, and classic game visual motifs"),
]


def _name_tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _infer_game_topic(game_name: str, fallback_topic: str) -> str:
    counts: dict[str, int] = {}
    joined = " ".join(_name_tokens(game_name))
    for keyword, topic in TOPIC_KEYWORDS.items():
        if keyword in joined:
            counts[topic] = counts.get(topic, 0) + 1
    if counts:
        return max(counts.items(), key=lambda item: item[1])[0]
    return fallback_topic


def _banner_scene_from_name(game_name: str, fallback_topic: str) -> tuple[str, str]:
    joined = " ".join(_name_tokens(game_name))
    for keywords, topic, scene in _BANNER_SCENE_RULES:
        if any(keyword in joined for keyword in keywords):
            return topic, scene
    topic = _infer_game_topic(game_name, fallback_topic)
    return topic, _TOPIC_DESC.get(topic, "game world that matches the title's implied setting")


def _overall_color_scheme(palette: dict | None, tone: str) -> str:
    """
    Summarize the site's palette so banner prompts can match the generated UI.
    """
    if not palette or not isinstance(palette, dict):
        return (
            f"Overall site color scheme: {_TONE_DESC.get(tone, 'cinematic, dramatic lighting')}. "
            "Keep the artwork aligned with that site-wide mood."
        )

    name = str(palette.get("name", "custom palette"))
    family = str(palette.get("family", "custom")).replace("_", " ")
    img_desc = palette.get("img_desc")
    primary = palette.get("primary")
    secondary = palette.get("secondary")
    accent = palette.get("accent")
    grad_a = palette.get("grad_a")
    grad_b = palette.get("grad_b")
    bg_page = palette.get("bg_page")
    text = palette.get("text")

    parts = [f"Overall site color scheme: palette '{name}' from the {family} family"]
    if img_desc:
        parts.append(f"with {img_desc}")

    swatches: list[str] = []
    if primary:
        swatches.append(f"primary {primary}")
    if secondary:
        swatches.append(f"secondary {secondary}")
    if accent:
        swatches.append(f"accent {accent}")
    if grad_a and grad_b:
        swatches.append(f"gradient {grad_a} to {grad_b}")
    if bg_page:
        swatches.append(f"background {bg_page}")
    if text:
        swatches.append(f"highlight text {text}")

    if swatches:
        parts.append("using " + ", ".join(swatches))

    parts.append(
        "Use this palette for lighting, effects, atmospheric haze, wardrobe accents, and background details. "
        "Avoid unrelated dominant colors."
    )
    return ". ".join(parts) + "."


def _build_banner_prompt(
    *,
    game_name: str,
    game_scene: str,
    game_world_desc: str,
    color_scheme: str,
    style: str,
    char_clause: str,
) -> str:
    """
    Build a banner prompt driven by the game name plus the overall site palette.
    """
    return (
        f"Game promotional banner art for a game called '{game_name}'. "
        f"Use the game name itself as the creative brief: infer the characters, creatures, sport, vehicle, world, or action "
        f"implied by '{game_name}' and make that the unmistakable focal point of the image. "
        f"Primary scene requirement: {game_scene}. "
        f"World direction: {game_world_desc}. "
        f"{color_scheme} "
        f"If the game name implies a specific real-world sport or activity, prioritize that over generic batch-theme imagery. "
        f"{char_clause} Rendering style: {style}. "
        "Square composition, dynamic central action, polished commercial key art, rich depth, readable silhouette. "
        "No text, no logos."
    )


# ── Named return type ──────────────────────────────────────────────────────────

class GeneratedImages(NamedTuple):
    hero:        bytes
    background:  bytes
    icons:       list[bytes]   # exactly 6 items
    logo:        bytes         # square brand logo, 1024×1024


# ── Public API ─────────────────────────────────────────────────────────────────

def generate_all_images(
    game1_name:      str,
    game2_name:      str,
    topic:           str,
    tone:            str,
    brand_name:      str = "",
    img_style:       str = "",
    img_composition: str = "",
    theme:           dict | None = None,
    palette:         dict | None = None,
) -> GeneratedImages:
    """
    Sequentially generate all site images.

    Sequential (not parallel) to avoid DALL-E rate-limit errors on free and
    standard tiers.  Returns a ``GeneratedImages`` namedtuple of raw bytes.

    brand_name is woven into hero, background, and logo prompts so that the
    visual identity reflects the meaning embedded in the site's domain name.
    theme and palette dicts (from VariationConfig) enrich prompts with specific
    character/setting descriptions and color mood language.
    """
    # Fall back to legacy topic/tone lookups when no variation data provided
    if palette and isinstance(palette, dict):
        color_desc = palette["img_desc"]
    else:
        color_desc = _TONE_DESC.get(tone, "cinematic, dramatic lighting")

    if theme and isinstance(theme, dict):
        world_desc  = theme["setting_desc"]
        char_desc   = theme["char_desc"]
        icon_bg     = theme["icon_bg"]
    else:
        world_desc  = _TOPIC_DESC.get(topic, "fantasy world")
        char_desc   = ""
        icon_bg     = _ICON_BG_DESC.get(topic, "very dark square background")

    char_clause = f" {char_desc}." if char_desc else ""
    bd    = f" for a gaming platform called '{brand_name}'" if brand_name else ""
    # Variant style/composition directives — fall back to sensible defaults
    style = img_style       or "hyper-realistic digital painting, photorealistic detail"
    comp  = img_composition or "dramatic wide-angle establishing shot, horizon line at lower third"

    # 1. Hero (wide landscape)
    log.info("Generating hero image…")
    hero = _generate_one(
        f"Epic digital artwork{bd}.{char_clause} {world_desc}. "
        f"Scene featuring characters from '{game1_name}' and '{game2_name}'. "
        f"Color mood: {color_desc}. "
        f"The visual mood and setting should evoke the spirit of the name '{brand_name}'. "
        f"Rendering style: {style}. Composition: {comp}. "
        f"Ultra-detailed, professional game key art. No text, no logos, no UI elements.",
        size=OPENAI_IMAGE_SIZE_HERO,
    )

    # 2. Background (subtle texture)
    log.info("Generating background image…")
    bg = _generate_one(
        f"Seamless abstract background texture{bd}. {world_desc} aesthetic. "
        f"Color mood: {color_desc}. Rendering style: {style}. "
        f"Deep atmospheric depth, blurred bokeh, no focal characters or objects. "
        f"Suitable for a dark-themed website background. No text, no UI elements.",
    )


    # 3. Banner — game 1
    log.info(f"Generating banner for '{game1_name}'…")
    b1 = _generate_one(
        f"Game promotional banner art for a game called '{game1_name}'. "
        f"Use the game name itself as the creative brief for the subject and scene. "
        f"Interpret the meaning and spirit of the name '{game1_name}' — the characters, creatures, "
        f"setting, sport, vehicle, or action it implies — and make that the visual focus of the image. "
        f"Primary scene requirement: {game1_scene}. "
        f"World direction: {game1_world_desc}. "
        f"If the game name implies a specific real-world sport or activity, prioritize that over generic batch-theme imagery. "
        f"{char_clause} {color_scheme} Color mood: {color_desc}. Rendering style: {style}. "
        f"Square composition, central character or action scene, rich detail. "
        f"No text, no logos.",
    )

    # 4. Banner — game 2
    log.info(f"Generating banner for '{game2_name}'…")
    b2 = _generate_one(
        f"Game promotional banner art for a game called '{game2_name}'. "
        f"Use the game name itself as the creative brief for the subject and scene. "
        f"Interpret the meaning and spirit of the name '{game2_name}' — the characters, creatures, "
        f"setting, sport, vehicle, or action it implies — and make that the visual focus of the image. "
        f"Primary scene requirement: {game2_scene}. "
        f"World direction: {game2_world_desc}. "
        f"If the game name implies a specific real-world sport or activity, prioritize that over generic batch-theme imagery. "
        f"{char_clause} {color_scheme} Color mood: {color_desc}. Rendering style: {style}. "
        f"Square composition, central character or action scene, rich detail. "
        f"No text, no logos.",
    )

    # 5. Icons (6×, one per feature card)
    subjects  = sample_icon_subjects(6)
    icons: list[bytes] = []
    for subject in subjects:
        log.info(f"Generating icon: {subject}…")
        icon = _generate_one(
            f"Minimalist game-UI icon of '{subject}'. {color_desc} accent colours. "
            f"Rendering style: {style}. "
            f"{icon_bg}. Single centred object, clean sharp silhouette, "
            f"high contrast against the background, vibrant accent glow. "
            f"No text, no border, icon only.",
        )
        icons.append(icon)
        time.sleep(_ICON_DELAY)   # rate-limit courtesy

    # 6. Logo
    log.info("Generating site logo…")
    logo = _generate_one(
        f"Minimalist vector logo mark for a gaming platform called '{brand_name}'. "
        f"A single bold abstract symbol that visually captures the essence of '{brand_name}'. "
        f"{color_desc} accent colours. {world_desc} aesthetic. Rendering style: {style}. "
        f"Transparent background — no background fill, no square, no rectangle, no card, no frame. "
        f"Isolated floating symbol only, clean sharp edges, vibrant accent glow. "
        f"No text, no letters, no words, no UI chrome.",
    )

    log.info("All images generated successfully")
    return GeneratedImages(hero=hero, background=bg, icons=icons, logo=logo)


from generator.ai_image_safe import (  # noqa: E402
    GeneratedImages as GeneratedImages,
    generate_all_images as generate_all_images,
    reset_openai_state as reset_openai_state,
)
