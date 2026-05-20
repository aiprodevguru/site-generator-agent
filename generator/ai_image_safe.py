"""
AI image generation using DALL-E 3.

Generates four categories of assets:
  1. Hero image        (1792x1024, wide cinematic)
  2. Background image  (1024x1024, subtle tileable texture)
  3. Icons x6          (1024x1024 each, displayed at 72x72 in CSS)
  4. Logo              (1024x1024, transparent background preferred)

All images are downloaded as raw bytes and returned so the caller can
write them to disk. Every generation call has retry logic applied.
"""
from __future__ import annotations

import re
import time
import uuid
from typing import NamedTuple

import openai
import requests

from generator.config import (
    BANNED_WORDS,
    MAX_RETRIES,
    OPENAI_API_KEY,
    OPENAI_IMAGE_MODEL,
    OPENAI_IMAGE_QUALITY,
    OPENAI_IMAGE_SIZE_HERO,
    OPENAI_IMAGE_SIZE_STD,
    RETRY_BACKOFF,
    TOPIC_KEYWORDS,
)
from generator.logger import get_logger
from generator.utils import contains_banned_words, retry
from generator.variation_data.icons import sample_icon_subjects

log = get_logger("ai_image")
_OPENAI_CLIENT: openai.OpenAI | None = None
_GENERATION_NONCE: str = uuid.uuid4().hex[:12]

_ICON_DELAY: float = 0.6
_SAFETY_RETRY_LIMIT: int = 3

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

_IMAGE_TITLE_RISK_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\bscratch\b", "scratch"),
    (r"\bspin\b", "spin"),
    (r"\bslot\b", "slot"),
    (r"\broulette\b", "roulette"),
    (r"\bpoker\b", "poker"),
    (r"\bjackpot\b", "jackpot"),
    (r"\bprize\b", "prize"),
    (r"\bfortune\b", "fortune"),
    (r"\bluck\b", "luck"),
    (r"\bwin\b", "win"),
)

_TONE_DESC: dict[str, str] = {
    "dark": "dark, cinematic, moody blue lighting",
    "fierce": "fierce, high-energy, dramatic red and orange lighting",
    "warm": "warm, inviting, golden-hour amber lighting",
    "colorful": "vibrant, colourful, playful neon tones",
    "horror": "eerie, atmospheric, dim sickly-green lighting",
    "neon": "electric neon glow, vivid cyan and magenta highlights, cyberpunk lighting",
    "epic": "grandiose epic scale, god-rays and volumetric light, monumental atmosphere",
}

_TOPIC_DESC: dict[str, str] = {
    "fantasy": "high-fantasy magical realm with ancient ruins and arcane energy",
    "sci-fi": "futuristic science-fiction environment with holographic interfaces",
    "battle": "epic battlefield with champions amid smoke and fire",
    "legend": "legendary ancient world with mythic monuments and divine light",
    "sports": "dynamic sports arena packed with energy and motion blur",
    "horror": "haunted horror setting with creeping fog and decay",
    "adventure": "lush adventurous landscape of jungles, seas, and lost temples",
    "colorful": "vibrant candy-themed world with saturated pastels and sparkle",
    "rpg": "dark dungeon RPG world with torchlit corridors and mystical artefacts",
    "strategy": "grand strategy war-map with fortress cities and marching armies",
    "puzzle": "surreal puzzle dimension with floating geometric shapes and glowing clues",
    "arcade": "retro arcade dimension with pixel-art neon grids and 8-bit elements",
    "racing": "high-speed racing circuit with motion blur, tarmac, and exhaust flames",
}

_ICON_BG_DESC: dict[str, str] = {
    "fantasy": "deep midnight purple square background",
    "sci-fi": "dark void-black square background with faint electric blue edge glow",
    "battle": "charcoal gunmetal dark square background",
    "legend": "deep navy blue square background with faint gold border",
    "sports": "near-black dark green square background",
    "horror": "pure black square background",
    "adventure": "dark earthy brown square background",
    "colorful": "very dark desaturated purple square background",
    "rpg": "dark sepia-toned square background",
    "strategy": "dark slate grey square background",
    "puzzle": "deep teal-black square background",
    "arcade": "jet-black CRT-dark square background",
    "racing": "dark asphalt-grey square background",
}

_BANNER_SCENE_RULES: list[tuple[tuple[str, ...], str, str]] = [
    (
        ("soccer", "football", "goal", "league", "cup"),
        "sports",
        "association football match scene with players contesting the ball, green stadium pitch, goal net, boots, floodlights, and crowd energy",
    ),
    (
        ("basketball", "hoops", "dunk", "court"),
        "sports",
        "basketball action scene with airborne player, indoor arena court markings, hoop, backboard, and dramatic crowd lighting",
    ),
    (
        ("tennis", "ace", "racket"),
        "sports",
        "tennis match scene with player swinging a racket, bright court surface, net, and fast-traveling ball",
    ),
    (
        ("golf", "fairway", "putt"),
        "sports",
        "golf scene with golfer mid-swing, manicured fairway, flagstick, and tournament atmosphere",
    ),
    (
        ("racing", "race", "rally", "drift", "nitro", "turbo", "lap", "prix", "speedway"),
        "racing",
        "high-speed motorsport scene with aggressive race car, tarmac track, tire smoke, motion blur, sparks, and track lights",
    ),
    (
        ("pirate", "treasure", "island", "voyage", "ocean", "sea"),
        "adventure",
        "pirate adventure scene with ocean spray, ship deck or hidden island, treasure map energy, cutlasses, and storm-lit skies",
    ),
    (
        ("dragon", "wyrm", "drake"),
        "fantasy",
        "dragon-focused fantasy scene with a massive dragon, scorched sky, claws, scales, and elemental breath",
    ),
    (
        ("wizard", "mage", "sorcerer", "spell", "magic"),
        "fantasy",
        "arcane fantasy scene with spellcaster, glowing runes, magical staff or hands, and supernatural energy effects",
    ),
    (
        ("zombie", "undead", "dead", "grave", "crypt"),
        "horror",
        "horror scene with undead figures, ruined streets or graveyard, fog, decay, and tense survival action",
    ),
    (
        ("ghost", "haunt", "phantom", "spirit"),
        "horror",
        "haunted supernatural scene with spectral figures, mist, ruined architecture, and eerie moonlit glow",
    ),
    (
        ("alien", "space", "galaxy", "star", "nova", "cosmic"),
        "sci-fi",
        "science-fiction scene with starships or space explorers, cosmic backdrop, planets, energy trails, and futuristic technology",
    ),
    (
        ("cyber", "neon", "robot", "mech", "quantum"),
        "sci-fi",
        "cyberpunk sci-fi scene with neon city lights, high-tech armor or machines, holograms, and electric glow",
    ),
    (
        ("jungle", "temple", "relic", "safari", "expedition"),
        "adventure",
        "adventure scene with dense jungle foliage, lost temple ruins, explorer gear, and discovery-focused action",
    ),
    (
        ("puzzle", "maze", "riddle", "cipher", "logic"),
        "puzzle",
        "surreal puzzle-world scene with glowing mechanisms, shifting geometry, maze architecture, and mystery clues",
    ),
    (
        ("arcade", "pixel", "retro", "8bit", "joystick"),
        "arcade",
        "retro arcade scene with pixel energy, CRT glow, arcade machines, and classic game visual motifs",
    ),
]


def _client() -> openai.OpenAI:
    global _OPENAI_CLIENT
    if not OPENAI_API_KEY:
        raise EnvironmentError("OPENAI_API_KEY is not set. Add it to your .env file.")
    if _OPENAI_CLIENT is None:
        _OPENAI_CLIENT = openai.OpenAI(api_key=OPENAI_API_KEY)
    return _OPENAI_CLIENT


def reset_openai_state() -> None:
    """Drop the cached client and rotate the fresh-generation nonce."""
    global _OPENAI_CLIENT, _GENERATION_NONCE
    _OPENAI_CLIENT = None
    _GENERATION_NONCE = uuid.uuid4().hex[:12]


def _is_content_policy_violation(exc: openai.BadRequestError) -> bool:
    body = getattr(exc, "body", None)
    if isinstance(body, dict):
        error = body.get("error")
        if isinstance(error, dict) and error.get("code") == "content_policy_violation":
            return True
    return "content_policy_violation" in str(exc).lower()


def _compact_prompt(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _sanitize_prompt_text(text: str) -> str:
    cleaned = text
    for pattern, replacement in _PROMPT_CLEANUPS:
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
    return _compact_prompt(cleaned)


def _derive_safer_variants(prompt: str) -> list[str]:
    """
    Build progressively simpler prompt rewrites for safety retries.
    """
    sanitized = _sanitize_prompt_text(prompt)
    generic = sanitized
    generic = re.sub(r"'[^']+'", "the featured brand", generic)
    generic = re.sub(
        r"\b(characters|creatures|fighters|champions|agents|heroes|captains)\b",
        "figures",
        generic,
        flags=re.IGNORECASE,
    )
    generic = re.sub(
        r"\bweapons?|blades?|guns?|pistols?|swords?|tridents?|armou?r\b",
        "gear",
        generic,
        flags=re.IGNORECASE,
    )
    minimal = (
        "Premium entertainment platform artwork. "
        "Atmospheric environment, polished commercial style, rich lighting, "
        "dynamic composition. No text, no logos, no UI elements."
    )
    return [sanitized, _compact_prompt(generic), minimal]


def _image_title_violations(game_name: str) -> list[str]:
    violations = list(contains_banned_words(game_name, BANNED_WORDS))
    lowered = game_name.lower()
    for pattern, label in _IMAGE_TITLE_RISK_PATTERNS:
        if re.search(pattern, lowered, flags=re.IGNORECASE) and label not in violations:
            violations.append(label)
    return violations


def _build_prompt_variants(
    prompt: str,
    fallback_prompts: list[str] | None = None,
) -> list[str]:
    candidates = [prompt]
    candidates.extend(_derive_safer_variants(prompt))
    for extra in fallback_prompts or []:
        candidates.append(extra)
        candidates.extend(_derive_safer_variants(extra))

    seen: set[str] = set()
    variants: list[str] = []
    for candidate in candidates:
        normalized = _compact_prompt(candidate)
        if normalized and normalized not in seen:
            variants.append(normalized)
            seen.add(normalized)
    return variants


def _log_prompt_transition(original_prompt: str, modified_prompt: str, *, attempt: int) -> None:
    """Log the original prompt and the exact prompt variant being attempted."""
    log.debug(
        f"Image prompt attempt {attempt}/{_SAFETY_RETRY_LIMIT} original: {original_prompt}"
    )
    log.debug(
        f"Image prompt attempt {attempt}/{_SAFETY_RETRY_LIMIT} modified: {modified_prompt}"
    )


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


def _safe_game_reference(game_name: str, fallback_topic: str) -> str:
    violations = _image_title_violations(game_name)
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
    violations = _image_title_violations(game_name)
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
def _generate_one(
    prompt: str,
    size: str = OPENAI_IMAGE_SIZE_STD,
    fallback_prompts: list[str] | None = None,
) -> bytes:
    prompt_variants = _build_prompt_variants(prompt, fallback_prompts)
    last_policy_error: openai.BadRequestError | None = None
    prompt_variants = prompt_variants[:_SAFETY_RETRY_LIMIT]

    for index, candidate in enumerate(prompt_variants, start=1):
        _log_prompt_transition(prompt, candidate, attempt=index)
        log.debug(
            f"DALL-E prompt ({size}, variant {index}/{len(prompt_variants)}): "
            f"{candidate[:90]}..."
        )
        candidate = (
            f"{candidate} Fresh creative pass token {_GENERATION_NONCE}. "
            "Create a distinct composition for this request."
        )
        try:
            response = _client().images.generate(
                model=OPENAI_IMAGE_MODEL,
                prompt=candidate,
                size=size,  # type: ignore[arg-type]
                quality=OPENAI_IMAGE_QUALITY,
                n=1,
                response_format="url",
            )
            url = response.data[0].url
            assert url, "DALL-E returned an empty URL"

            dl = requests.get(url, timeout=60)
            dl.raise_for_status()
            return dl.content
        except openai.BadRequestError as exc:
            if not _is_content_policy_violation(exc):
                raise
            last_policy_error = exc
            if index < len(prompt_variants):
                log.warning(
                    f"Image prompt attempt {index}/{len(prompt_variants)} hit "
                    "content_policy_violation; retrying with a safer variant."
                )
                continue

    if last_policy_error is not None:
        log.error(
            f"Image generation failed after {len(prompt_variants)} safety attempts. "
            f"Original prompt: {prompt}"
        )
        raise RuntimeError(
            f"Image generation blocked by safety system after {len(prompt_variants)} failures"
        ) from last_policy_error
    raise RuntimeError("Image generation failed before producing a usable image")


def _overall_color_scheme(palette: dict | None, tone: str) -> str:
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
    title_clause: str,
    creative_brief: str,
    game_scene: str,
    game_world_desc: str,
    color_scheme: str,
    style: str,
    char_clause: str,
) -> str:
    return (
        f"Game promotional banner art for {title_clause}. "
        f"{creative_brief} "
        f"Primary scene requirement: {game_scene}. "
        f"World direction: {game_world_desc}. "
        f"{color_scheme} "
        "If the game concept implies a specific real-world sport or activity, prioritize that over generic batch-theme imagery. "
        f"{char_clause} Rendering style: {style}. "
        "Square composition, dynamic central action, polished commercial key art, rich depth, readable silhouette. "
        "No text, no logos."
    )


class GeneratedImages(NamedTuple):
    hero: bytes
    background: bytes
    icons: list[bytes]
    logo: bytes


def generate_all_images(
    game1_name: str,
    game2_name: str,
    topic: str,
    tone: str,
    brand_name: str = "",
    img_style: str = "",
    img_composition: str = "",
    theme: dict | None = None,
    palette: dict | None = None,
) -> GeneratedImages:
    if palette and isinstance(palette, dict):
        color_desc = palette["img_desc"]
    else:
        color_desc = _TONE_DESC.get(tone, "cinematic, dramatic lighting")

    if theme and isinstance(theme, dict):
        world_desc = theme["setting_desc"]
        char_desc = theme["char_desc"]
        icon_bg = theme["icon_bg"]
    else:
        world_desc = _TOPIC_DESC.get(topic, "fantasy world")
        char_desc = ""
        icon_bg = _ICON_BG_DESC.get(topic, "very dark square background")

    char_clause = f" {char_desc}." if char_desc else ""
    brand_clause = f" for a gaming platform called '{brand_name}'" if brand_name else ""
    safe_game1_ref = _safe_game_reference(game1_name, topic)
    safe_game2_ref = _safe_game_reference(game2_name, topic)

    style = img_style or "hyper-realistic digital painting, photorealistic detail"
    comp = img_composition or "dramatic wide-angle establishing shot, horizon line at lower third"

    log.info("Generating hero image...")
    hero = _generate_one(
        (
            f"Epic digital artwork{brand_clause}.{char_clause} {world_desc}. "
            f"Scene featuring worlds inspired by {safe_game1_ref} and {safe_game2_ref}. "
            f"Color mood: {color_desc}. "
            f"The visual mood and setting should evoke the spirit of the name '{brand_name}'. "
            f"Rendering style: {style}. Composition: {comp}. "
            "Ultra-detailed, professional game key art. No text, no logos, no UI elements."
        ),
        size=OPENAI_IMAGE_SIZE_HERO,
        fallback_prompts=[
            (
                f"Cinematic entertainment-platform hero artwork{brand_clause}. "
                f"{world_desc}. Color mood: {color_desc}. "
                "Blend two complementary game worlds into one dramatic environment. "
                f"Rendering style: {style}. Composition: {comp}. "
                "No text, no logos, no UI elements."
            ),
            (
                f"Atmospheric wide digital artwork{brand_clause}. "
                "Storm-lit premium game-world environment with layered haze and energy. "
                f"Color mood: {color_desc}. Rendering style: {style}. Composition: {comp}. "
                "No text, no logos, no UI elements."
            ),
        ],
    )

    log.info("Generating background image...")
    background = _generate_one(
        (
            f"Seamless abstract background texture{brand_clause}. {world_desc} aesthetic. "
            f"Color mood: {color_desc}. Rendering style: {style}. "
            "Deep atmospheric depth, blurred bokeh, no focal characters or objects. "
            "Suitable for a dark-themed website background. No text, no UI elements."
        ),
        fallback_prompts=[
            (
                f"Seamless abstract background texture{brand_clause}. "
                "Electric storm atmosphere with layered haze and soft light streaks. "
                f"Color mood: {color_desc}. Rendering style: {style}. "
                "No focal characters, no text, no UI elements."
            ),
        ],
    )

    subjects = sample_icon_subjects(6)
    icons: list[bytes] = []
    for subject in subjects:
        log.info(f"Generating icon: {subject}...")
        icon = _generate_one(
            (
                f"Minimalist game-UI icon of '{subject}'. {color_desc} accent colours. "
                f"Rendering style: {style}. "
                f"{icon_bg}. Single centered object, clean sharp silhouette, "
                "high contrast against the background, vibrant accent glow. "
                "No text, no border, icon only."
            ),
            fallback_prompts=[
                (
                    f"Minimalist entertainment-platform icon of '{subject}'. "
                    f"{color_desc} accent colours. Rendering style: {style}. "
                    f"{icon_bg}. Single centered object, clean silhouette, no text."
                ),
            ],
        )
        icons.append(icon)
        time.sleep(_ICON_DELAY)

    log.info("Generating site logo...")
    logo = _generate_one(
        (
            f"Minimalist vector logo mark for a gaming platform called '{brand_name}'. "
            f"A single bold abstract symbol that visually captures the essence of '{brand_name}'. "
            f"{color_desc} accent colours. {world_desc} aesthetic. Rendering style: {style}. "
            "Transparent background, no background fill, no square, no rectangle, no card, no frame. "
            "Isolated floating symbol only, clean sharp edges, vibrant accent glow. "
            "No text, no letters, no words, no UI chrome."
        ),
        fallback_prompts=[
            (
                f"Minimalist abstract logo symbol for an entertainment platform called '{brand_name}'. "
                f"{color_desc} accent colours. Rendering style: {style}. "
                "Transparent background, isolated floating symbol, no text, no letters."
            ),
        ],
    )

    log.info("All images generated successfully")
    return GeneratedImages(
        hero=hero,
        background=background,
        icons=icons,
        logo=logo,
    )
