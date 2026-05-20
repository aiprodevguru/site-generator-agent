# CLAUDE.md — Whitepage Generator

Instructions for Claude Code when working in this repository.

---

## What this project is

A modular Python system that auto-generates complete PHP whitepage websites for
batches of two local games.  It calls OpenAI (GPT-4o + DALL-E 3) to produce
all copy and images, then writes a fully structured PHP site under
`C:\xampp\htdocs\<batch_name>\`.

The output is a compliant entertainment-only site — no gambling terminology,
18+ notices throughout, iframe-based game embedding with a USD→FUN proxy.

Every batch is visually unique — a deterministic variation engine hashes the
batch name to pick a palette, font set, theme, and layout parameters; icon
subjects are sampled randomly from a 1000-item pool each run.

---

## Module map

```
generate_whitepage.py          Entry point — calls generator/main.py::run()

generator/
  config.py                    Constants: paths, API settings, banned words, keyword maps
  logger.py                    Coloured ANSI logger (get_logger / log)
  utils.py                     retry decorator, slugify, folder_to_title, infer_topic/tone
  cli.py                       argparse — parse_args() returns validated Namespace
  game_detector.py             detect_games() → (GameInfo, GameInfo) — must be exactly 2
  file_manager.py              scaffold_directories, move_game_folders, write_text, write_binary
  ai_text.py                   GPT-4o single JSON call → dict; banned-word rewrite pass
  ai_image.py                  DALL-E 3 → GeneratedImages namedtuple (hero/bg/banners/icons/logo)
  template_engine.py           generate_css() / generate_js() / generate_logo_svg()
  php_generator.py             SiteContext dataclass + PHPGenerator class → 9 PHP files
  validator.py                 validate_output() — checks all required files present
  main.py                      Pipeline: parse → detect → scaffold → move → AI → write → validate
  variation_engine.py          build_variation_config(batch_name) → VariationConfig
  variant.py                   Backward-compat shim — re-exports from variation_engine

  variation_data/
    __init__.py
    palettes.py                100 curated color palettes in 11 visual families
    fonts.py                   100 Google Font combinations
    themes.py                  30 character/visual themes with AI prompt descriptors
    animations.py              50 animation sets (enter, hover, stagger timing)
    layouts.py                 All layout option pools (header, footer, nav, legacy fields)
    icons.py                   1000 icon prompt subjects + sample_icon_subjects()

  gallery/
    __init__.py                (package init — in progress)
```

---

## Variation engine

`build_variation_config(batch_name)` in `variation_engine.py` uses the MD5
hash of the batch name to deterministically pick from every variation pool.
The same batch name always produces the same `VariationConfig`.

```python
from generator.variation_engine import build_variation_config
v = build_variation_config("dragon-arena")
# v.palette     — full palette dict (name, family, bg_page, glow, img_desc, …)
# v.font_set    — full font dict (google_url, logo_css, heading_css, …)
# v.theme       — character/visual theme (name, char_desc, setting_desc, icon_bg, …)
# v.animation_set — animation personality (anim_in, duration, easing, stagger, …)
# v.hero_layout, v.game_layout, v.feat_layout, v.nav_style, … — layout fields
# v.gpt_temp, v.gpt_persona, v.img_style, v.img_composition — AI parameters
# v.extra_sections — frozenset of optional home-page sections
```

**`variant.py` is a thin re-export shim** — all real logic lives in
`variation_engine.py`.  `SiteVariant` and `pick_variant` still work but are
aliases for `VariationConfig` and `build_variation_config`.

### Palette is now a dict, not a string
Old code compared `v.palette` to string keys like `"neon"`.  It is now a full
dict from `palettes.py`.  Always guard: `if isinstance(v.palette, dict)`.
Access fields as `v.palette["name"]`, `v.palette["glow"]`, etc.

### Theme is a dict
`v.theme` is a full dict from `themes.py` with keys `name`, `topic`, `tone`,
`char_desc`, `setting_desc`, `ai_style`, `ai_comp`, `icon_bg`.

### Icon subjects are random
`ai_image.py` calls `sample_icon_subjects(6)` from `variation_data/icons.py`
which uses `random.sample()` on the 1000-item pool — a different set every run.
`config.ICON_SUBJECTS` is no longer used by `ai_image.py`.

---

## Architecture rules — follow these when editing

### PHP template generation
PHP files are built via `str.replace("[[PLACEHOLDER]]", value)` — **never
use Python f-strings on PHP source strings**.  PHP uses `{` and `}` in every
control structure and they collide with Python f-string interpolation.

### Content injection flow
1. `ai_text.generate_site_content()` returns a raw `dict[str, Any]`
2. `php_generator.build_context()` converts it into a typed `SiteContext`
3. `PHPGenerator(ctx).write_all(batch_dir)` renders every PHP file

### CSS placeholders
`styles.css` is built from `_CSS_TEMPLATE` in `template_engine.py` using
`str.replace()` on three placeholders:

| Placeholder | Injected by | Content |
|---|---|---|
| `[[FONT_IMPORTS]]` | `generate_css()` | `@import url(...)` from `v.font_set["google_url"]` |
| `[[VARIANT_CSS]]` | `generate_css()` → `_variant_css()` | Palette `:root {}` vars, font overrides, animation overrides |
| `[[TOPIC_FX]]` | `generate_css()` → `_topic_fx()` | Topic-specific visual effects CSS |

Do **not** hardcode `@import url(...)` for fonts — it is injected via
`[[FONT_IMPORTS]]` so each batch gets its chosen Google Font pair.

### Theme and palette flow into AI generators
Both `ai_text.generate_site_content()` and `ai_image.generate_all_images()`
accept optional `theme: dict | None` and `palette: dict | None` parameters.
`main.py` passes `variant.theme` and `variant.palette` to both.

- **Text**: `theme["char_desc"]` and `theme["setting_desc"]` are injected into
  the GPT-4o prompt as a "Visual universe" line for thematically appropriate copy.
- **Images**: `palette["img_desc"]` drives color mood; `theme["setting_desc"]`
  and `theme["char_desc"]` describe the world; `theme["icon_bg"]` sets the
  background for icon generation.

### Game banner prompts
Banner prompts explicitly ask DALL-E to *interpret the meaning and spirit of
the game name* as the visual focus.  Do not reduce this back to a simple label
— the game name should drive what characters and setting appear.

### Feature section icon display
All three feature layouts (`_features_icons`, `_features_numbered`,
`_features_horizontal`) render icon images via `<img>` tags.
`_features_numbered()` shows both the icon image and the oversized number.

### Page wrapper
Every page body is wrapped in `<div class="page-wrapper">` (opened in
`_header()`, closed in `_footer()`).  The wrapper is a card with a dark
glass background, a purple accent border, rounded corners, and layered
shadow.  The cookie banner lives **outside** the wrapper because it is
`position: fixed` to the viewport.

`overflow: clip` (not `overflow: hidden`) is used on `.page-wrapper` —
this clips children to the border-radius visually without creating a new
scroll container, so `position: sticky` on the navbar still works.

### Fonts
CSS font imports are injected per-batch via `[[FONT_IMPORTS]]`.  The fallback
when no variant is supplied is a static Inter + Space Grotesk import.  Both
fonts have full system-font fallback chains for offline rendering.

### Card backgrounds
`--card-bg` is hardcoded to `rgba(20, 20, 48, 0.97)` — essentially solid
dark.  The `generate_css(container_opacity)` signature is kept for
backward compatibility but the parameter no longer affects card backgrounds.
Do not revert cards to semi-transparent; this hurts text readability.

### Navbar scroll effect
The navbar starts tall (92px) and shrinks to 64px once the user scrolls
past 60px.  CSS handles the animation via a `.scrolled` class; JS adds /
removes it.  Affected properties: `height`, `font-size` of brand,
`width`/`height` of logo image, `box-shadow`, accent-line `opacity`.
All transitions run at `0.38s cubic-bezier(0.4, 0, 0.2, 1)`.

### Game slug sanitization
`game.php` and `game_proxy.php` use a **blocklist** approach — they strip
path separators (`/`, `\`), path traversal (`..`), null bytes, and control
characters (`\r`, `\n`) from the `?game=` parameter.  The `array_key_exists`
/ `in_array` whitelist check that follows is the authoritative security gate.
Do not revert to the old allowlist (`[^a-z0-9\-_]`) — it breaks folder
names that contain uppercase letters, spaces, or other valid characters.

### iframe URL construction
`game.php` builds a root-relative URL for the iframe src:
```
{base_dir}/games/{game_key}/index.php
```
`$base_dir` is `dirname($_SERVER['SCRIPT_NAME'])` — the batch root path on
the server (e.g. `/dragon-arena`). No protocol or host is needed because the
iframe is served from the same origin as the whitepage.

### Logo assets
`ai_image.py` generates a square `logo.png` via DALL-E 3 (saved to
`assets/icons/logo.png`).  `template_engine.generate_logo_svg()` produces
a minimal letter-mark SVG that is saved as `assets/icons/logo.svg` and
used only as the `<link rel="icon">` favicon fallback.  The `<img>` tags
in the navbar and footer always reference `logo.png`.

### Banned words
The full list lives in `config.BANNED_WORDS`.  `ai_text.py` automatically
runs a second GPT-4o rewrite pass if any are found.  If you add new pages or
copy-generating code, always check output against `utils.contains_banned_words()`.

### Retry decorator
All API calls use `@retry(max_attempts=3, backoff=2.0, exceptions=(...))` from
`utils.py`.  Do not add bare `try/except` around API calls — use the decorator.

### File writes
Always route through `file_manager.write_text()` or `file_manager.write_binary()`.
Do not call `Path.write_text()` directly in other modules — the manager handles
parent-directory creation and debug logging uniformly.

---

## Running the pipeline

```bash
# Requires OPENAI_API_KEY in .env (see .env.example)
python generate_whitepage.py --batch dragon-arena
python generate_whitepage.py --batch space-duo --topic sci-fi --tone dark
```

## Testing without API calls

```python
from generator.php_generator import PHPGenerator, build_context
from generator.template_engine import generate_css, generate_js
from generator.variation_engine import build_variation_config

variant = build_variation_config("test")

ctx = build_context(
    batch_name="test", brand_name="My Site", topic="fantasy", tone="dark",
    current_year=2025,
    game1_folder="game-one", game1_name="Game One",
    game1_banner="assets/images/banner_game-one.jpg",
    game2_folder="game-two", game2_name="Game Two",
    game2_banner="assets/images/banner_game-two.jpg",
    icon_paths=[f"assets/icons/icon_{i}.png" for i in range(1, 7)],
    ai_content={ ... },   # fill with dict matching the schema in ai_text.py
    variant=variant,
)

index_php = PHPGenerator(ctx)._index()
css = generate_css(variant=variant)   # injects palette vars + chosen font
```

## Syntax check (covers all sub-packages)

```bash
python -c "
import ast, pathlib
for p in pathlib.Path('generator').rglob('*.py'):
    ast.parse(p.read_text('utf-8'))
print('clean')
"
```

---

## Adding a new page

1. Add a `_newpage(self) -> str` method to `PHPGenerator` using the same
   `self._page(active_page, title, body)` wrapper pattern.
2. Add the filename to the `files` dict inside `PHPGenerator.write_all()`.
3. Add the relative path to `config.REQUIRED_OUTPUT_FILES`.
4. Add a nav entry in `PHPGenerator._header()` if it needs a nav link.

## Adding a new topic or tone

Edit `config.TOPIC_KEYWORDS` / `config.TONE_KEYWORDS` — no other file
changes needed.  `utils.infer_topic()` and `utils.infer_tone()` iterate
the maps automatically.

Note: `config.ICON_SUBJECTS` is no longer used for image generation — icon
subjects now come from `variation_data/icons.py`.

## Adding palettes / fonts / themes / animations

Edit the relevant file in `generator/variation_data/`.  Each file has an
`assert len(...) == N` guard at the bottom — update the expected count when
adding entries.  `build_variation_config()` picks from these pools using bit
offsets into the batch MD5 hash; adding entries automatically widens the pool.

---

## Common mistakes to avoid

- Do not treat `v.palette` as a string — it is a dict.  Access fields as
  `v.palette["name"]`, `v.palette["glow"]`, etc.  Guard with
  `isinstance(v.palette, dict)` before accessing dict keys.
- Do not hardcode `@import url(...)` for fonts in the CSS template — fonts
  are injected per-batch via `[[FONT_IMPORTS]]`.
- Do not use `config.ICON_SUBJECTS` for icon generation — use
  `variation_data.icons.sample_icon_subjects()` instead.
- Do not put gambling-adjacent words in any template string — they will pass
  the Python layer but appear in PHP output and fail the compliance check.
- Do not hardcode `C:\xampp\htdocs` anywhere — always use `config.HTDOCS_ROOT`
  which reads from the `HTDOCS_ROOT` env var with a sensible default.
- Do not call `openai.OpenAI()` without checking `OPENAI_API_KEY` first —
  both `ai_text._client()` and `ai_image._client()` already guard this.
- Image URLs from DALL-E are temporary — always download immediately (see
  `ai_image._generate_one()`).  Never store the URL and fetch later.
- Do not make card backgrounds semi-transparent — `--card-bg` must stay
  near-opaque for text to be readable against the page background image.
- Do not revert the game slug sanitization to an allowlist — it breaks
  folder names with uppercase letters, spaces, or other valid characters.
  The whitelist (`array_key_exists`) is the security gate, not the regex.

---

## Dependencies

```
openai>=1.0.0
requests>=2.31.0
python-dotenv>=1.0.0
```

Install: `pip install -r requirements.txt`
