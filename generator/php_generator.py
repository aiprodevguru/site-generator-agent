"""
PHP site generator.

Builds all PHP pages, partials, and the USD→FUN proxy using content
provided via ``SiteContext``.

Template strategy
-----------------
Every template uses ``[[PLACEHOLDER]]`` markers.  Python never uses f-strings
on PHP source because PHP's ``{}`` block syntax would collide with Python's
f-string interpolation syntax.  All substitution is done with ``.replace()``.
"""
from __future__ import annotations

import html
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from generator.file_manager      import write_text
from generator.logger            import get_logger
from generator.variant           import SiteVariant, pick_variant
from generator.gallery.renderer  import GalleryRenderer

log = get_logger("php_generator")


# ═══════════════════════════════════════════════════════════════════════════════
#  Data model
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class FeatureCard:
    icon_path:   str   # relative web path, e.g. 'assets/icons/icon_1.png'
    title:       str
    description: str


@dataclass
class ContentSection:
    heading: str
    body:    str


@dataclass
class StatItem:
    number: str   # e.g. "1M+", "24/7", "100+"
    label:  str   # e.g. "Active Players", "Support"


@dataclass
class TestimonialItem:
    quote:  str   # 1-2 sentence player quote
    author: str   # first name + initial, e.g. "Alex T."


@dataclass
class SiteContext:
    """All data required to render a complete whitepage site."""

    # ── Batch & branding ──────────────────────────────────────────────
    batch_name:   str
    brand_name:   str
    topic:        str
    tone:         str
    current_year: int
    variant:      SiteVariant

    # ── Games ─────────────────────────────────────────────────────────
    game1_folder:      str
    game1_name:        str
    game1_banner:      str   # e.g. 'games/dragon-quest/banner.png'
    game1_description: str

    game2_folder:      str
    game2_name:        str
    game2_banner:      str   # e.g. 'games/space-blast/banner.png'
    game2_description: str

    # ── Meta / SEO ────────────────────────────────────────────────────
    meta_description: str

    # ── Hero ──────────────────────────────────────────────────────────
    hero_badge:           str
    hero_headline_part1:  str
    hero_headline_part2:  str
    hero_subtext:         str

    # ── Gallery ───────────────────────────────────────────────────────
    gallery_title:       str
    gallery_description: str

    # ── Features ──────────────────────────────────────────────────────
    why_title:       str
    why_description: str
    feature_cards:   list[FeatureCard] = field(default_factory=list)

    # ── Contact ───────────────────────────────────────────────────────
    contact_intro: str = ""

    # ── Legal ─────────────────────────────────────────────────────────
    terms_sections:   list[ContentSection] = field(default_factory=list)
    privacy_sections: list[ContentSection] = field(default_factory=list)
    cookie_intro:     str = ""

    # ── Footer ────────────────────────────────────────────────────────
    footer_brand_description: str = ""
    footer_legal_notice:      str = ""

    # ── Optional home-page sections ──────────────────────────────────
    stats_title:        str = ""
    stats_items:        list[StatItem] = field(default_factory=list)
    testimonials_title: str = ""
    testimonials_items: list[TestimonialItem] = field(default_factory=list)
    about_title:        str = ""
    about_body:         str = ""
    cta_headline:       str = ""
    cta_subtext:        str = ""
    cta_button_text:    str = "Explore All Games"


# ═══════════════════════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _h(text: str) -> str:
    """HTML-escape a string for safe embedding in HTML content."""
    return html.escape(text, quote=False)


def _ha(text: str) -> str:
    """HTML-escape a string for safe embedding in an HTML attribute."""
    return html.escape(text, quote=True)


def _php_str(text: str) -> str:
    """Escape a string for embedding inside a PHP single-quoted string literal."""
    return text.replace("\\", "\\\\").replace("'", "\\'")


def _section_id(heading: str) -> str:
    """Convert a section heading to a URL-safe anchor id."""
    return heading.lower().replace(" ", "-").replace("/", "-")


def _render_legal_sections(sections: list[ContentSection]) -> str:
    """Render a list of ContentSection objects as HTML legal cards."""
    parts: list[str] = []
    for i, sec in enumerate(sections, 1):
        sid  = _section_id(sec.heading)
        body = _h(sec.body).replace("\n\n", "</p><p>").replace("\n", " ")
        parts.append(
            f'        <div class="legal-section fade-in" id="{sid}">\n'
            f'          <h2><span class="text-accent">{i:02d}</span> {_h(sec.heading)}</h2>\n'
            f'          <p>{body}</p>\n'
            f'        </div>'
        )
    return "\n".join(parts)


def _render_toc(sections: list[ContentSection]) -> str:
    """Render a table-of-contents list for legal pages."""
    items = [
        f'<li><a href="#{_section_id(s.heading)}">{_h(s.heading)}</a></li>'
        for s in sections
    ]
    return "\n          ".join(items)


def _feature_grid_classes(*classes: str, count: int) -> str:
    names = [name for name in classes if name]
    names.append(f"features-count-{count}")
    return " ".join(names)


def _count_grid_classes(prefix: str, *classes: str, count: int) -> str:
    names = [name for name in classes if name]
    names.append(f"{prefix}-count-{count}")
    return " ".join(names)


# ═══════════════════════════════════════════════════════════════════════════════
#  PHPGenerator
# ═══════════════════════════════════════════════════════════════════════════════

class PHPGenerator:
    """
    Generates all PHP files for a whitepage site from a ``SiteContext``.

    Usage::

        gen = PHPGenerator(ctx)
        gen.write_all(batch_dir)
    """

    def __init__(self, ctx: SiteContext) -> None:
        self.ctx      = ctx
        self._gallery = GalleryRenderer()

    # ── Public entrypoint ──────────────────────────────────────────────────────

    def write_all(self, batch_dir: Path) -> None:
        """Write every PHP file for the site under *batch_dir*."""
        files = {
            "partials/header.php": self._header(),
            "partials/footer.php": self._footer(),
            "index.php":           self._index(),
            "game.php":            self._game(),
            "game_proxy.php":      self._game_proxy(),
            "contact.php":         self._contact(),
            "terms.php":           self._terms(),
            "privacy.php":         self._privacy(),
            "cookie.php":          self._cookie(),
        }
        for rel, content in files.items():
            write_text(batch_dir / rel, content)
            log.info(f"Generated  {rel}")

    # ── Shared page wrapper helper ─────────────────────────────────────────────

    def _page(self, active_page: str, title: str, body: str) -> str:
        """Wrap *body* with PHP include calls for header and footer partials."""
        safe_title = _php_str(title)
        safe_page  = _php_str(active_page)
        return (
            "<?php\n"
            f"$page_title  = '{safe_title}';\n"
            f"$active_page = '{safe_page}';\n"
            "include 'partials/header.php';\n"
            "?>\n\n"
            + body
            + "\n\n<?php include 'partials/footer.php'; ?>\n"
        )

    # ══════════════════════════════════════════════════════════════════════════
    #  partials/header.php
    # ══════════════════════════════════════════════════════════════════════════

    def _header(self) -> str:
        ctx = self.ctx
        v = ctx.variant
        brand    = _h(ctx.brand_name)
        brand_ha = _ha(ctx.brand_name)
        meta     = _ha(ctx.meta_description)

        # Nav items: (label, href, page_key)
        nav_items = [
            ("Home",         "index.php",   "home"),
            ("Game Gallery", "index.php#games", "games"),
            ("Contact",      "contact.php", "contact"),
            ("Terms",        "terms.php",   "terms"),
            ("Privacy",      "privacy.php", "privacy"),
        ]

        nav_links = "\n    ".join(
            f'<li><a href="{href}"'
            f' <?php if ($active_page === \'{key}\') echo \'class="active"\'; ?>>'
            f'{label}</a></li>'
            for label, href, key in nav_items
        )

        navbar_classes = " ".join([
            "navbar",
            f"navbar-logo-{_ha(v.header_logo_pos)}",
            f"navbar-nav-{_ha(v.header_nav_style)}",
            f"navbar-menu-{_ha(v.menu_hover)}",
            f"navbar-space-{_ha(v.menu_spacing)}",
            f"navbar-cta-{_ha(v.header_cta)}",
        ])
        menu_classes = " ".join([
            "nav-menu",
            f"nav-menu-style-{_ha(v.header_nav_style)}",
            f"nav-menu-hover-{_ha(v.menu_hover)}",
            f"nav-menu-space-{_ha(v.menu_spacing)}",
        ])
        cta_html = ""
        if v.header_cta != "none":
            cta_html = (
                f'\n  <a class="nav-cta nav-cta-{_ha(v.header_cta)}" href="index.php#games">'
                f'Play Now</a>'
            )

        return f"""<?php
// Variables expected from the including page:
//   $page_title  (string) — browser tab title
//   $active_page (string) — nav highlight key
$page_title  = isset($page_title)  ? $page_title  : '{_php_str(brand)}';
$active_page = isset($active_page) ? $active_page : '';
?>
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="{meta}">
  <meta name="robots" content="index, follow">
  <title><?php echo htmlspecialchars($page_title); ?></title>
  <link rel="stylesheet" href="styles.css">
  <link rel="icon" href="assets/icons/logo.svg" type="image/svg+xml">
  <link rel="apple-touch-icon" href="assets/icons/logo.png">
</head>
<body>

<div class="page-wrapper">

<nav class="{navbar_classes}" id="navbar" role="navigation" aria-label="Main navigation">
  <a class="navbar-brand" href="index.php" aria-label="{brand_ha} home">
    <img src="assets/icons/logo.png" alt="{brand_ha} logo" width="40" height="40">
    <span>{brand}</span>
  </a>

  {cta_html}

  <button class="hamburger" id="hamburger"
          aria-label="Toggle navigation" aria-expanded="false"
          aria-controls="nav-menu">
    <span></span><span></span><span></span>
  </button>

  <ul class="{menu_classes}" id="nav-menu">
    {nav_links}
  </ul>
</nav>
"""

    # ══════════════════════════════════════════════════════════════════════════
    #  partials/footer.php  — dispatches to one of 4 layout variants
    # ══════════════════════════════════════════════════════════════════════════

    def _footer(self) -> str:
        v = self.ctx.variant
        dispatch = {
            "standard": self._footer_standard,
            "wide":     self._footer_wide,
            "centered": self._footer_centered,
            "compact":  self._footer_compact,
        }
        footer_body = dispatch.get(v.footer_style, self._footer_standard)()
        return footer_body + self._footer_tail()

    def _footer_tail(self) -> str:
        """Closing wrapper + cookie banner + scripts — shared by all footer variants."""
        return """
</div><!-- /.page-wrapper -->

<!-- Cookie banner lives outside the wrapper — it is position:fixed to the viewport -->
<div class="cookie-banner" id="cookie-banner" role="dialog" aria-label="Cookie notice">
  <p class="cookie-text">
    We use essential cookies only to keep the site running.
    No tracking, no ads. <a href="cookie.php">Learn more</a>.
  </p>
  <div class="cookie-actions">
    <button id="btn-accept-cookies"  class="btn btn-primary btn-sm">Accept</button>
    <button id="btn-decline-cookies" class="btn btn-outline btn-sm">Decline</button>
  </div>
</div>

<script src="script.js"></script>
</body>
</html>
"""

    def _footer_standard(self) -> str:
        """3-col: brand | quick links | legal. Default layout."""
        ctx   = self.ctx
        brand = _h(ctx.brand_name)
        desc  = _h(ctx.footer_brand_description)
        legal = _h(ctx.footer_legal_notice)
        g1    = _h(ctx.game1_name)
        g2    = _h(ctx.game2_name)
        year  = ctx.current_year

        ql_html = "\n        ".join(
            f'<li><a href="{href}">{label}</a></li>'
            for label, href in [
                ("Home",         "index.php"),
                ("Game Gallery", "index.php#games"),
                ("Contact Us",   "contact.php"),
                ("Terms of Use", "terms.php"),
                ("Privacy",      "privacy.php"),
                ("Cookies",      "cookie.php"),
            ]
        )
        return f"""
<footer class="footer" role="contentinfo">
  <div class="footer-grid">
    <div class="footer-brand">
      <a class="footer-brand-logo" href="index.php">
        <img src="assets/icons/logo.png" alt="{brand} logo" width="34" height="34">
        <span>{brand}</span>
      </a>
      <p>{desc}</p>
    </div>
    <div class="footer-col">
      <p class="footer-col-title">Quick Links</p>
      <ul class="footer-links">
        {ql_html}
      </ul>
    </div>
    <div class="footer-col footer-legal-note">
      <p class="footer-col-title">Legal</p>
      <p>{legal}</p>
      <p>Features: {g1} &amp; {g2}.</p>
    </div>
  </div>
  <div class="footer-bottom">
    <p>&copy; {year} {brand}. All rights reserved.</p>
    <div class="footer-bottom-links">
      <a href="terms.php">Terms</a>
      <a href="privacy.php">Privacy</a>
      <a href="cookie.php">Cookies</a>
    </div>
  </div>
</footer>"""

    def _footer_wide(self) -> str:
        """4-col: brand | navigation | legal | games. Accent top border."""
        ctx   = self.ctx
        brand = _h(ctx.brand_name)
        desc  = _h(ctx.footer_brand_description)
        legal = _h(ctx.footer_legal_notice)
        g1n   = _h(ctx.game1_name)
        g2n   = _h(ctx.game2_name)
        g1f   = _ha(ctx.game1_folder)
        g2f   = _ha(ctx.game2_folder)
        year  = ctx.current_year

        return f"""
<footer class="footer footer-wide" role="contentinfo">
  <div class="footer-grid footer-grid-4">

    <div class="footer-brand">
      <a class="footer-brand-logo" href="index.php">
        <img src="assets/icons/logo.png" alt="{brand} logo" width="40" height="40">
        <span>{brand}</span>
      </a>
      <p>{desc}</p>
    </div>

    <div class="footer-col">
      <p class="footer-col-title">Navigation</p>
      <ul class="footer-links">
        <li><a href="index.php">Home</a></li>
        <li><a href="index.php#games">Game Gallery</a></li>
        <li><a href="contact.php">Contact Us</a></li>
      </ul>
    </div>

    <div class="footer-col">
      <p class="footer-col-title">Legal</p>
      <ul class="footer-links">
        <li><a href="terms.php">Terms of Use</a></li>
        <li><a href="privacy.php">Privacy Policy</a></li>
        <li><a href="cookie.php">Cookie Policy</a></li>
      </ul>
      <p class="footer-legal-note" style="margin-top:1rem;">{legal}</p>
    </div>

    <div class="footer-col">
      <p class="footer-col-title">Featured Games</p>
      <ul class="footer-links">
        <li><a href="game.php?game={g1f}">{g1n}</a></li>
        <li><a href="game.php?game={g2f}">{g2n}</a></li>
        <li><a href="index.php#games">View All &rarr;</a></li>
      </ul>
    </div>

  </div>
  <div class="footer-bottom">
    <p>&copy; {year} {brand}. All rights reserved. Entertainment only &mdash; 18+ only.</p>
    <div class="footer-bottom-links">
      <a href="terms.php">Terms</a>
      <a href="privacy.php">Privacy</a>
      <a href="cookie.php">Cookies</a>
    </div>
  </div>
</footer>"""

    def _footer_centered(self) -> str:
        """Centered stacked: large logo → tagline → horizontal nav row → legal."""
        ctx   = self.ctx
        brand = _h(ctx.brand_name)
        desc  = _h(ctx.footer_brand_description)
        legal = _h(ctx.footer_legal_notice)
        year  = ctx.current_year

        return f"""
<footer class="footer footer-centered" role="contentinfo">
  <div class="footer-centered-inner">

    <a class="footer-brand-logo" href="index.php" style="justify-content:center;margin-bottom:1rem;">
      <img src="assets/icons/logo.png" alt="{brand} logo" width="48" height="48">
      <span style="font-size:1.5rem;">{brand}</span>
    </a>

    <p style="color:var(--text-secondary);max-width:480px;margin:0 auto 2rem;text-align:center;line-height:1.7;">{desc}</p>

    <nav class="footer-center-nav" aria-label="Footer navigation">
      <a href="index.php">Home</a>
      <span aria-hidden="true">&middot;</span>
      <a href="index.php#games">Games</a>
      <span aria-hidden="true">&middot;</span>
      <a href="contact.php">Contact</a>
      <span aria-hidden="true">&middot;</span>
      <a href="terms.php">Terms</a>
      <span aria-hidden="true">&middot;</span>
      <a href="privacy.php">Privacy</a>
      <span aria-hidden="true">&middot;</span>
      <a href="cookie.php">Cookies</a>
    </nav>

    <p class="footer-legal-notice" style="margin-top:2rem;color:var(--text-muted);font-size:0.85rem;text-align:center;max-width:560px;margin-left:auto;margin-right:auto;">{legal}</p>

    <p style="margin-top:1.5rem;color:var(--text-muted);font-size:0.82rem;text-align:center;">&copy; {year} {brand}. All rights reserved.</p>

  </div>
</footer>"""

    def _footer_compact(self) -> str:
        """Dense 2-col: (brand + legal paragraph) + (all links in two rows)."""
        ctx   = self.ctx
        brand = _h(ctx.brand_name)
        desc  = _h(ctx.footer_brand_description)
        legal = _h(ctx.footer_legal_notice)
        g1    = _h(ctx.game1_name)
        g2    = _h(ctx.game2_name)
        year  = ctx.current_year

        return f"""
<footer class="footer footer-compact" role="contentinfo">
  <div class="footer-compact-grid">

    <div class="footer-compact-left">
      <a class="footer-brand-logo" href="index.php" style="margin-bottom:0.75rem;">
        <img src="assets/icons/logo.png" alt="{brand} logo" width="30" height="30">
        <span style="font-size:1.1rem;">{brand}</span>
      </a>
      <p style="color:var(--text-secondary);font-size:0.90rem;line-height:1.65;margin-bottom:1rem;">{desc}</p>
      <p style="color:var(--text-muted);font-size:0.82rem;line-height:1.6;">{legal}</p>
      <p style="color:var(--text-muted);font-size:0.82rem;margin-top:0.75rem;">Features: {g1} &amp; {g2}.</p>
    </div>

    <div class="footer-compact-right">
      <div class="footer-compact-links">
        <div>
          <p class="footer-col-title">Pages</p>
          <ul class="footer-links">
            <li><a href="index.php">Home</a></li>
            <li><a href="index.php#games">Gallery</a></li>
            <li><a href="contact.php">Contact</a></li>
          </ul>
        </div>
        <div>
          <p class="footer-col-title">Legal</p>
          <ul class="footer-links">
            <li><a href="terms.php">Terms</a></li>
            <li><a href="privacy.php">Privacy</a></li>
            <li><a href="cookie.php">Cookies</a></li>
          </ul>
        </div>
      </div>
    </div>

  </div>

  <div class="footer-bottom" style="margin-top:1.5rem;">
    <p>&copy; {year} {brand}. All rights reserved.</p>
    <div class="footer-bottom-links">
      <a href="terms.php">Terms</a>
      <a href="privacy.php">Privacy</a>
      <a href="cookie.php">Cookies</a>
    </div>
  </div>
</footer>"""

    # ══════════════════════════════════════════════════════════════════════════
    #  index.php  — delegates to layout helpers driven by ctx.variant
    # ══════════════════════════════════════════════════════════════════════════

    # ── Hero layout variants ───────────────────────────────────────────────

    def _hero_centered(self, badge: str, head1: str, head2: str, sub: str) -> str:
        return (
            f'  <section class="hero hero-centered" id="home" aria-label="Hero">\n'
            f'    <div class="hero-bg" role="img" aria-label="Hero background"></div>\n'
            f'    <div class="hero-content">\n'
            f'      <div class="hero-badge">{badge}</div>\n'
            f'      <h1>{head1} <span class="accent">{head2}</span></h1>\n'
            f'      <p>{sub}</p>\n'
            f'      <div class="cta-group">\n'
            f'        <a href="#games" class="btn btn-primary">Explore Games</a>\n'
            f'        <a href="contact.php" class="btn btn-outline">Contact Us</a>\n'
            f'      </div>\n'
            f'    </div>\n'
            f'  </section>'
        )

    def _hero_left(self, badge: str, head1: str, head2: str, sub: str) -> str:
        """Left-aligned headline, hero image shifts to atmospheric bg."""
        return (
            f'  <section class="hero hero-left" id="home" aria-label="Hero">\n'
            f'    <div class="hero-bg" role="img" aria-label="Hero background"></div>\n'
            f'    <div class="hero-content">\n'
            f'      <div class="hero-badge">{badge}</div>\n'
            f'      <h1>{head1}<br><span class="accent">{head2}</span></h1>\n'
            f'      <p>{sub}</p>\n'
            f'      <div class="cta-group">\n'
            f'        <a href="#games" class="btn btn-primary">Explore Games</a>\n'
            f'        <a href="contact.php" class="btn btn-outline">Contact Us</a>\n'
            f'      </div>\n'
            f'    </div>\n'
            f'  </section>'
        )

    def _hero_split(self, badge: str, head1: str, head2: str, sub: str) -> str:
        """Two-column: text left, game banner previews right."""
        ctx = self.ctx
        b1 = _ha(ctx.game1_banner)
        b2 = _ha(ctx.game2_banner)
        n1 = _ha(ctx.game1_name)
        n2 = _ha(ctx.game2_name)
        return (
            f'  <section class="hero hero-split" id="home" aria-label="Hero">\n'
            f'    <div class="hero-bg" role="img" aria-label="Hero background"></div>\n'
            f'    <div class="hero-split-wrap">\n'
            f'      <div class="hero-content">\n'
            f'        <div class="hero-badge">{badge}</div>\n'
            f'        <h1>{head1} <span class="accent">{head2}</span></h1>\n'
            f'        <p>{sub}</p>\n'
            f'        <div class="cta-group">\n'
            f'          <a href="#games" class="btn btn-primary">Explore Games</a>\n'
            f'          <a href="contact.php" class="btn btn-outline">Contact Us</a>\n'
            f'        </div>\n'
            f'      </div>\n'
            f'      <div class="hero-split-visual" aria-hidden="true">\n'
            f'        <div class="hero-preview-card">\n'
            f'          <img src="{b1}" alt="{n1}" loading="lazy">\n'
            f'        </div>\n'
            f'        <div class="hero-preview-card hero-preview-card-lower">\n'
            f'          <img src="{b2}" alt="{n2}" loading="lazy">\n'
            f'        </div>\n'
            f'      </div>\n'
            f'    </div>\n'
            f'  </section>'
        )

    # ── Game section layout variants ───────────────────────────────────────

    def _games_grid(self, gtitle: str, gdesc: str) -> str:
        """Equal two-column card grid."""
        ctx = self.ctx
        def card(folder, name, banner, desc, delay):
            return (
                f'          <article class="game-card fade-in fade-in-delay-{delay}">\n'
                f'            <div class="game-card-thumb">\n'
                f'              <img src="{_ha(banner)}" alt="{_ha(name)} banner" loading="lazy">\n'
                f'            </div>\n'
                f'            <div class="game-card-body">\n'
                f'              <h3 class="game-card-title">{_h(name)}</h3>\n'
                f'              <p class="game-card-desc">{_h(desc)}</p>\n'
                f'              <a href="game.php?game={_ha(folder)}" class="btn btn-primary">Play Now</a>\n'
                f'            </div>\n'
                f'          </article>'
            )
        cards = "\n".join([
            card(ctx.game1_folder, ctx.game1_name, ctx.game1_banner, ctx.game1_description, 1),
            card(ctx.game2_folder, ctx.game2_name, ctx.game2_banner, ctx.game2_description, 2),
        ])
        return (
            f'  <section class="section" id="games" aria-labelledby="gallery-heading">\n'
            f'    <div class="container">\n'
            f'      <div class="section-header fade-in">\n'
            f'        <h2 id="gallery-heading">{gtitle}</h2>\n'
            f'        <p>{gdesc}</p>\n'
            f'      </div>\n'
            f'      <div class="game-grid">\n'
            f'{cards}\n'
            f'      </div>\n'
            f'    </div>\n'
            f'  </section>'
        )

    def _games_featured(self, gtitle: str, gdesc: str) -> str:
        """First game large/featured (1.6fr), second smaller (1fr)."""
        ctx = self.ctx
        def card(folder, name, banner, desc, delay, extra_cls=""):
            cls = f"game-card {extra_cls} fade-in fade-in-delay-{delay}".strip()
            return (
                f'          <article class="{cls}">\n'
                f'            <div class="game-card-thumb">\n'
                f'              <img src="{_ha(banner)}" alt="{_ha(name)} banner" loading="lazy">\n'
                f'            </div>\n'
                f'            <div class="game-card-body">\n'
                f'              <h3 class="game-card-title">{_h(name)}</h3>\n'
                f'              <p class="game-card-desc">{_h(desc)}</p>\n'
                f'              <a href="game.php?game={_ha(folder)}" class="btn btn-primary">Play Now</a>\n'
                f'            </div>\n'
                f'          </article>'
            )
        cards = "\n".join([
            card(ctx.game1_folder, ctx.game1_name, ctx.game1_banner, ctx.game1_description, 1, "game-card-primary"),
            card(ctx.game2_folder, ctx.game2_name, ctx.game2_banner, ctx.game2_description, 2, "game-card-secondary"),
        ])
        return (
            f'  <section class="section" id="games" aria-labelledby="gallery-heading">\n'
            f'    <div class="container">\n'
            f'      <div class="section-header fade-in">\n'
            f'        <h2 id="gallery-heading">{gtitle}</h2>\n'
            f'        <p>{gdesc}</p>\n'
            f'      </div>\n'
            f'      <div class="game-grid game-grid-featured">\n'
            f'{cards}\n'
            f'      </div>\n'
            f'    </div>\n'
            f'  </section>'
        )

    def _games_list(self, gtitle: str, gdesc: str) -> str:
        """Horizontal list: thumbnail left, text right."""
        ctx = self.ctx
        def item(folder, name, banner, desc, delay):
            return (
                f'          <article class="game-list-item card fade-in fade-in-delay-{delay}">\n'
                f'            <div class="game-list-thumb">\n'
                f'              <img src="{_ha(banner)}" alt="{_ha(name)} banner" loading="lazy">\n'
                f'            </div>\n'
                f'            <div class="game-list-body">\n'
                f'              <h3 class="game-card-title">{_h(name)}</h3>\n'
                f'              <p class="game-card-desc">{_h(desc)}</p>\n'
                f'              <a href="game.php?game={_ha(folder)}" class="btn btn-primary btn-sm">Play Now</a>\n'
                f'            </div>\n'
                f'          </article>'
            )
        items = "\n".join([
            item(ctx.game1_folder, ctx.game1_name, ctx.game1_banner, ctx.game1_description, 1),
            item(ctx.game2_folder, ctx.game2_name, ctx.game2_banner, ctx.game2_description, 2),
        ])
        return (
            f'  <section class="section" id="games" aria-labelledby="gallery-heading">\n'
            f'    <div class="container">\n'
            f'      <div class="section-header fade-in">\n'
            f'        <h2 id="gallery-heading">{gtitle}</h2>\n'
            f'        <p>{gdesc}</p>\n'
            f'      </div>\n'
            f'      <div class="game-list">\n'
            f'{items}\n'
            f'      </div>\n'
            f'    </div>\n'
            f'  </section>'
        )

    # ── Feature section layout variants ───────────────────────────────────

    def _features_icons(self, why_title: str, why_desc: str) -> str:
        """3-col grid with icon images (original layout)."""
        ctx = self.ctx
        count = len(ctx.feature_cards)
        parts = []
        for i, fc in enumerate(ctx.feature_cards, 1):
            parts.append(
                f'          <div class="feature-card fade-in fade-in-delay-{i}">\n'
                f'            <div class="feature-icon">\n'
                f'              <img src="{_ha(fc.icon_path)}" alt="{_ha(fc.title)} icon" loading="lazy">\n'
                f'            </div>\n'
                f'            <h3>{_h(fc.title)}</h3>\n'
                f'            <p>{_h(fc.description)}</p>\n'
                f'          </div>'
            )
        return (
            f'  <section class="section section-alt" id="features" aria-labelledby="features-heading">\n'
            f'    <div class="container">\n'
            f'      <div class="section-header fade-in">\n'
            f'        <h2 id="features-heading">{why_title}</h2>\n'
            f'        <p>{why_desc}</p>\n'
            f'      </div>\n'
            f'      <div class="{_feature_grid_classes("features-grid", count=count)}">\n'
            + "\n".join(parts) + "\n"
            f'      </div>\n'
            f'    </div>\n'
            f'  </section>'
        )

    def _features_numbered(self, why_title: str, why_desc: str) -> str:
        """3-col grid with oversized accent numbers and icon images."""
        ctx = self.ctx
        count = len(ctx.feature_cards)
        parts = []
        for i, fc in enumerate(ctx.feature_cards, 1):
            parts.append(
                f'          <div class="feature-card fade-in fade-in-delay-{i}">\n'
                f'            <div class="feature-icon">\n'
                f'              <img src="{_ha(fc.icon_path)}" alt="{_ha(fc.title)} icon" loading="lazy">\n'
                f'            </div>\n'
                f'            <div class="feature-number">{i:02d}</div>\n'
                f'            <h3>{_h(fc.title)}</h3>\n'
                f'            <p>{_h(fc.description)}</p>\n'
                f'          </div>'
            )
        return (
            f'  <section class="section section-alt" id="features" aria-labelledby="features-heading">\n'
            f'    <div class="container">\n'
            f'      <div class="section-header fade-in">\n'
            f'        <h2 id="features-heading">{why_title}</h2>\n'
            f'        <p>{why_desc}</p>\n'
            f'      </div>\n'
            f'      <div class="{_feature_grid_classes("features-grid", "features-numbered", count=count)}">\n'
            + "\n".join(parts) + "\n"
            f'      </div>\n'
            f'    </div>\n'
            f'  </section>'
        )

    def _features_horizontal(self, why_title: str, why_desc: str) -> str:
        """2-col layout: icon on left, text on right."""
        ctx = self.ctx
        count = len(ctx.feature_cards)
        parts = []
        for i, fc in enumerate(ctx.feature_cards, 1):
            parts.append(
                f'          <div class="feature-horiz-card fade-in fade-in-delay-{i}">\n'
                f'            <div class="feature-icon">\n'
                f'              <img src="{_ha(fc.icon_path)}" alt="{_ha(fc.title)} icon" loading="lazy">\n'
                f'            </div>\n'
                f'            <div class="feature-horiz-body">\n'
                f'              <h3>{_h(fc.title)}</h3>\n'
                f'              <p>{_h(fc.description)}</p>\n'
                f'            </div>\n'
                f'          </div>'
            )
        return (
            f'  <section class="section section-alt" id="features" aria-labelledby="features-heading">\n'
            f'    <div class="container">\n'
            f'      <div class="section-header fade-in">\n'
            f'        <h2 id="features-heading">{why_title}</h2>\n'
            f'        <p>{why_desc}</p>\n'
            f'      </div>\n'
            f'      <div class="{_feature_grid_classes("features-grid", "features-horiz", count=count)}">\n'
            + "\n".join(parts) + "\n"
            f'      </div>\n'
            f'    </div>\n'
            f'  </section>'
        )

    # ── Optional home-page section builders ───────────────────────────

    def _section_stats(self) -> str:
        ctx = self.ctx
        title = _h(ctx.stats_title) or "Platform Stats"
        parts = []
        for i, item in enumerate(ctx.stats_items[:4], 1):
            parts.append(
                f'          <div class="stat-item fade-in fade-in-delay-{i}">\n'
                f'            <div class="stat-number">{_h(item.number)}</div>\n'
                f'            <div class="stat-label">{_h(item.label)}</div>\n'
                f'          </div>'
            )
        grid = "\n".join(parts)
        count = len(parts)
        return (
            f'  <section class="section stats-section" id="stats" aria-labelledby="stats-heading">\n'
            f'    <div class="container">\n'
            f'      <h2 class="section-header-centered fade-in" id="stats-heading">{title}</h2>\n'
            f'      <div class="{_count_grid_classes("stats", "stats-grid", count=count)}">\n'
            f'{grid}\n'
            f'      </div>\n'
            f'    </div>\n'
            f'  </section>'
        )

    def _section_testimonials(self) -> str:
        ctx = self.ctx
        title = _h(ctx.testimonials_title) or "What Players Say"
        parts = []
        for i, item in enumerate(ctx.testimonials_items[:3], 1):
            parts.append(
                f'          <div class="testimonial-card card fade-in fade-in-delay-{i}">\n'
                f'            <div class="testimonial-quote">\u201c{_h(item.quote)}\u201d</div>\n'
                f'            <div class="testimonial-author">\u2014 {_h(item.author)}</div>\n'
                f'          </div>'
            )
        cards = "\n".join(parts)
        return (
            f'  <section class="section section-alt testimonials-section" id="testimonials"'
            f' aria-labelledby="testimonials-heading">\n'
            f'    <div class="container">\n'
            f'      <div class="section-header fade-in">\n'
            f'        <h2 id="testimonials-heading">{title}</h2>\n'
            f'      </div>\n'
            f'      <div class="testimonials-grid">\n'
            f'{cards}\n'
            f'      </div>\n'
            f'    </div>\n'
            f'  </section>'
        )

    def _section_about(self) -> str:
        ctx = self.ctx
        title = _h(ctx.about_title) or "About Us"
        body  = _h(ctx.about_body)
        return (
            f'  <section class="section about-section" id="about" aria-labelledby="about-heading">\n'
            f'    <div class="container">\n'
            f'      <div class="about-inner fade-in">\n'
            f'        <h2 id="about-heading">{title}</h2>\n'
            f'        <p>{body}</p>\n'
            f'      </div>\n'
            f'    </div>\n'
            f'  </section>'
        )

    def _section_cta_banner(self) -> str:
        ctx = self.ctx
        headline = _h(ctx.cta_headline) or "Ready to Play?"
        subtext  = _h(ctx.cta_subtext)
        btn_text = _h(ctx.cta_button_text) or "Explore All Games"
        return (
            f'  <section class="cta-banner" id="cta" aria-label="Call to Action">\n'
            f'    <div class="container">\n'
            f'      <h2>{headline}</h2>\n'
            f'      <p>{subtext}</p>\n'
            f'      <a href="#games" class="btn btn-primary btn-lg">{btn_text}</a>\n'
            f'    </div>\n'
            f'  </section>'
        )

    # ── index.php assembler ────────────────────────────────────────────────

    def _index(self) -> str:
        ctx   = self.ctx
        v     = ctx.variant
        brand = _h(ctx.brand_name)
        badge = _h(ctx.hero_badge)
        head1 = _h(ctx.hero_headline_part1)
        head2 = _h(ctx.hero_headline_part2)
        sub   = _h(ctx.hero_subtext)
        gtitle = _h(ctx.gallery_title)
        gdesc  = _h(ctx.gallery_description)
        wtitle = _h(ctx.why_title)
        wdesc  = _h(ctx.why_description)

        hero_html = {
            "centered": self._hero_centered,
            "left":     self._hero_left,
            "split":    self._hero_split,
        }[v.hero_layout](badge, head1, head2, sub)

        game_html = self._gallery.render_section(
            section_layout = v.gallery_section_layout,
            item_layout    = v.gallery_item_layout,
            game1 = {
                "folder":      ctx.game1_folder,
                "name":        ctx.game1_name,
                "banner":      ctx.game1_banner,
                "description": ctx.game1_description,
            },
            game2 = {
                "folder":      ctx.game2_folder,
                "name":        ctx.game2_name,
                "banner":      ctx.game2_banner,
                "description": ctx.game2_description,
            },
            gtitle = gtitle,
            gdesc  = gdesc,
        )

        feat_html = {
            "icons":      self._features_icons,
            "numbered":   self._features_numbered,
            "horizontal": self._features_horizontal,
        }[v.feat_layout](wtitle, wdesc)

        # Assemble page sections in order; optional sections keyed by extra_sections
        extra = v.extra_sections
        sections = [hero_html]
        if "stats" in extra:
            sections.append(self._section_stats())
        sections.append(game_html)
        sections.append(feat_html)
        if "testimonials" in extra:
            sections.append(self._section_testimonials())
        if "about" in extra:
            sections.append(self._section_about())
        if "cta_banner" in extra:
            sections.append(self._section_cta_banner())

        body = "<main id=\"main-content\">\n\n" + "\n\n".join(sections) + "\n\n</main>"

        return self._page(
            active_page="home",
            title=f"{brand} - Free Entertainment Games",
            body=body,
        )

    # ══════════════════════════════════════════════════════════════════════════
    #  game.php
    # ══════════════════════════════════════════════════════════════════════════

    def _game(self) -> str:
        ctx = self.ctx
        brand = _php_str(ctx.brand_name)
        f1    = _php_str(ctx.game1_folder)
        f2    = _php_str(ctx.game2_folder)
        n1    = _php_str(ctx.game1_name)
        n2    = _php_str(ctx.game2_name)

        php_logic = (
            "<?php\n"
            f"$_brand       = '{brand}';\n"
            f"$_valid_games = ['{f1}' => '{n1}', '{f2}' => '{n2}'];\n\n"
            "// Sanitise the 'game' parameter: strip path separators and null bytes, then\n"
            "// rely on the exact-match whitelist below as the authoritative security gate.\n"
            "$_game_key = isset($_GET['game']) ? $_GET['game'] : '';\n"
            "$_game_key = str_replace([\"\\0\", \"\\r\", \"\\n\", '/', '\\\\', '..'], '', $_game_key);\n"
            "$_is_valid  = array_key_exists($_game_key, $_valid_games);\n"
            "$_game_name = $_is_valid ? $_valid_games[$_game_key] : '';\n\n"
            "// Build a root-relative path — game.php lives in the same directory as\n"
            "// the batch root, so games/ is always a sibling of this file.\n"
            "$_base_dir = rtrim(dirname($_SERVER['SCRIPT_NAME']), '/');\n"
            "$_game_src = $_is_valid\n"
            "    ? $_base_dir . '/games/' . $_game_key . '/index.php'\n"
            "    : '';\n\n"
            "$page_title  = $_is_valid ? $_game_name . ' - ' . $_brand : 'Game Not Found - ' . $_brand;\n"
            "$active_page = 'games';\n"
            "include 'partials/header.php';\n"
            "?>\n\n"
        )

        valid_body = (
            '<div class="game-page-wrap">\n\n'
            '  <div class="game-topbar">\n'
            '    <div class="game-topbar-title">\n'
            '      <a href="index.php#games" class="btn btn-outline btn-sm"\n'
            '         aria-label="Back to game gallery">&larr; Gallery</a>\n'
            '      <span><?php echo htmlspecialchars($_game_name); ?></span>\n'
            '    </div>\n'
            '    <a href="index.php" class="btn btn-outline btn-sm">Home</a>\n'
            '  </div>\n\n'
            '  <div class="game-iframe-wrap" style="height: calc(100vh - 130px);">\n'
            '    <iframe\n'
            '      class="game-iframe"\n'
            '      src="<?php echo htmlspecialchars($_game_src); ?>"\n'
            '      title="<?php echo htmlspecialchars($_game_name); ?>"\n'
            '      allowfullscreen\n'
            '      loading="lazy"\n'
            '      sandbox="allow-scripts allow-same-origin allow-forms allow-popups"\n'
            '    ></iframe>\n'
            '  </div>\n\n'
            '</div>\n'
        )

        error_body = (
            '<main>\n'
            '  <div class="game-error-page">\n'
            '    <div class="error-code">404</div>\n'
            '    <h2>Game Not Found</h2>\n'
            '    <p>The game you\'re looking for isn\'t available right now.<br>\n'
            '       Please check the URL or choose from our game gallery.</p>\n'
            '    <a href="index.php#games" class="btn btn-primary">Back to Game Gallery</a>\n'
            '  </div>\n'
            '</main>\n'
        )

        php_switch = (
            "<?php if ($_is_valid): ?>\n"
            + valid_body
            + "<?php else: ?>\n"
            + error_body
            + "<?php endif; ?>\n"
        )

        return php_logic + php_switch + "\n<?php include 'partials/footer.php'; ?>\n"

    # ══════════════════════════════════════════════════════════════════════════
    #  game_proxy.php — USD → FUN replacement
    # ══════════════════════════════════════════════════════════════════════════

    def _game_proxy(self) -> str:
        ctx = self.ctx
        f1 = _php_str(ctx.game1_folder)
        f2 = _php_str(ctx.game2_folder)

        return f"""<?php
/**
 * game_proxy.php
 *
 * Serves a game's index.php through PHP output buffering, replacing every
 * occurrence of "USD" with "FUN" to reinforce the entertainment-only nature
 * of the platform.
 *
 * The iframe in game.php points here rather than directly to the game file.
 */

$_valid = ['{f1}', '{f2}'];
$_key   = isset($_GET['game']) ? $_GET['game'] : '';
$_key   = str_replace(["\\0", "\\r", "\\n", '/', '\\\\', '..'], '', $_key);

if (!in_array($_key, $_valid, true)) {{
    http_response_code(404);
    exit('Game not found.');
}}

$_game_file = __DIR__ . '/games/' . $_key . '/index.php';

if (!is_file($_game_file)) {{
    http_response_code(404);
    exit('Game file missing.');
}}

// Capture the game output, replace currency references, then emit
ob_start();
include $_game_file;
$_output = ob_get_clean();

// USD → FUN (covers both plain USD and $-prefixed amounts like $1.00 USD)
$_output = str_replace('USD', 'FUN', $_output);
$_output = str_replace(' $', ' FUN ', $_output);

echo $_output;
"""

    # ══════════════════════════════════════════════════════════════════════════
    #  contact.php
    # ══════════════════════════════════════════════════════════════════════════

    def _contact(self) -> str:
        ctx = self.ctx
        brand = _h(ctx.brand_name)
        intro = _h(ctx.contact_intro)

        body = f"""<main id="main-content">
  <div class="page-hero">
    <div class="container">
      <h1>Contact Us</h1>
      <p>{intro}</p>
    </div>
  </div>

  <section class="section">
    <div class="container contact-wrap">
      <div class="form-card fade-in">

        <form id="contact-form" novalidate aria-label="Contact form">
          <div class="form-group">
            <label for="name">Your Name</label>
            <input
              class="form-control"
              type="text"
              id="name"
              name="name"
              placeholder="Enter your name"
              autocomplete="name"
              required
            >
            <p class="form-error-msg" id="name-err" role="alert">Please enter your name.</p>
          </div>

          <div class="form-group">
            <label for="email">Email Address</label>
            <input
              class="form-control"
              type="email"
              id="email"
              name="email"
              placeholder="your@email.com"
              autocomplete="email"
              required
            >
            <p class="form-error-msg" id="email-err" role="alert">Please enter a valid email address.</p>
          </div>

          <div class="form-group">
            <label for="message">Message</label>
            <textarea
              class="form-control"
              id="message"
              name="message"
              placeholder="How can we help you?"
              rows="6"
              required
            ></textarea>
            <p class="form-error-msg" id="message-err" role="alert">Please enter a message.</p>
          </div>

          <button type="submit" class="btn btn-primary" style="width:100%;">Send Message</button>
        </form>

        <!-- Shown after simulated submit -->
        <div class="form-success" id="form-success" role="status" aria-live="polite">
          <div class="success-icon">&#10003;</div>
          <h3>Message Sent!</h3>
          <p>Thanks for reaching out. We&rsquo;ll get back to you as soon as possible.</p>
        </div>

      </div>
    </div>
  </section>
</main>"""

        return self._page(
            active_page="contact",
            title=f"Contact - {brand}",
            body=body,
        )

    # ══════════════════════════════════════════════════════════════════════════
    #  terms.php
    # ══════════════════════════════════════════════════════════════════════════

    def _terms(self) -> str:
        ctx = self.ctx
        brand = _h(ctx.brand_name)

        sections_html = _render_legal_sections(ctx.terms_sections)
        toc_html      = _render_toc(ctx.terms_sections)

        body = f"""<main id="main-content">
  <div class="page-hero">
    <div class="container">
      <h1>Terms of Use</h1>
      <p>Please read these terms carefully before using {brand}.</p>
    </div>
  </div>

  <section class="section">
    <div class="container legal-wrap">

      <!-- Table of contents -->
      <nav class="legal-toc fade-in" aria-label="Terms sections">
        <h3>On This Page</h3>
        <ul>
          {toc_html}
        </ul>
      </nav>

      <!-- Sections -->
{sections_html}

    </div>
  </section>
</main>"""

        return self._page(
            active_page="terms",
            title=f"Terms of Use - {brand}",
            body=body,
        )

    # ══════════════════════════════════════════════════════════════════════════
    #  privacy.php
    # ══════════════════════════════════════════════════════════════════════════

    def _privacy(self) -> str:
        ctx = self.ctx
        brand = _h(ctx.brand_name)

        sections_html = _render_legal_sections(ctx.privacy_sections)
        toc_html      = _render_toc(ctx.privacy_sections)

        body = f"""<main id="main-content">
  <div class="page-hero">
    <div class="container">
      <h1>Privacy Policy</h1>
      <p>Your privacy matters to us. Here&rsquo;s exactly what we collect and why.</p>
    </div>
  </div>

  <section class="section">
    <div class="container legal-wrap">

      <nav class="legal-toc fade-in" aria-label="Privacy sections">
        <h3>On This Page</h3>
        <ul>
          {toc_html}
        </ul>
      </nav>

{sections_html}

    </div>
  </section>
</main>"""

        return self._page(
            active_page="privacy",
            title=f"Privacy Policy - {brand}",
            body=body,
        )

    # ══════════════════════════════════════════════════════════════════════════
    #  cookie.php
    # ══════════════════════════════════════════════════════════════════════════

    def _cookie(self) -> str:
        ctx = self.ctx
        brand = _h(ctx.brand_name)
        intro = _h(ctx.cookie_intro)

        cookie_sections = [
            ContentSection(
                heading="What Are Cookies?",
                body=(
                    "Cookies are small text files that a website stores on your device "
                    "when you visit. They help the site function correctly and remember "
                    "your preferences between visits."
                ),
            ),
            ContentSection(
                heading="Cookies We Use",
                body=(
                    "We only use essential session cookies required for the site to "
                    "operate. These cookies do not collect personal data, cannot track "
                    "you across other websites, and expire when you close your browser."
                ),
            ),
            ContentSection(
                heading="What We Do Not Use",
                body=(
                    "We do not use advertising cookies, third-party tracking cookies, "
                    "analytics cookies, or any other cookies that identify you personally "
                    "or follow your activity across the web."
                ),
            ),
            ContentSection(
                heading="Your Choices",
                body=(
                    "You can accept or decline non-essential cookies at any time using "
                    "the cookie notice at the bottom of the screen. You may also manage "
                    "or delete cookies via your browser settings at any time."
                ),
            ),
        ]

        sections_html = _render_legal_sections(cookie_sections)

        body = f"""<main id="main-content">
  <div class="page-hero">
    <div class="container">
      <h1>Cookie Policy</h1>
      <p>{intro}</p>
    </div>
  </div>

  <section class="section">
    <div class="container legal-wrap">

      <div class="legal-section fade-in"
           style="border-left: 3px solid var(--accent); margin-bottom: 2rem;">
        <h2>Summary</h2>
        <p>{intro}</p>
        <p><strong>{brand}</strong> uses only essential cookies.
           We have no advertising partners and do not sell your data.</p>
      </div>

{sections_html}

    </div>
  </section>
</main>"""

        return self._page(
            active_page="",
            title=f"Cookie Policy - {brand}",
            body=body,
        )


# ═══════════════════════════════════════════════════════════════════════════════
#  SiteContext factory
# ═══════════════════════════════════════════════════════════════════════════════

def build_context(
    *,
    batch_name:   str,
    brand_name:   str,
    topic:        str,
    tone:         str,
    current_year: int,
    game1_folder: str,
    game1_name:   str,
    game1_banner: str,
    game2_folder: str,
    game2_name:   str,
    game2_banner: str,
    icon_paths:   list[str],
    ai_content:   dict[str, Any],
    variant:      SiteVariant | None = None,
) -> SiteContext:
    """
    Assemble a ``SiteContext`` from AI-generated content and game metadata.

    *ai_content* is the dict returned by ``ai_text.generate_site_content()``.
    *icon_paths* is a list of relative web paths for feature card icons.
    """
    raw_cards    = ai_content.get("feature_cards", [])
    feature_cards = [
        FeatureCard(
            icon_path   = icon_paths[i] if i < len(icon_paths) else "assets/icons/icon_1.png",
            title       = fc.get("title", f"Feature {i+1}"),
            description = fc.get("description", ""),
        )
        for i, fc in enumerate(raw_cards)
    ]

    def _sec(raw: list[dict[str, str]]) -> list[ContentSection]:
        return [ContentSection(heading=s.get("heading", ""), body=s.get("body", "")) for s in raw]

    def _stats(raw: dict) -> list[StatItem]:
        return [
            StatItem(number=it.get("number", ""), label=it.get("label", ""))
            for it in raw.get("items", [])[:4]
        ]

    def _testimonials(raw: dict) -> list[TestimonialItem]:
        return [
            TestimonialItem(quote=it.get("quote", ""), author=it.get("author", ""))
            for it in raw.get("items", [])[:3]
        ]

    raw_stats          = ai_content.get("stats", {})
    raw_testimonials   = ai_content.get("testimonials", {})
    raw_about          = ai_content.get("about", {})
    raw_cta            = ai_content.get("cta_banner", {})

    return SiteContext(
        batch_name            = batch_name,
        brand_name            = ai_content.get("brand_name", brand_name),
        topic                 = topic,
        tone                  = tone,
        current_year          = current_year,
        variant               = variant if variant is not None else pick_variant(batch_name),
        game1_folder          = game1_folder,
        game1_name            = game1_name,
        game1_banner          = game1_banner,
        game1_description     = ai_content.get("game1_description", ""),
        game2_folder          = game2_folder,
        game2_name            = game2_name,
        game2_banner          = game2_banner,
        game2_description     = ai_content.get("game2_description", ""),
        meta_description      = ai_content.get("meta_description", ""),
        hero_badge            = ai_content.get("hero_badge", "PLAY FOR FREE"),
        hero_headline_part1   = ai_content.get("hero_headline_part1", "Your Next"),
        hero_headline_part2   = ai_content.get("hero_headline_part2", "Adventure Awaits"),
        hero_subtext          = ai_content.get("hero_subtext", ""),
        gallery_title         = ai_content.get("gallery_title", "Game Gallery"),
        gallery_description   = ai_content.get("gallery_description", ""),
        why_title             = ai_content.get("why_title", "Why Choose Us"),
        why_description       = ai_content.get("why_description", ""),
        feature_cards         = feature_cards,
        contact_intro         = ai_content.get("contact_intro", ""),
        terms_sections        = _sec(ai_content.get("terms_sections", [])),
        privacy_sections      = _sec(ai_content.get("privacy_sections", [])),
        cookie_intro          = ai_content.get("cookie_intro", ""),
        footer_brand_description = ai_content.get("footer_brand_description", ""),
        footer_legal_notice      = ai_content.get("footer_legal_notice", ""),
        stats_title              = raw_stats.get("title", ""),
        stats_items              = _stats(raw_stats),
        testimonials_title       = raw_testimonials.get("title", ""),
        testimonials_items       = _testimonials(raw_testimonials),
        about_title              = raw_about.get("title", ""),
        about_body               = raw_about.get("body", ""),
        cta_headline             = raw_cta.get("headline", ""),
        cta_subtext              = raw_cta.get("subtext", ""),
        cta_button_text          = raw_cta.get("button_text", "Explore All Games"),
    )
