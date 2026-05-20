# Whitepage Generator

A production-grade Python system that automatically generates complete
**PHP whitepage websites** for batches of local games.

Given a folder containing two game sub-directories, the generator:

- calls a **cost-optimized OpenAI text stack** to write all site copy (cheap primary model with quality fallback)
- calls **DALL-E 3** to create the hero image, background, game banners, icons, and brand logo
- assembles a fully structured **PHP site** with dark-theme CSS and vanilla JS
- moves the game folders into the right place and validates the output

The sites are entertainment-only compliant — no gambling terminology, 18+
notices on every legal page, and a USD→FUN proxy for game iframes.

---

## Requirements

| Requirement | Version |
|---|---|
| Python | 3.11+ |
| PHP (XAMPP) | 7.4+ |
| OpenAI API key | — |

---

## Installation

```bash
# 1. Clone / copy the scripts folder into C:\xampp\htdocs\scripts\

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Configure your API key
cp .env.example .env
# Open .env and set:  OPENAI_API_KEY=sk-...
```

---

## Quick start

### 1. Create a batch folder with two game sub-directories

```
C:\xampp\htdocs\
└── dragon-arena\           ← batch folder
    ├── dragon-quest\       ← game 1
    └── space-blast\        ← game 2
```

Each game folder must contain at minimum an `index.php` that XAMPP can serve.
Folder names may contain any characters that are valid on your OS (spaces,
uppercase letters, parentheses, etc.) — the generator handles them correctly.

### 2. Run the generator

```bash
cd C:\xampp\htdocs\scripts

# Minimal — topic and tone are inferred from folder names
python generate_whitepage.py --batch dragon-arena

# Explicit overrides
python generate_whitepage.py --batch dragon-arena \
    --topic fantasy \
    --tone dark \
    --container_opacity 0.08
```

### 3. Open in browser

```
http://localhost/dragon-arena/
```

---

## CLI reference

```
python generate_whitepage.py --batch NAME [OPTIONS]

Required:
  --batch NAME          Folder name inside C:\xampp\htdocs\
                        Must contain exactly two game sub-directories.

Optional:
  --topic TOPIC         Content theme (see table below).
                        Inferred from game folder names when omitted.

  --tone TONE           Visual and copy tone (see table below).
                        Inferred from game folder names when omitted.

  --container_opacity F Accepted for backward compatibility; currently has
                        no effect on card backgrounds (cards are solid dark).
                        Default: 0.05
```

### Topics

| Value | Style |
|---|---|
| `fantasy` | Swords, magic, dragons |
| `sci-fi` | Space, robots, neon |
| `battle` | Warriors, arenas, combat |
| `legend` | Ancient heroes, epics |
| `sports` | Arenas, trophies, speed |
| `horror` | Dark, eerie, atmospheric |
| `adventure` | Exploration, treasure, maps |
| `colorful` | Candy, gems, vibrant |

### Tones

| Value | Feel |
|---|---|
| `dark` | Deep blues, moody lighting |
| `fierce` | High energy, dramatic |
| `warm` | Golden tones, inviting |
| `colorful` | Vibrant neon, playful |
| `horror` | Eerie greens, dim |

---

## Output structure

After generation, the batch folder looks like this:

```
C:\xampp\htdocs\dragon-arena\
├── index.php               Home — hero, game gallery, features
├── game.php                Game page — sanitised iframe loader
├── game_proxy.php          USD → FUN output-buffer proxy
├── contact.php             Contact form (JS fake-submit)
├── terms.php               Terms of Use — 6 AI sections
├── privacy.php             Privacy Policy — 6 AI sections
├── cookie.php              Cookie Policy
├── styles.css              Dark theme — responsive, Google Fonts
├── script.js               Cookie banner, menu, form, scroll animations,
│                           navbar shrink-on-scroll
├── partials/
│   ├── header.php          Sticky nav with scroll-shrink effect + active-link logic
│   └── footer.php          3-column footer + cookie banner
├── assets/
│   ├── images/
│   │   ├── hero.jpg                    1792×1024 hero scene
│   │   ├── background.jpg              1024×1024 subtle bg texture
│   │   ├── banner_dragon-quest.jpg     game 1 banner
│   │   └── banner_space-blast.jpg      game 2 banner
│   └── icons/
│       ├── logo.png                    AI-generated brand logo (DALL-E 3, 1024×1024)
│       ├── logo.svg                    Procedural SVG letter-mark (favicon fallback only)
│       ├── icon_1.png                  Feature card icons ×6
│       └── …
└── games/
    ├── dragon-quest/       ← moved from batch root
    └── space-blast/        ← moved from batch root
```

---

## Visual design

### Page wrapper
All page content (header, main, footer) is enclosed in a `.page-wrapper`
card — a dark glass panel with a purple-accent border, rounded corners,
and layered drop shadows. On screens narrower than 768px the wrapper
expands edge-to-edge (no margins or rounded corners).

### Typography
- **Body / UI** — [Inter](https://fonts.google.com/specimen/Inter) loaded
  via Google Fonts; falls back to system-ui / Segoe UI
- **Headings / brand** — [Space Grotesk](https://fonts.google.com/specimen/Space+Grotesk)
  loaded via Google Fonts; geometric and slightly techy

### Navbar
The navbar starts at **92px tall** and smoothly shrinks to **64px** once
the user scrolls past 60px. The brand logo and text scale down with it.
A purple gradient accent line sits at the very top and fades on scroll.
All transitions use `cubic-bezier(0.4, 0, 0.2, 1)` for a material-style feel.

### Cards
All content cards (game cards, feature cards, form card, legal sections)
use a solid dark background (`rgba(20, 20, 48, 0.97)`) for maximum text
readability against the page background image.

---

## Batch processing

Process multiple batches in one script:

```python
from generator.main import run_batch

run_batch(
    ["dragon-arena", "space-duo", "fun-pack"],
    topic="fantasy",
    tone="dark",
)
```

Or from the CLI in a shell loop:

```bash
for batch in dragon-arena space-duo fun-pack; do
    python generate_whitepage.py --batch "$batch"
done
```

---

## Configuration

All settings live in `generator/config.py`.  The most commonly changed values:

| Variable | Default | Purpose |
|---|---|---|
| `HTDOCS_ROOT` | `C:/xampp/htdocs` | Set via `HTDOCS_ROOT` env var |
| `OPENAI_TEXT_MODEL_PRIMARY` | `gpt-5-mini` | Default low-cost copy model |
| `OPENAI_TEXT_MODEL_FALLBACK` | `gpt-5.4-mini` | Stronger fallback used only when validation fails |
| `OPENAI_TEXT_ENABLE_FALLBACK` | `true` | Enables automatic quality fallback |
| `OPENAI_TEXT_USE_JSON_SCHEMA` | `true` | Uses structured outputs instead of a large prompt schema |
| `OPENAI_TEXT_MODEL` | `(legacy alias)` | Backward-compatible override for the primary text model |
| `OPENAI_IMAGE_MODEL` | `dall-e-3` | Image model |
| `OPENAI_IMAGE_QUALITY` | `standard` | `standard` or `hd` |
| `MAX_RETRIES` | `3` | API retry attempts |
| `RETRY_BACKOFF` | `2.0` | Exponential backoff base (seconds) |
| `DEFAULT_CONTAINER_OPACITY` | `0.05` | Accepted by CLI; no effect on card backgrounds |

---

## Architecture

```
generate_whitepage.py
        │
        └── generator/main.py::run()
                │
                ├── cli.py              parse + validate args
                ├── game_detector.py    find exactly 2 game folders
                ├── file_manager.py     scaffold dirs, move games/
                ├── utils.py            infer topic + tone from names
                │
                ├── ai_text.py          Primary mini model → JSON, fallback on validation failure
                │     └── banned-word rewrite pass if needed
                │
                ├── ai_image.py         DALL-E 3 → 10 images + logo (sequential)
                │
                ├── template_engine.py  CSS (Google Fonts, scroll effects) + JS + SVG logo
                ├── php_generator.py    9 PHP files from SiteContext
                └── validator.py        check all required files exist
```

### Key design decisions

**`[[PLACEHOLDER]]` substitution for PHP**
PHP uses `{` `}` in every control structure. Python f-strings on PHP source
strings cause immediate syntax errors. All PHP templates use
`str.replace("[[KEY]]", value)` instead.

**Single structured text pass**
All site copy (hero, gallery, cards, legal pages) is generated in one
structured JSON request. The generator now prefers a cheaper primary model,
uses JSON schema mode to reduce prompt overhead, and only escalates to a
stronger fallback model when validation or compliance checks fail.

**Sequential DALL-E calls**
Images are generated one at a time with a short courtesy delay. Parallel
calls on standard/free tiers hit rate limits immediately.

**DALL-E logo + SVG fallback**
The brand logo displayed in the navbar and footer is a DALL-E 3 generated
`logo.png`. A minimal letter-mark `logo.svg` is also written and used only
as the `<link rel="icon">` favicon fallback.

**`game_proxy.php`**
The game iframe points to `game_proxy.php?game=<slug>` rather than directly
to the game file. The proxy wraps the game in `ob_start()` / `ob_get_clean()`
and replaces `USD` with `FUN` before serving.

**Input sanitisation in `game.php` and `game_proxy.php`**
The `?game=` parameter has path separators (`/`, `\`), traversal sequences
(`..`), null bytes, and control characters stripped out, then the result is
checked against a hardcoded whitelist of exactly the two valid folder names.
An allowlist regex like `[^a-z0-9\-_]` is intentionally avoided — it would
break folder names containing uppercase letters, spaces, or other valid
characters.

**Page wrapper**
The `.page-wrapper` div encloses every page's header, content, and footer
as a single dark-glass card. `overflow: clip` (CSS4) clips children to the
border-radius without creating a scroll container, so `position: sticky` on
the navbar still works.

**Navbar shrink on scroll**
JS listens on the `scroll` event (passive) and toggles a `.scrolled` class
on `#navbar`. CSS transitions handle the height (92px → 64px), logo size,
brand font size, box-shadow, and accent-line opacity. No layout thrashing —
only compositor-friendly properties animate.

---

## Compliance rules

The generator enforces these rules automatically:

- Banned words are checked after every text-model response and a rewrite is
  requested if any are found (see `config.BANNED_WORDS`).
- 18+ notices appear on every legal page and in the footer on every page.
- "Entertainment only — no real rewards" messaging is injected into all
  footer legal sections and terms/privacy content.
- The USD→FUN proxy applies at runtime to game output.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `Expected exactly 2 game folders` | Your batch folder has more or fewer than 2 sub-directories. Move/remove extras. |
| `OPENAI_API_KEY is not set` | Add your key to `.env` (copy from `.env.example`). |
| `API failure after 3 attempts` | Check your OpenAI account quota and network. |
| Images look wrong / placeholder | DALL-E 3 rate limit hit — wait 60s and retry. |
| PHP site shows blank page | Ensure XAMPP Apache is running and the batch folder is under `htdocs/`. |
| `Game not found` on game.php | The `?game=` slug must exactly match the folder name inside `games/`. |
| Fonts not loading | Site needs internet access to fetch Google Fonts. For offline use, download Inter and Space Grotesk locally and update the `@import` URL in `styles.css`. |
