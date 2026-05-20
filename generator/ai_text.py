"""
AI-powered site copy generator.

Uses a single structured JSON prompt to generate all page content in one API
call, minimising latency and cost.  Output is automatically screened for
banned words; violations trigger a targeted rewrite pass.
"""
from __future__ import annotations

import json
import uuid
from typing import Any

import openai

from generator.config import (
    OPENAI_API_KEY,
    OPENAI_TEXT_MODEL,
    BANNED_WORDS,
    MAX_RETRIES,
    RETRY_BACKOFF,
)
from generator.logger import get_logger
from generator.utils import contains_banned_words, retry

log = get_logger("ai_text")
_OPENAI_CLIENT: openai.OpenAI | None = None
_GENERATION_NONCE: str = uuid.uuid4().hex[:12]
_COMPLIANCE_REWRITE_ATTEMPTS = 3


# ── Client factory ─────────────────────────────────────────────────────────────

def _client() -> openai.OpenAI:
    global _OPENAI_CLIENT
    if not OPENAI_API_KEY:
        raise EnvironmentError(
            "OPENAI_API_KEY is not set.  Add it to your .env file "
            "(see .env.example for reference)."
        )
    if _OPENAI_CLIENT is None:
        _OPENAI_CLIENT = openai.OpenAI(api_key=OPENAI_API_KEY)
    return _OPENAI_CLIENT


def reset_openai_state() -> None:
    """Drop the cached client and rotate the fresh-generation nonce."""
    global _OPENAI_CLIENT, _GENERATION_NONCE
    _OPENAI_CLIENT = None
    _GENERATION_NONCE = uuid.uuid4().hex[:12]


# ── JSON schema description sent in the prompt ─────────────────────────────────

_SCHEMA = """
Return a single valid JSON object — no markdown fences, no prose, just JSON.
Required keys and their types:

{
  "brand_name":            "string — short catchy site name (2-4 words)",
  "meta_description":      "string — SEO meta description, max 155 chars",
  "hero_badge":            "string — badge label, ALL CAPS, 3-5 words",
  "hero_headline_part1":   "string — first part of the hero headline (3-5 words)",
  "hero_headline_part2":   "string — accented words shown in colour (2-3 words)",
  "hero_subtext":          "string — 1-2 compelling sentences, entertainment focus",

  "gallery_title":         "string — game gallery section heading",
  "gallery_description":   "string — 1 sentence introducing the collection",

  "game1_description":     "string — 2-sentence description for game 1",
  "game2_description":     "string — 2-sentence description for game 2",

  "why_title":             "string — Why Choose Us heading",
  "why_description":       "string — 1 sentence subheading",
  "feature_cards": [
    {
      "icon_label":  "string — icon concept (sword / shield / star / etc.)",
      "title":       "string — feature card title",
      "description": "string — 1-2 sentences"
    }
    ... (exactly 3, 4, or 6 cards)
  ],

  "contact_intro": "string — 1 sentence intro for the contact page",

  "terms_sections": [
    { "heading": "Age Requirement",          "body": "string" },
    { "heading": "Entertainment Only",       "body": "string" },
    { "heading": "Permitted Use",            "body": "string" },
    { "heading": "Intellectual Property",    "body": "string" },
    { "heading": "Limitation of Liability",  "body": "string" },
    { "heading": "Policy Updates",           "body": "string" }
  ],

  "privacy_sections": [
    { "heading": "Information We Collect",   "body": "string" },
    { "heading": "How We Use Information",   "body": "string" },
    { "heading": "Data Sharing",             "body": "string" },
    { "heading": "Cookies",                  "body": "string" },
    { "heading": "Your Rights",              "body": "string" },
    { "heading": "Contact Us",               "body": "string" }
  ],

  "cookie_intro":              "string — 1 paragraph explaining essential-only cookies",
  "footer_brand_description":  "string — 2 sentences about the site, mention both game names",
  "footer_legal_notice":       "string — 2 sentences: 18+, entertainment only, no real rewards",

  "stats": {
    "title": "string — short heading above the stats row (e.g. 'By The Numbers')",
    "items": [
      {"number": "string — e.g. '1M+', '24/7', '100+', '4.9★'", "label": "string — e.g. 'Active Players'"},
      {"number": "...", "label": "..."},
      {"number": "...", "label": "..."},
      {"number": "...", "label": "..."}
    ]
  },

  "testimonials": {
    "title": "string — section heading (e.g. 'What Players Are Saying')",
    "items": [
      {"quote": "string — 1-2 sentence enthusiastic player quote", "author": "string — first name + initial, e.g. 'Jordan K.'"},
      {"quote": "...", "author": "..."},
      {"quote": "...", "author": "..."}
    ]
  },

  "about": {
    "title": "string — section heading (e.g. 'About {brand_name}')",
    "body":  "string — 2-3 sentences about the platform's mission and entertainment focus"
  },

  "cta_banner": {
    "headline":    "string — short punchy call-to-action headline, 5-8 words",
    "subtext":     "string — 1 supporting sentence",
    "button_text": "string — 3-5 words for the CTA button, e.g. 'Play Free Now'"
  }
}
""".strip()

_SYSTEM = (
    "You are a creative copywriter specialising in entertainment-only interactive platforms. "
    "Your writing is natural, engaging, and legally compliant — never robotic or generic. "
    "You NEVER use gambling terminology under any circumstances. "
    "Respond with valid JSON only. No explanations, no markdown."
)


# ── Main generation function ───────────────────────────────────────────────────

_PERSONA_DESC: dict[str, str] = {
    "authoritative": (
        "Write with authority and expertise — confident, precise, informative. "
        "Use strong declarative statements. Sound like a trusted industry voice."
    ),
    "energetic": (
        "Write with high energy and enthusiasm — punchy sentences, exclamation where natural, "
        "action verbs. Sound like an excited community host."
    ),
    "mystical": (
        "Write with a sense of mystery and wonder — evocative language, metaphor, a hint of the "
        "arcane. Sound like a storyteller drawing players into another world."
    ),
    "welcoming": (
        "Write with warmth and approachability — inclusive, friendly, encouraging. "
        "Sound like a knowledgeable friend recommending something they love."
    ),
}


@retry(
    max_attempts=MAX_RETRIES,
    backoff=RETRY_BACKOFF,
    exceptions=(openai.OpenAIError, json.JSONDecodeError, KeyError, ValueError),
)
def generate_site_content(
    game1_name:  str,
    game2_name:  str,
    topic:       str,
    tone:        str,
    brand_hint:  str,
    temperature: float = 0.75,
    persona:     str   = "authoritative",
    theme:       dict | None = None,
    palette:     dict | None = None,
) -> dict[str, Any]:
    """
    Generate all site copy as a structured JSON dict.

    The output is screened for banned words.  If any are found, a targeted
    rewrite message is appended to the conversation and the model produces
    a cleaned version.

    Parameters
    ----------
    game1_name  : display name of the first game
    game2_name  : display name of the second game
    topic       : content theme (fantasy, sci-fi, …)
    tone        : visual/copy tone (dark, fierce, warm, …)
    brand_hint  : suggested brand name; the model may refine it

    Returns
    -------
    dict[str, Any]
        Parsed JSON content ready to be threaded into the site templates.
    """
    client = _client()
    persona_instruction = _PERSONA_DESC.get(persona, _PERSONA_DESC["authoritative"])

    # Build optional theme/palette/layout context lines
    if theme and isinstance(theme, dict):
        theme_context = (
            f"Visual universe: {theme['name']} — {theme['char_desc']}. "
            f"Setting: {theme['setting_desc']}."
        )
    else:
        theme_context = f"Visual universe: {topic} / {tone}"

    if palette and isinstance(palette, dict):
        palette_context = (
            f"Palette direction: {palette['name']} ({palette['family']}) with "
            f"{palette['img_desc']}."
        )
    else:
        palette_context = f"Palette direction: {tone} mood with {topic} cues."

    design_context = (
        "Design cues: make the copy feel authored for a distinctive brand world, "
        "not a reusable template. Vary the rhythm of headings, avoid generic gaming "
        "phrases, and let the visual direction influence word choice."
    )

    user_prompt = f"""
Create website copy for an entertainment gaming platform.

Writing voice : {persona_instruction}

Brand / domain : "{brand_hint}"
  The brand name is derived directly from the site's domain name.
  Interpret the words and meaning in "{brand_hint}" to shape the platform's
  identity, tone, and narrative — not just as a label but as a concept.
  For example, "Lunar Game Summit" suggests a celestial/space setting and a
  prestigious gathering of gamers; let that meaning bleed into headlines,
  descriptions, and the overall voice.  You may adjust capitalisation or
  spacing to make it read naturally, but keep all the core words intact.

Featured games : "{game1_name}" and "{game2_name}"
Content theme  : {topic}
Visual tone    : {tone}
Fresh generation token: {_GENERATION_NONCE}
{theme_context}
{palette_context}
{design_context}

ABSOLUTE RULES — violating these is unacceptable:
• NEVER use: casino, bet, betting, spin, spinning, gambling, gamble, bonus,
  real money, jackpot, wager, wagering, stake, slot machine, roulette,
  poker, blackjack, baccarat, payout, winnings, cashout, deposit funds.
• All copy MUST convey: entertainment only, free to play, no real-world
  rewards, and that players must be 18+.
• Write natural, fluent English — no filler phrases, no corporate clichés.
• Avoid generic headings like "Ultimate Gaming Experience", "Why Choose Us",
  "Top Features", or "Join the Action" unless the meaning is genuinely fresh.

• The "feature_cards" array MUST contain exactly 3, 4, or 6 cards.
  Choose the count that best fits the brand and avoid filler items.

Treat this as a completely fresh generation and do not intentionally reuse
wording from earlier batches.

{_SCHEMA}
""".strip()

    log.info(f"Generating copy for '{brand_hint}' — {topic} / {tone} / {persona} @ {temperature}…")

    messages: list[dict[str, str]] = [
        {"role": "system", "content": _SYSTEM},
        {"role": "user",   "content": user_prompt},
    ]

    response = client.chat.completions.create(
        model=OPENAI_TEXT_MODEL,
        messages=messages,
        temperature=temperature,
        response_format={"type": "json_object"},
    )
    raw     = response.choices[0].message.content
    content: dict[str, Any] = json.loads(raw)

    # ── Compliance scan ────────────────────────────────────────────────────────
    flat_text  = json.dumps(content).lower()
    violations = contains_banned_words(flat_text, BANNED_WORDS)

    if violations:
        log.warning(f"Banned words detected — requesting rewrite: {violations}")

        messages.append({"role": "assistant", "content": raw})
        messages.append({
            "role": "user",
            "content": (
                f"The previous response contains prohibited words: {violations}. "
                "Rewrite the entire JSON, replacing every violation with a "
                "compliant, natural-sounding alternative. "
                "Return clean JSON only — no markdown, no explanation."
            ),
        })

        fix_response = client.chat.completions.create(
            model=OPENAI_TEXT_MODEL,
            messages=messages,
            temperature=0.4,
            response_format={"type": "json_object"},
        )
        content   = json.loads(fix_response.choices[0].message.content)
        remaining = contains_banned_words(json.dumps(content).lower(), BANNED_WORDS)
        if remaining:
            log.error(f"Banned words still present after rewrite: {remaining}")

    _validate_content_keys(content)
    log.info("Site copy generated successfully")
    return content


def _validate_content_keys(content: dict[str, Any]) -> None:
    """Raise ValueError if any top-level required key is missing."""
    required = {
        "brand_name", "meta_description", "hero_badge",
        "hero_headline_part1", "hero_headline_part2", "hero_subtext",
        "gallery_title", "gallery_description",
        "game1_description", "game2_description",
        "why_title", "why_description", "feature_cards",
        "contact_intro", "terms_sections", "privacy_sections",
        "cookie_intro", "footer_brand_description", "footer_legal_notice",
    }
    missing = required - set(content.keys())
    if missing:
        raise ValueError(f"AI response missing required keys: {missing}")

    feature_count = len(content.get("feature_cards", []))
    if feature_count not in {3, 4, 6}:
        raise ValueError("AI response must contain exactly 3, 4, or 6 feature_cards")
    if len(content.get("terms_sections", [])) < 4:
        raise ValueError("AI response must contain at least 4 terms_sections")


# Cost-optimized override layer: prefer a cheaper primary text model, keep a
# stronger fallback, and move structure enforcement into JSON schema mode.
from generator import config as _cfg

_SYSTEM = (
    "You write distinctive, natural copy for entertainment-only gaming sites. "
    "Keep it vivid, brand-shaped, and compliant. Never use gambling language. "
    "Return data only."
)

_PERSONA_DESC = {
    "authoritative": "confident, precise, polished, trustworthy",
    "energetic": "high-energy, punchy, lively, community-driven",
    "mystical": "evocative, mysterious, imaginative, story-rich",
    "welcoming": "warm, friendly, inclusive, approachable",
}

_GENERIC_HEADINGS = {
    "ultimate gaming experience",
    "why choose us",
    "top features",
    "join the action",
}


def _string_schema(*, max_length: int | None = None) -> dict[str, Any]:
    schema: dict[str, Any] = {"type": "string"}
    if max_length is not None:
        schema["maxLength"] = max_length
    return schema


def _object_schema(
    properties: dict[str, Any],
    *,
    required: list[str],
    additional_properties: bool = False,
) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": additional_properties,
    }


_SECTION_SCHEMA = _object_schema(
    {
        "heading": _string_schema(),
        "body": _string_schema(),
    },
    required=["heading", "body"],
)

_FEATURE_CARD_SCHEMA = _object_schema(
    {
        "icon_label": _string_schema(),
        "title": _string_schema(),
        "description": _string_schema(),
    },
    required=["icon_label", "title", "description"],
)

_STAT_ITEM_SCHEMA = _object_schema(
    {
        "number": _string_schema(),
        "label": _string_schema(),
    },
    required=["number", "label"],
)

_TESTIMONIAL_SCHEMA = _object_schema(
    {
        "quote": _string_schema(),
        "author": _string_schema(),
    },
    required=["quote", "author"],
)

_SITE_CONTENT_SCHEMA = _object_schema(
    {
        "brand_name": _string_schema(),
        "meta_description": _string_schema(max_length=155),
        "hero_badge": _string_schema(),
        "hero_headline_part1": _string_schema(),
        "hero_headline_part2": _string_schema(),
        "hero_subtext": _string_schema(),
        "gallery_title": _string_schema(),
        "gallery_description": _string_schema(),
        "game1_description": _string_schema(),
        "game2_description": _string_schema(),
        "why_title": _string_schema(),
        "why_description": _string_schema(),
        "feature_cards": {
            "type": "array",
            "items": _FEATURE_CARD_SCHEMA,
            "minItems": 3,
            "maxItems": 6,
        },
        "contact_intro": _string_schema(),
        "terms_sections": {
            "type": "array",
            "items": _SECTION_SCHEMA,
            "minItems": 6,
        },
        "privacy_sections": {
            "type": "array",
            "items": _SECTION_SCHEMA,
            "minItems": 6,
        },
        "cookie_intro": _string_schema(),
        "footer_brand_description": _string_schema(),
        "footer_legal_notice": _string_schema(),
        "stats": _object_schema(
            {
                "title": _string_schema(),
                "items": {
                    "type": "array",
                    "items": _STAT_ITEM_SCHEMA,
                    "minItems": 4,
                    "maxItems": 4,
                },
            },
            required=["title", "items"],
        ),
        "testimonials": _object_schema(
            {
                "title": _string_schema(),
                "items": {
                    "type": "array",
                    "items": _TESTIMONIAL_SCHEMA,
                    "minItems": 3,
                    "maxItems": 3,
                },
            },
            required=["title", "items"],
        ),
        "about": _object_schema(
            {
                "title": _string_schema(),
                "body": _string_schema(),
            },
            required=["title", "body"],
        ),
        "cta_banner": _object_schema(
            {
                "headline": _string_schema(),
                "subtext": _string_schema(),
                "button_text": _string_schema(),
            },
            required=["headline", "subtext", "button_text"],
        ),
    },
    required=[
        "brand_name",
        "meta_description",
        "hero_badge",
        "hero_headline_part1",
        "hero_headline_part2",
        "hero_subtext",
        "gallery_title",
        "gallery_description",
        "game1_description",
        "game2_description",
        "why_title",
        "why_description",
        "feature_cards",
        "contact_intro",
        "terms_sections",
        "privacy_sections",
        "cookie_intro",
        "footer_brand_description",
        "footer_legal_notice",
        "stats",
        "testimonials",
        "about",
        "cta_banner",
    ],
)

_LEGACY_OUTPUT_GUIDE = (
    "Required keys: brand_name, meta_description, hero_badge, hero_headline_part1, "
    "hero_headline_part2, hero_subtext, gallery_title, gallery_description, "
    "game1_description, game2_description, why_title, why_description, feature_cards, "
    "contact_intro, terms_sections, privacy_sections, cookie_intro, "
    "footer_brand_description, footer_legal_notice, stats, testimonials, about, "
    "cta_banner. Return one valid JSON object only."
)


def _response_format() -> dict[str, Any]:
    if _cfg.OPENAI_TEXT_USE_JSON_SCHEMA:
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "site_content",
                "strict": True,
                "schema": _SITE_CONTENT_SCHEMA,
            },
        }
    return {"type": "json_object"}


def _model_candidates() -> list[str]:
    models = [_cfg.OPENAI_TEXT_MODEL_PRIMARY.strip()]
    fallback = _cfg.OPENAI_TEXT_MODEL_FALLBACK.strip()
    if _cfg.OPENAI_TEXT_ENABLE_FALLBACK and fallback and fallback not in models:
        models.append(fallback)
    return [model for model in models if model]


def _build_messages(
    *,
    game1_name: str,
    game2_name: str,
    topic: str,
    tone: str,
    brand_hint: str,
    persona: str,
    theme: dict[str, Any] | None,
    palette: dict[str, Any] | None,
) -> list[dict[str, str]]:
    persona_instruction = _PERSONA_DESC.get(persona, _PERSONA_DESC["authoritative"])

    if theme and isinstance(theme, dict):
        theme_context = (
            f"Theme world: {theme.get('name', topic)}. "
            f"Characters: {theme.get('char_desc', topic)}. "
            f"Setting: {theme.get('setting_desc', tone)}."
        )
    else:
        theme_context = f"Theme world: {topic}. Tone: {tone}."

    if palette and isinstance(palette, dict):
        palette_context = (
            f"Palette: {palette.get('name', tone)} / {palette.get('family', tone)}. "
            f"Visual color cues: {palette.get('img_desc', tone)}."
        )
    else:
        palette_context = f"Palette: {tone} mood with {topic} cues."

    user_prompt = (
        "Create original website copy for a free-to-play entertainment gaming platform.\n"
        f"Brand hint: \"{brand_hint}\". Keep the same core words, but improve spacing or casing if needed.\n"
        f"Featured games: \"{game1_name}\" and \"{game2_name}\".\n"
        f"Voice: {persona_instruction}.\n"
        f"Topic: {topic}. Tone: {tone}.\n"
        f"Fresh generation token: {_GENERATION_NONCE}.\n"
        f"{theme_context}\n"
        f"{palette_context}\n"
        "Make the copy feel authored for this brand world, not like a reusable template.\n"
        "Rules:\n"
        f"- Never use these terms: {', '.join(BANNED_WORDS)}.\n"
        "- Keep the site clearly entertainment-only, free to play, 18+, and with no real-world rewards.\n"
        "- Avoid generic headings and obvious cliches.\n"
        "- feature_cards must contain exactly 3, 4, or 6 items.\n"
        "- footer_brand_description must mention both featured game names.\n"
        "- Return data only.\n"
    )
    if not _cfg.OPENAI_TEXT_USE_JSON_SCHEMA:
        user_prompt += _LEGACY_OUTPUT_GUIDE

    return [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": user_prompt},
    ]


def _request_content(
    *,
    client: openai.OpenAI,
    model: str,
    messages: list[dict[str, str]],
    temperature: float,
) -> tuple[dict[str, Any], str]:
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        response_format=_response_format(),
    )
    raw = response.choices[0].message.content or ""
    if not raw.strip():
        raise ValueError("Model returned an empty response")
    return json.loads(raw), raw


def _rewrite_for_compliance(
    *,
    client: openai.OpenAI,
    model: str,
    messages: list[dict[str, str]],
    raw: str,
    violations: list[str],
) -> dict[str, Any]:
    revised_messages = list(messages)
    revised_messages.append({"role": "assistant", "content": raw})
    remaining = list(violations)
    last_fixed: dict[str, Any] | None = None

    for attempt in range(1, _COMPLIANCE_REWRITE_ATTEMPTS + 1):
        revised_messages.append(
            {
                "role": "user",
                "content": (
                    "Rewrite the full response so it stays natural while removing these "
                    f"prohibited terms: {', '.join(remaining)}. "
                    "Preserve the JSON structure and meaning, but replace each prohibited "
                    "term with safe entertainment-only wording. Return data only."
                ),
            }
        )
        fixed, fixed_raw = _request_content(
            client=client,
            model=model,
            messages=revised_messages,
            temperature=0.25,
        )
        last_fixed = fixed
        remaining = contains_banned_words(json.dumps(fixed), BANNED_WORDS)
        if not remaining:
            return fixed

        log.warning(
            f"Compliance rewrite attempt {attempt}/{_COMPLIANCE_REWRITE_ATTEMPTS} "
            f"still contains banned words with {model}: {remaining}"
        )
        revised_messages.append({"role": "assistant", "content": fixed_raw})

    raise ValueError(f"Banned words still present after rewrite: {remaining}")


def _generate_with_model(
    *,
    client: openai.OpenAI,
    model: str,
    messages: list[dict[str, str]],
    temperature: float,
    game1_name: str,
    game2_name: str,
) -> dict[str, Any]:
    content, raw = _request_content(
        client=client,
        model=model,
        messages=messages,
        temperature=temperature,
    )

    violations = contains_banned_words(json.dumps(content).lower(), BANNED_WORDS)
    if violations:
        log.warning(f"Banned words detected with {model}: {violations}")
        content = _rewrite_for_compliance(
            client=client,
            model=model,
            messages=messages,
            raw=raw,
            violations=violations,
        )

    _validate_content_keys(content, game1_name=game1_name, game2_name=game2_name)
    return content


@retry(
    max_attempts=MAX_RETRIES,
    backoff=RETRY_BACKOFF,
    exceptions=(openai.OpenAIError, json.JSONDecodeError, KeyError, ValueError),
)
def generate_site_content(
    game1_name: str,
    game2_name: str,
    topic: str,
    tone: str,
    brand_hint: str,
    temperature: float = 0.75,
    persona: str = "authoritative",
    theme: dict | None = None,
    palette: dict | None = None,
) -> dict[str, Any]:
    """Generate all site copy as a validated structured JSON dict."""
    client = _client()
    messages = _build_messages(
        game1_name=game1_name,
        game2_name=game2_name,
        topic=topic,
        tone=tone,
        brand_hint=brand_hint,
        persona=persona,
        theme=theme if isinstance(theme, dict) else None,
        palette=palette if isinstance(palette, dict) else None,
    )
    models = _model_candidates()
    if not models:
        raise ValueError("No text model configured. Set OPENAI_TEXT_MODEL_PRIMARY.")

    last_exc: Exception | None = None
    for index, model in enumerate(models):
        try:
            temp = temperature if index == 0 else min(temperature, 0.55)
            log.info(
                f"Generating copy for '{brand_hint}' with {model} "
                f"({topic} / {tone} / {persona} @ {temp})"
            )
            content = _generate_with_model(
                client=client,
                model=model,
                messages=messages,
                temperature=temp,
                game1_name=game1_name,
                game2_name=game2_name,
            )
            log.info(f"Site copy generated successfully with {model}")
            return content
        except (openai.OpenAIError, json.JSONDecodeError, KeyError, ValueError) as exc:
            last_exc = exc
            if index == len(models) - 1:
                raise
            log.warning(
                f"Primary text model '{model}' failed validation: {type(exc).__name__}: {exc}. "
                f"Trying fallback '{models[index + 1]}'."
            )

    raise RuntimeError("Text generation failed") from last_exc


def _validate_content_keys(
    content: dict[str, Any],
    *,
    game1_name: str,
    game2_name: str,
) -> None:
    """Raise ValueError when required structure or quality gates are missed."""
    required = {
        "brand_name",
        "meta_description",
        "hero_badge",
        "hero_headline_part1",
        "hero_headline_part2",
        "hero_subtext",
        "gallery_title",
        "gallery_description",
        "game1_description",
        "game2_description",
        "why_title",
        "why_description",
        "feature_cards",
        "contact_intro",
        "terms_sections",
        "privacy_sections",
        "cookie_intro",
        "footer_brand_description",
        "footer_legal_notice",
        "stats",
        "testimonials",
        "about",
        "cta_banner",
    }
    missing = required - set(content.keys())
    if missing:
        raise ValueError(f"AI response missing required keys: {missing}")

    feature_count = len(content.get("feature_cards", []))
    if feature_count not in {3, 4, 6}:
        raise ValueError("AI response must contain exactly 3, 4, or 6 feature_cards")

    if len(content.get("terms_sections", [])) < 6:
        raise ValueError("AI response must contain at least 6 terms_sections")
    if len(content.get("privacy_sections", [])) < 6:
        raise ValueError("AI response must contain at least 6 privacy_sections")

    stats_items = content.get("stats", {}).get("items", [])
    if len(stats_items) != 4:
        raise ValueError("AI response must contain exactly 4 stats items")

    testimonials = content.get("testimonials", {}).get("items", [])
    if len(testimonials) != 3:
        raise ValueError("AI response must contain exactly 3 testimonials")

    meta_description = str(content.get("meta_description", "")).strip()
    if len(meta_description) > 155:
        raise ValueError("meta_description must be 155 characters or fewer")

    for label, value in {
        "why_title": str(content.get("why_title", "")).strip().lower(),
        "gallery_title": str(content.get("gallery_title", "")).strip().lower(),
        "cta_banner.headline": str(content.get("cta_banner", {}).get("headline", "")).strip().lower(),
    }.items():
        if value in _GENERIC_HEADINGS:
            raise ValueError(f"{label} is too generic: {value!r}")

    footer_brand_description = str(content.get("footer_brand_description", "")).lower()
    if game1_name.lower() not in footer_brand_description:
        raise ValueError("footer_brand_description must mention game 1 by name")
    if game2_name.lower() not in footer_brand_description:
        raise ValueError("footer_brand_description must mention game 2 by name")
