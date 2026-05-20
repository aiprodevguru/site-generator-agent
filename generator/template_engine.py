"""
Generates styles.css, script.js, and the SVG logo for the whitepage.

Uses [[PLACEHOLDER]] substitution (not Python f-strings) so that CSS/JS
curly-brace syntax never conflicts with Python string formatting.
"""
from __future__ import annotations

from generator.variant         import SiteVariant
from generator.gallery.css     import GALLERY_CSS

# ═══════════════════════════════════════════════════════════════════════════════
#  CSS
# ═══════════════════════════════════════════════════════════════════════════════

_CSS_TEMPLATE = """
/* ====================================================================
   styles.css — Whitepage Generator
   Dark theme • Responsive • CSS custom properties
   ==================================================================== */

/* ── Google Fonts (injected per-batch from font_set) ──────────────── */
[[FONT_IMPORTS]]

/* ── Variables ──────────────────────────────────────────────────────── */
:root {
  --bg-primary:      #0a0a1a;
  --bg-secondary:    #12122a;
  --accent:          #6c63ff;
  --accent-hover:    #8b84ff;
  --accent-glow:     rgba(108, 99, 255, 0.35);
  --danger:          #ff6b6b;
  --success:         #4fc878;

  /* ── Text colour scale ─────────────────────────────────────────────
     --text          #f0effe  headings, labels, primary UI — near-white
     --text-secondary #c4c2e0  body copy inside cards, descriptions — very readable
     --text-muted     #9a98be  footnotes, placeholders, copyright — clearly dimmer
     All three clear WCAG AA (4.5:1) on the dark backgrounds used.
  ────────────────────────────────────────────────────────────────── */
  --text:            #f0effe;
  --text-secondary:  #c4c2e0;
  --text-muted:      #9a98be;

  --card-bg:         rgba(20, 20, 48, 0.97);
  --card-border:     rgba(108, 99, 255, 0.22);
  --nav-bg:          rgba(10, 10, 26, 0.96);
  --radius:          12px;
  --radius-sm:       8px;
  --radius-lg:       20px;
  --shadow-sm:       0 2px 12px rgba(0, 0, 0, 0.4);
  --shadow:          0 6px 30px rgba(0, 0, 0, 0.55);
  --shadow-lg:       0 16px 60px rgba(0, 0, 0, 0.65);
  --transition:      0.28s ease;
}

/* ── Reset ──────────────────────────────────────────────────────────── */
*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html {
  scroll-behavior: smooth;
}

body {
  background-color: var(--bg-primary);
  background-image: url('assets/images/background.jpg');
  background-attachment: fixed;
  background-size: cover;
  background-position: center;
  color: var(--text);
  font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-size: 16px;
  line-height: 1.65;
  min-height: 100vh;
  overflow-x: hidden;
}

img { display: block; max-width: 100%; }
a { text-decoration: none; color: inherit; }
ul { list-style: none; }

/* ── Page wrapper ───────────────────────────────────────────────────── */
/*
   The card that contains every page: header, content, and footer.
   The background image on <body> bleeds through around the edges.

   overflow: clip  (NOT overflow: hidden)
     Clips children visually to the border-radius, but does NOT create
     a new scroll container — so position:sticky on the navbar still works.
*/
.page-wrapper {
  max-width: 1400px;
  margin: 2.5rem auto;
  min-height: calc(100vh - 5rem);
  background: rgba(8, 8, 20, 0.90);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  border: 1px solid color-mix(in srgb, var(--accent) 38%, transparent);
  border-radius: 20px;
  overflow: clip;          /* clips children to border-radius, sticky still works */
  position: relative;

  /* ── Shadow stack ────────────────────────────────────────────────────
     Layer 1: tight drop shadow for crisp lift
     Layer 2: mid-range depth
     Layer 3: wide ambient darkness
     Layer 4: outer accent glow (the "breathing" purple halo)
     Layer 5: inset rim light (subtle top-left highlight)
  ─────────────────────────────────────────────────────────────────── */
  box-shadow:
    0 2px 6px  rgba(0, 0, 0, 0.60),
    0 12px 32px rgba(0, 0, 0, 0.55),
    0 40px 100px rgba(0, 0, 0, 0.48),
    0 0  120px color-mix(in srgb, var(--accent) 14%, transparent),
    inset 0 1px 0 rgba(255, 255, 255, 0.05),
    inset 0 0 0 1px color-mix(in srgb, var(--accent) 14%, transparent);
}

/* ── Typography ─────────────────────────────────────────────────────── */
h1, h2, h3, h4 {
  font-family: 'Space Grotesk', 'Inter', system-ui, sans-serif;
  font-weight: 700;
  line-height: 1.25;
  letter-spacing: -0.02em;
}

/* ── Navbar ─────────────────────────────────────────────────────────── */
/*
   Starts fully transparent so the hero image bleeds through.
   JS adds .scrolled at 60px; background, border, and shadow fade in (0.50s).
   backdrop-filter is NOT transitioned — it simply switches on with .scrolled.
*/
.navbar {
  position: sticky;
  top: 0;
  z-index: 200;
  height: 92px;          /* tall initial state — shrinks to 64px on scroll */
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 2.5rem;
  background: transparent;
  border-bottom: 1px solid transparent;
  box-shadow: none;
  gap: 1.5rem;
  transition:
    height       0.38s cubic-bezier(0.4, 0, 0.2, 1),
    background   0.50s ease,
    border-color 0.50s ease,
    box-shadow   0.50s ease;
}

/* ── Scrolled: glass panel materialises ────────────────────────────── */
.navbar.scrolled {
  height: 64px;
  background: linear-gradient(
    180deg,
    rgba(10, 10, 26, 0.97) 0%,
    rgba(8,  8,  20, 0.96) 100%
  );
  backdrop-filter: blur(18px) saturate(160%);
  -webkit-backdrop-filter: blur(18px) saturate(160%);
  border-bottom-color: color-mix(in srgb, var(--accent) 34%, transparent);
  box-shadow:
    0 1px 0  color-mix(in srgb, var(--accent) 30%, transparent),
    0 6px 32px rgba(0, 0, 0, 0.65);
}

/* Accent line — visible from page-load, softens once the panel is solid */
.navbar::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 2px;
  background: linear-gradient(
    90deg,
    transparent 0%,
    var(--accent) 30%,
    var(--accent-hover) 70%,
    transparent 100%
  );
  opacity: 0.90;
  transition: opacity 0.50s ease;
}

.navbar.scrolled::before { opacity: 0.42; }

.navbar-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  font-family: 'Space Grotesk', 'Inter', sans-serif;
  font-size: 1.42rem;    /* slightly larger in tall state */
  font-weight: 800;
  letter-spacing: -0.03em;
  color: var(--text);
  flex-shrink: 0;
  margin-right: auto;
  transition: font-size 0.38s cubic-bezier(0.4, 0, 0.2, 1),
              opacity   0.28s ease;
}

.navbar.scrolled .navbar-brand { font-size: 1.2rem; }

.navbar-brand:hover { opacity: 0.88; }

.navbar-brand img {
  width: 48px;           /* larger in tall state */
  height: 48px;
  border-radius: 12px;
  object-fit: cover;
  /* Soft glow ring around logo */
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--accent) 46%, transparent),
              0 0 18px color-mix(in srgb, var(--accent) 30%, transparent);
  transition: width        0.38s cubic-bezier(0.4, 0, 0.2, 1),
              height       0.38s cubic-bezier(0.4, 0, 0.2, 1),
              border-radius 0.38s ease,
              box-shadow   0.38s ease;
}

.navbar.scrolled .navbar-brand img {
  width: 34px;
  height: 34px;
  border-radius: 8px;
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--accent) 36%, transparent),
              0 0 10px color-mix(in srgb, var(--accent) 18%, transparent);
}

/* Brand name gradient */
.navbar-brand span {
  background: linear-gradient(135deg, #f0effe 0%, var(--accent-hover) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.nav-menu {
  display: flex;
  gap: 2rem;
  align-items: center;
}

.nav-cta {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 40px;
  padding: 0.7rem 1.1rem;
  border-radius: 999px;
  font-size: 0.86rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  border: 1px solid transparent;
  transition: transform var(--transition), box-shadow var(--transition),
              background var(--transition), color var(--transition),
              border-color var(--transition), opacity var(--transition);
}

.nav-cta:hover {
  transform: translateY(-1px);
}

.nav-cta-filled {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
}

.nav-cta-outlined,
.nav-cta-ghost-glow {
  background: transparent;
  color: var(--text);
  border-color: var(--card-border);
}

.nav-cta-gradient {
  background: linear-gradient(135deg, var(--grad-a), var(--grad-b));
  color: #fff;
  border-color: transparent;
}

.nav-cta-ghost-glow:hover {
  box-shadow: 0 0 24px var(--accent-glow);
  border-color: var(--accent);
}

.nav-menu a {
  color: var(--text-secondary);
  font-size: 0.96rem;
  font-weight: 500;
  transition: color var(--transition);
  position: relative;
  padding-bottom: 3px;
}

.nav-menu a::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 0;
  height: 2px;
  background: var(--accent);
  border-radius: 2px;
  transition: width var(--transition);
}

.nav-menu a:hover,
.nav-menu a.active {
  color: var(--text);
}

.nav-menu a:hover::after,
.nav-menu a.active::after {
  width: 100%;
}

/* Hamburger */
.hamburger {
  display: none;
  flex-direction: column;
  gap: 5px;
  cursor: pointer;
  background: none;
  border: none;
  padding: 5px;
  border-radius: 6px;
  transition: background var(--transition);
}

.hamburger:hover {
  background: rgba(255,255,255,0.07);
}

.hamburger span {
  display: block;
  width: 22px;
  height: 2px;
  background: var(--text);
  border-radius: 2px;
  transition: var(--transition);
}

.hamburger.active span:nth-child(1) { transform: translateY(7px) rotate(45deg); }
.hamburger.active span:nth-child(2) { opacity: 0; }
.hamburger.active span:nth-child(3) { transform: translateY(-7px) rotate(-45deg); }

/* ── Layout helpers ─────────────────────────────────────────────────── */
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1.5rem;
}

.section {
  padding: 6rem 1.5rem;
}

.section-alt {
  background: color-mix(in srgb, var(--accent) 7%, transparent);
}

.section-header {
  text-align: center;
  margin-bottom: 3.5rem;
}

.section-header h2 {
  font-size: clamp(1.75rem, 3.5vw, 2.4rem);
  margin-bottom: 0.85rem;
}

.section-header p {
  color: var(--text-secondary);
  max-width: 560px;
  margin: 0 auto;
  font-size: 1.1rem;
}

/* ── Page hero (inner pages) ────────────────────────────────────────── */
.page-hero {
  padding: 5.5rem 1.5rem 3.5rem;
  text-align: center;
  background: linear-gradient(180deg, color-mix(in srgb, var(--accent) 11%, transparent) 0%, transparent 100%);
  border-bottom: 1px solid var(--card-border);
}

.page-hero h1 {
  font-size: clamp(1.7rem, 4vw, 2.6rem);
  margin-bottom: 0.85rem;
}

.page-hero p {
  color: var(--text-secondary);
  max-width: 560px;
  margin: 0 auto;
  font-size: 1.1rem;
}

/* ── Buttons ────────────────────────────────────────────────────────── */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 13px 26px;
  border-radius: var(--radius);
  font-size: 0.97rem;
  font-weight: 600;
  font-family: inherit;
  cursor: pointer;
  transition: transform var(--transition), box-shadow var(--transition),
              background var(--transition), border-color var(--transition),
              color var(--transition);
  border: 1px solid transparent;
  line-height: 1;
  white-space: nowrap;
}

.btn:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 3px;
}

.btn-primary {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
}

.btn-primary:hover {
  background: var(--accent-hover);
  border-color: var(--accent-hover);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px var(--accent-glow);
}

.btn-outline {
  background: transparent;
  color: var(--text);
  border-color: var(--card-border);
}

.btn-outline:hover {
  border-color: var(--accent);
  color: var(--accent);
  transform: translateY(-2px);
}

.btn-sm {
  padding: 9px 18px;
  font-size: 0.875rem;
}

/* ── Hero section ───────────────────────────────────────────────────── */
.hero {
  position: relative;
  min-height: 90vh;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 5rem 1.5rem;
  overflow: hidden;
}

.hero-bg {
  position: absolute;
  inset: 0;
  background-image: url('assets/images/hero.jpg');
  background-size: cover;
  background-position: center 30%;
  filter: brightness(0.38);
  z-index: 0;
}

.hero-bg::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(
    to bottom,
    rgba(10,10,26,0.15) 0%,
    rgba(10,10,26,0.65) 100%
  );
}

.hero-content {
  position: relative;
  z-index: 1;
  max-width: 820px;
}

.hero-badge {
  display: inline-block;
  padding: 5px 18px;
  border: 1px solid var(--accent);
  border-radius: 100px;
  color: var(--accent);
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 2px;
  text-transform: uppercase;
  margin-bottom: 1.6rem;
}

.hero h1 {
  font-size: clamp(2.2rem, 6vw, 3.8rem);
  line-height: 1.15;
  margin-bottom: 1.5rem;
  color: #fff;
}

.hero h1 .accent {
  color: var(--accent);
}

.hero p {
  font-size: clamp(1rem, 2vw, 1.2rem);
  color: rgba(255,255,255,0.78);
  margin-bottom: 2.5rem;
  max-width: 620px;
  margin-left: auto;
  margin-right: auto;
}

.cta-group {
  display: flex;
  gap: 1rem;
  justify-content: center;
  flex-wrap: wrap;
}

/* ── Cards (base) ───────────────────────────────────────────────────── */
.card {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: var(--radius);
  padding: 2rem;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  transition: border-color var(--transition), transform var(--transition),
              box-shadow var(--transition);
}

.card:hover {
  border-color: var(--accent);
  transform: translateY(-4px);
  box-shadow: var(--shadow);
}

/* ── Game gallery ───────────────────────────────────────────────────── */
.game-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 2rem;
}

.game-card {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  transition: border-color var(--transition), transform var(--transition),
              box-shadow var(--transition);
}

.game-card:hover {
  border-color: var(--accent);
  transform: translateY(-6px);
  box-shadow: var(--shadow-lg);
}

.game-card-thumb {
  position: relative;
  overflow: hidden;
  height: 220px;
}

.game-card-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.45s ease;
}

.game-card:hover .game-card-thumb img {
  transform: scale(1.06);
}

.game-card-body {
  padding: 1.6rem 1.8rem 1.8rem;
}

.game-card-title {
  font-size: 1.3rem;
  font-weight: 700;
  margin-bottom: 0.65rem;
  color: var(--text);
}

.game-card-desc {
  color: var(--text-secondary);
  font-size: 1rem;
  margin-bottom: 1.5rem;
  line-height: 1.65;
}

/* ── Features grid ──────────────────────────────────────────────────── */
.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
}

.features-grid.features-count-3 {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.features-grid.features-count-4 {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.features-grid.features-count-6 {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.feature-card {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: var(--radius);
  padding: 2rem 1.75rem;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  text-align: center;
  transition: border-color var(--transition), transform var(--transition),
              box-shadow var(--transition);
}

.feature-card:hover {
  border-color: var(--accent);
  transform: translateY(-4px);
  box-shadow: var(--shadow);
}

.feature-icon {
  width: 72px;
  height: 72px;
  border-radius: 16px;
  overflow: hidden;
  margin: 0 auto 1.4rem;
  border: 1px solid var(--card-border);
}

.feature-icon img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.feature-card h3 {
  font-size: 1.1rem;
  margin-bottom: 0.6rem;
  color: var(--text);
}

.feature-card p {
  color: var(--text-secondary);
  font-size: 0.97rem;
  line-height: 1.65;
}

/* ── Game page ──────────────────────────────────────────────────────── */
.game-page-wrap {
  display: flex;
  flex-direction: column;
  min-height: calc(100vh - 68px);
}

.game-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.85rem 2rem;
  background: var(--card-bg);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--card-border);
  gap: 1rem;
  flex-shrink: 0;
}

.game-topbar-title {
  font-size: 1rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.game-iframe-wrap {
  flex: 1;
  position: relative;
}

.game-iframe {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  border: none;
  display: block;
}

.game-error-page {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  text-align: center;
  padding: 4rem 1.5rem;
}

.game-error-page .error-code {
  font-size: 5rem;
  font-weight: 800;
  color: var(--accent);
  line-height: 1;
  margin-bottom: 1.25rem;
}

.game-error-page h2 {
  font-size: 1.6rem;
  margin-bottom: 0.85rem;
}

.game-error-page p {
  color: var(--text-secondary);
  font-size: 1.05rem;
  margin-bottom: 2rem;
  max-width: 420px;
}

/* ── Contact form ───────────────────────────────────────────────────── */
.contact-wrap {
  max-width: 680px;
  margin: 0 auto;
}

.form-card {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: var(--radius-lg);
  padding: 2.5rem;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

.form-group {
  margin-bottom: 1.4rem;
}

.form-group label {
  display: block;
  font-size: 0.92rem;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 0.5rem;
  letter-spacing: 0.02em;
  text-transform: uppercase;
}

.form-control {
  width: 100%;
  background: rgba(255,255,255,0.04);
  border: 1px solid var(--card-border);
  border-radius: var(--radius-sm);
  padding: 12px 16px;
  color: var(--text);
  font-size: 0.97rem;
  font-family: inherit;
  transition: border-color var(--transition), background var(--transition),
              box-shadow var(--transition);
  resize: none;
}

.form-control::placeholder { color: var(--text-muted); opacity: 1; }

.form-control:focus {
  outline: none;
  border-color: var(--accent);
  background: color-mix(in srgb, var(--accent) 7%, transparent);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 18%, transparent);
}

.form-control.is-invalid {
  border-color: var(--danger);
  box-shadow: 0 0 0 3px rgba(255,107,107,0.15);
}

.form-error-msg {
  display: none;
  color: var(--danger);
  font-size: 0.8rem;
  margin-top: 0.4rem;
}

.form-error-msg.visible { display: block; }

textarea.form-control { min-height: 140px; }

.form-success {
  display: none;
  background: rgba(79,200,120,0.1);
  border: 1px solid rgba(79,200,120,0.3);
  border-radius: var(--radius);
  padding: 2rem;
  text-align: center;
}

.form-success.visible { display: block; }
.form-success .success-icon { font-size: 2.5rem; margin-bottom: 1rem; }
.form-success h3 { font-size: 1.2rem; margin-bottom: 0.5rem; color: var(--success); }
.form-success p { color: var(--text-secondary); font-size: 0.97rem; }

/* ── Legal pages ────────────────────────────────────────────────────── */
.legal-wrap {
  max-width: 860px;
  margin: 0 auto;
}

.legal-toc {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: var(--radius);
  padding: 1.5rem 2rem;
  backdrop-filter: blur(12px);
  margin-bottom: 2.5rem;
}

.legal-toc h3 {
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  color: var(--accent);
  margin-bottom: 0.85rem;
}

.legal-toc ul {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem 1.5rem;
}

.legal-toc a {
  color: var(--text-secondary);
  font-size: 0.95rem;
  transition: color var(--transition);
}

.legal-toc a:hover { color: var(--accent); }

.legal-section {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: var(--radius);
  padding: 2rem 2.2rem;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  margin-bottom: 1.5rem;
  scroll-margin-top: 90px;
}

.legal-section h2 {
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--accent);
  padding-bottom: 0.85rem;
  margin-bottom: 1.1rem;
  border-bottom: 1px solid var(--card-border);
  display: flex;
  align-items: center;
  gap: 0.65rem;
}

.legal-section p {
  color: var(--text-secondary);
  line-height: 1.85;
  font-size: 1rem;
  margin-bottom: 0.75rem;
}

.legal-section p:last-child { margin-bottom: 0; }

.legal-section ul {
  padding-left: 0.5rem;
}

.legal-section ul li {
  color: var(--text-secondary);
  font-size: 1rem;
  padding: 0.4rem 0;
  padding-left: 1.4rem;
  position: relative;
  line-height: 1.75;
}

.legal-section ul li::before {
  content: '›';
  position: absolute;
  left: 0;
  color: var(--accent);
  font-weight: 700;
}

/* ── Footer ─────────────────────────────────────────────────────────── */
.footer {
  /* overflow:clip on .page-wrapper clips this to the 20px bottom corners */
  background: rgba(6, 6, 16, 0.98);
  border-top: 1px solid rgba(108, 99, 255, 0.20);
  padding: 4.5rem 2rem 2rem;
  /* Subtle top shadow so footer has visual weight against content */
  box-shadow: 0 -8px 40px rgba(0, 0, 0, 0.35),
              inset 0 1px 0 rgba(108, 99, 255, 0.12);
}

.footer-grid {
  display: grid;
  grid-template-columns: 2.2fr 1fr 1fr;
  gap: 3.5rem;
  max-width: 1200px;
  margin: 0 auto 3rem;
}

.footer-brand-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 1.15rem;
  font-weight: 800;
  margin-bottom: 1rem;
}

.footer-brand-logo img {
  width: 34px;
  height: 34px;
  border-radius: 8px;
  object-fit: cover;
  box-shadow: 0 0 0 1px rgba(108, 99, 255, 0.35);
}

.footer-brand p {
  color: var(--text-secondary);
  font-size: 0.97rem;
  line-height: 1.75;
}

.footer-col-title {
  font-size: 0.82rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1.8px;
  color: var(--accent);
  margin-bottom: 1.25rem;
}

.footer-links li {
  margin-bottom: 0.6rem;
}

.footer-links a {
  color: var(--text-secondary);
  font-size: 0.95rem;
  transition: color var(--transition);
}

.footer-links a:hover { color: var(--accent); }

.footer-legal-note p {
  color: var(--text-secondary);
  font-size: 0.92rem;
  line-height: 1.75;
  margin-bottom: 0.5rem;
}

.footer-bottom {
  max-width: 1200px;
  margin: 0 auto;
  padding-top: 1.75rem;
  border-top: 1px solid var(--card-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.footer-bottom p {
  color: var(--text-muted);
  font-size: 0.87rem;
}

.footer-bottom-links {
  display: flex;
  gap: 1.5rem;
}

.footer-bottom-links a {
  color: var(--text-muted);
  font-size: 0.87rem;
  transition: color var(--transition);
}

.footer-bottom-links a:hover { color: var(--accent); }

/* ── Footer layout variants ─────────────────────────────────────────── */

/* Wide footer: 4-col grid */
.footer-grid-4 {
  grid-template-columns: 2fr 1fr 1fr 1fr;
  gap: 2.5rem;
}
@media (max-width: 900px) {
  .footer-grid-4 { grid-template-columns: 1fr 1fr; }
}
@media (max-width: 540px) {
  .footer-grid-4 { grid-template-columns: 1fr; }
}

/* Centered footer: single column */
.footer-centered-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  max-width: 700px;
  margin: 0 auto;
}
.footer-center-nav {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.5rem 1.25rem;
  align-items: center;
}
.footer-center-nav a {
  color: var(--text-secondary);
  font-size: 0.95rem;
  transition: color var(--transition);
}
.footer-center-nav a:hover { color: var(--accent); }
.footer-center-nav span { color: var(--text-muted); user-select: none; }

/* Compact footer: 2-col split */
.footer-compact-grid {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 2.5rem;
  max-width: 1200px;
  margin: 0 auto;
}
.footer-compact-links {
  display: flex;
  gap: 2.5rem;
}
@media (max-width: 640px) {
  .footer-compact-grid { grid-template-columns: 1fr; }
  .footer-compact-links { gap: 2rem; }
}

/* ── Cookie banner ──────────────────────────────────────────────────── */
.cookie-banner {
  position: fixed;
  bottom: 1.75rem;
  left: 50%;
  transform: translateX(-50%);
  z-index: 9999;
  background: rgba(14, 14, 32, 0.98);
  border: 1px solid var(--card-border);
  border-radius: var(--radius-lg);
  padding: 1.25rem 1.75rem;
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  display: flex;
  align-items: center;
  gap: 1.5rem;
  max-width: 680px;
  width: calc(100% - 3rem);
  box-shadow: var(--shadow-lg);
  transition: opacity var(--transition), transform var(--transition);
}

.cookie-banner.hidden {
  opacity: 0;
  pointer-events: none;
  transform: translateX(-50%) translateY(12px);
}

.cookie-text {
  flex: 1;
  font-size: 0.95rem;
  color: var(--text-secondary);
  line-height: 1.6;
}

.cookie-text a { color: var(--accent); }

.cookie-actions {
  display: flex;
  gap: 0.65rem;
  flex-shrink: 0;
}

/* ── Scroll animations ──────────────────────────────────────────────── */
.fade-in {
  opacity: 0;
  transform: translateY(22px);
  transition: opacity 0.55s ease, transform 0.55s ease;
}

.fade-in.visible {
  opacity: 1;
  transform: translateY(0);
}

.fade-in-delay-1 { transition-delay: 0.08s; }
.fade-in-delay-2 { transition-delay: 0.16s; }
.fade-in-delay-3 { transition-delay: 0.24s; }
.fade-in-delay-4 { transition-delay: 0.32s; }
.fade-in-delay-5 { transition-delay: 0.40s; }
.fade-in-delay-6 { transition-delay: 0.48s; }

/* ── Utility ────────────────────────────────────────────────────────── */
.text-accent { color: var(--accent); }
.text-muted  { color: var(--text-muted); }
.mt-2  { margin-top: 2rem; }
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0,0,0,0);
  white-space: nowrap;
}

/* ── Responsive ─────────────────────────────────────────────────────── */
@media (max-width: 900px) {
  .footer-grid {
    grid-template-columns: 1fr 1fr;
  }
  .footer-brand {
    grid-column: 1 / -1;
  }
}

@media (max-width: 768px) {
  /* Flatten the wrapper card edge-to-edge on narrow screens */
  .page-wrapper {
    margin: 0;
    border-radius: 0;
    border-left: none;
    border-right: none;
    min-height: 100vh;
    box-shadow: none;
  }

  .nav-menu {
    display: none;
    position: absolute;
    top: 72px;
    left: 0;
    right: 0;
    background: var(--nav-bg);
    flex-direction: column;
    align-items: flex-start;
    padding: 1.25rem 2rem 1.5rem;
    border-bottom: 1px solid var(--card-border);
    gap: 0;
  }
  .nav-menu.open { display: flex; }
  .nav-menu li { width: 100%; }
  .nav-menu a {
    display: block;
    padding: 0.75rem 0;
    border-bottom: 1px solid rgba(108,99,255,0.1);
  }
  .nav-menu a::after { display: none; }
  .hamburger { display: flex; }
  .nav-cta { display: none; }

  .navbar { padding: 0 1.25rem; height: 68px; }
  .navbar.scrolled { height: 58px; }
  .section { padding: 4rem 1rem; }
  .hero { min-height: 80vh; padding: 4rem 1rem; }

  .footer-grid { grid-template-columns: 1fr; gap: 2rem; }
  .footer-bottom { flex-direction: column; text-align: center; }

  .cookie-banner { flex-direction: column; align-items: flex-start; gap: 1rem; }

  .game-topbar { padding: 0.75rem 1rem; }

  .form-card { padding: 1.75rem; }
}

@media (max-width: 480px) {
  .hero h1 { font-size: 2rem; }
  .cta-group { flex-direction: column; align-items: center; }
  .cta-group .btn { width: 100%; max-width: 300px; }
  .cookie-actions { width: 100%; }
  .cookie-actions .btn { flex: 1; }
}

/* ── Per-batch generated CSS (layout, navbar, footer, sections) ──── */
[[VARIANT_CSS]]

/* ── Per-topic visual effects ────────────────────────────────────── */
[[TOPIC_FX]]
""".strip()


# ═══════════════════════════════════════════════════════════════════════════════
#  Per-topic visual effect packs
#
#  Each pack:
#    • overrides :root accent colours so every accent-coloured element matches
#    • defines @keyframes specific to that theme
#    • applies animations to hero overlays, cards, icons, or headings
#
#  Implementation notes:
#    - Hero overlays use .hero::before (above the filtered .hero-bg, below content)
#    - Card glows use filter:drop-shadow to avoid colliding with box-shadow transitions
#    - body::after (sci-fi scanlines) uses position:fixed to escape .page-wrapper clip
# ═══════════════════════════════════════════════════════════════════════════════

_TOPIC_CSS: dict[str, str] = {

# ────────────────────────────────────────────────────────────────────────────
"fantasy": """
/* THEME: fantasy — ethereal glow, floating icons, shimmer headings */
:root {
  --accent:      #7c6cff;
  --accent-hover:#9b8dff;
  --accent-glow: rgba(124, 108, 255, 0.38);
}

@keyframes fx-float {
  0%, 100% { transform: translateY(0);    }
  50%       { transform: translateY(-9px); }
}
@keyframes fx-magic-glow {
  0%, 100% { filter: drop-shadow(0 0  8px rgba(124,108,255,0.18)); }
  50%       { filter: drop-shadow(0 0 22px rgba(124,108,255,0.55)); }
}
@keyframes fx-shimmer {
  0%   { background-position: -300% center; }
  100% { background-position:  300% center; }
}

/* Floating + pulsing glow on feature icons */
.feature-icon {
  animation: fx-float 4s ease-in-out infinite,
             fx-magic-glow 4s ease-in-out infinite;
}

/* Radial magic-circle glow behind hero content */
.hero::before {
  content: '';
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background: radial-gradient(ellipse 70% 50% at 50% 40%,
    rgba(124,108,255,0.24) 0%, transparent 70%);
  animation: fx-magic-glow 7s ease-in-out infinite;
  filter: none !important;
}

/* Gold-to-purple shimmer sweep on section headings */
.section-header h2 {
  background: linear-gradient(90deg,
    #f0effe 0%, var(--accent-hover) 40%, #f0effe 80%);
  background-size: 200% auto;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: fx-shimmer 6s linear infinite;
}
""",

# ────────────────────────────────────────────────────────────────────────────
"sci-fi": """
/* THEME: sci-fi — neon cyan, CRT scanlines, hero glitch */
:root {
  --accent:      #00d4ff;
  --accent-hover:#33ddff;
  --accent-glow: rgba(0, 212, 255, 0.38);
}

@keyframes fx-glitch {
  0%, 86%, 100% { transform: none; text-shadow: none; }
  88%  { transform: skewX(-3deg) translateX(-3px);
         text-shadow: 3px 0 rgba(0,212,255,0.85), -3px 0 rgba(255,0,80,0.65); }
  90%  { transform: skewX( 2deg) translateX( 2px);
         text-shadow: -2px 0 rgba(0,212,255,0.55); }
  92%  { transform: none;
         text-shadow: 2px 0 rgba(255,0,80,0.40); }
}
@keyframes fx-sweep {
  0%        { opacity: 0; top: -4px;  }
  8%, 18%   { opacity: 0.75;          }
  28%       { opacity: 0; top: 100%;  }
  100%      { opacity: 0; top: 100%;  }
}

/* CRT scanline texture fixed over the viewport */
body::after {
  content: '';
  position: fixed;
  inset: 0;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 3px,
    rgba(0, 212, 255, 0.016) 3px,
    rgba(0, 212, 255, 0.016) 4px
  );
  pointer-events: none;
  z-index: 9997;
}

/* Neon sweep line that descends the hero */
.hero::before {
  content: '';
  position: absolute;
  left: 0; right: 0; height: 3px; top: 0;
  z-index: 2;
  pointer-events: none;
  background: linear-gradient(90deg,
    transparent 0%, rgba(0,212,255,0.90) 50%, transparent 100%);
  animation: fx-sweep 7s ease-in-out infinite;
}

/* Periodic glitch on the main headline */
.hero h1 { animation: fx-glitch 8s ease-in-out infinite; }
""",

# ────────────────────────────────────────────────────────────────────────────
"battle": """
/* THEME: battle — blood-red, ember pulse, animated strike line */
:root {
  --accent:      #e84040;
  --accent-hover:#ff6060;
  --accent-glow: rgba(232, 64, 64, 0.38);
}

@keyframes fx-ember {
  0%, 100% { filter: drop-shadow(0 0  6px rgba(232,64,64,0.12)); }
  50%       { filter: drop-shadow(0 0 20px rgba(232,64,64,0.38)); }
}
@keyframes fx-strike {
  0%   { transform: scaleX(0); transform-origin: left;  opacity: 0; }
  40%  { transform: scaleX(1); transform-origin: left;  opacity: 1; }
  60%  { transform: scaleX(1); transform-origin: right; opacity: 1; }
  100% { transform: scaleX(0); transform-origin: right; opacity: 0; }
}

/* Pulsing ember glow on content cards */
.card, .feature-card, .legal-section, .legal-toc {
  animation: fx-ember 3.5s ease-in-out infinite;
}

/* Animated red strike line under every section heading */
.section-header::after {
  content: '';
  display: block;
  height: 2px;
  margin-top: 1.4rem;
  background: linear-gradient(90deg, transparent, var(--accent), transparent);
  animation: fx-strike 4s ease-in-out infinite;
}

/* Low ember glow rising from the bottom of the hero */
.hero::before {
  content: '';
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background: radial-gradient(ellipse 65% 35% at 50% 85%,
    rgba(232,64,64,0.20) 0%, transparent 70%);
}
""",

# ────────────────────────────────────────────────────────────────────────────
"legend": """
/* THEME: legend — antique gold, shimmer headings, orbiting icon glow */
:root {
  --accent:      #c9a84c;
  --accent-hover:#e0bf6a;
  --accent-glow: rgba(201, 168, 76, 0.38);
}

@keyframes fx-gold {
  0%   { background-position: -300% center; }
  100% { background-position:  300% center; }
}
@keyframes fx-orbit {
  0%   { filter: drop-shadow( 8px  0   16px rgba(201,168,76,0.50)); }
  25%  { filter: drop-shadow( 0    8px 16px rgba(201,168,76,0.50)); }
  50%  { filter: drop-shadow(-8px  0   16px rgba(201,168,76,0.50)); }
  75%  { filter: drop-shadow( 0   -8px 16px rgba(201,168,76,0.50)); }
  100% { filter: drop-shadow( 8px  0   16px rgba(201,168,76,0.50)); }
}

/* Gold shimmer sweep on hero h1 and section headings */
.hero h1, .section-header h2 {
  background: linear-gradient(90deg,
    #f8f4e8 0%, #e8cf80 22%, #f8f4e8 50%, #c9a84c 72%, #f8f4e8 100%);
  background-size: 300% auto;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: fx-gold 5s linear infinite;
}

/* Orbiting gold glow around feature icons */
.feature-icon { animation: fx-orbit 4s linear infinite; }

/* Warm gold ambient over hero */
.hero::before {
  content: '';
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background: radial-gradient(ellipse 80% 50% at 50% 28%,
    rgba(201,168,76,0.14) 0%, transparent 70%);
}
""",

# ────────────────────────────────────────────────────────────────────────────
"sports": """
/* THEME: sports — electric green, speed streaks, energy pulse on CTA */
:root {
  --accent:      #00e676;
  --accent-hover:#33eb8e;
  --accent-glow: rgba(0, 230, 118, 0.38);
}

@keyframes fx-streak {
  0%   { background-position:  200% center; }
  100% { background-position: -200% center; }
}
@keyframes fx-energy {
  0%   { box-shadow: 0 0 0  0   rgba(0,230,118,0.60); }
  70%  { box-shadow: 0 0 0 18px rgba(0,230,118,0.00); }
  100% { box-shadow: 0 0 0  0   rgba(0,230,118,0.00); }
}

/* Diagonal speed-streak overlay across the hero */
.hero::before {
  content: '';
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background: repeating-linear-gradient(
    72deg,
    transparent 0%, transparent 46%,
    rgba(0,230,118,0.042) 46%, rgba(0,230,118,0.042) 54%,
    transparent 54%
  );
  background-size: 80px 100%;
  animation: fx-streak 3s linear infinite;
}

/* Expanding ring pulse on the primary CTA */
.btn-primary { animation: fx-energy 2.2s ease-out infinite; }
""",

# ────────────────────────────────────────────────────────────────────────────
"horror": """
/* THEME: horror — deep purple, irregular flicker, fog, creeping glow */
:root {
  --accent:      #7b1fa2;
  --accent-hover:#9c27b0;
  --accent-glow: rgba(123, 31, 162, 0.38);
}

@keyframes fx-flicker {
  0%, 91%, 100% { opacity: 1;    }
  92%            { opacity: 0.88; }
  93%            { opacity: 1;    }
  95%            { opacity: 0.82; }
  96%            { opacity: 0.96; }
  98%            { opacity: 0.87; }
}
@keyframes fx-fog {
  0%, 100% { transform: translateX(-7%); opacity: 0.55; }
  50%       { transform: translateX( 7%); opacity: 0.85; }
}
@keyframes fx-creep {
  0%, 100% { filter: drop-shadow(0 0  8px rgba(123,31,162,0.10)); }
  50%       { filter: drop-shadow(0 0 24px rgba(123,31,162,0.32)); }
}

/* Subtle page-flicker — barely perceptible, deeply unsettling */
.page-wrapper { animation: fx-flicker 11s ease-in-out infinite; }

/* Fog layer drifting at the bottom of the hero */
.hero::before {
  content: '';
  position: absolute;
  bottom: 0; left: -12%; right: -12%; top: 58%;
  z-index: 1;
  pointer-events: none;
  background: linear-gradient(to top, rgba(0,12,6,0.65) 0%, transparent 100%);
  filter: blur(16px);
  animation: fx-fog 14s ease-in-out infinite;
}

/* Cards slowly pulse with a sickly purple glow */
.card, .game-card, .feature-card {
  animation: fx-creep 5.5s ease-in-out infinite;
}
""",

# ────────────────────────────────────────────────────────────────────────────
"adventure": """
/* THEME: adventure — amber warmth, dual radial glow, compass-spin icons */
:root {
  --accent:      #ff9800;
  --accent-hover:#ffb74d;
  --accent-glow: rgba(255, 152, 0, 0.38);
}

@keyframes fx-warmth {
  0%, 100% { opacity: 0.55; transform: scale(1.00); }
  50%       { opacity: 0.85; transform: scale(1.07); }
}
@keyframes fx-compass {
  0%   { transform: rotate(  0deg); }
  14%  { transform: rotate(-13deg); }
  34%  { transform: rotate( 19deg); }
  54%  { transform: rotate( -8deg); }
  74%  { transform: rotate( 15deg); }
  100% { transform: rotate(  0deg); }
}

/* Dual warm-light radial gradients breathing in the hero */
.hero::before {
  content: '';
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background:
    radial-gradient(ellipse 55% 42% at 22% 65%, rgba(255,152,0,0.17) 0%, transparent 60%),
    radial-gradient(ellipse 45% 36% at 78% 34%, rgba(255,195,60,0.11) 0%, transparent 60%);
  animation: fx-warmth 9s ease-in-out infinite;
}

/* Feature icons wobble like a compass needle */
.feature-icon {
  animation: fx-compass 6s ease-in-out infinite;
  transform-origin: center center;
}
""",

# ────────────────────────────────────────────────────────────────────────────
"colorful": """
/* THEME: colorful — hot pink, animated rainbow border, hue-spin icons */
:root {
  --accent:      #ff4081;
  --accent-hover:#ff6ea6;
  --accent-glow: rgba(255, 64, 129, 0.38);
}

@keyframes fx-rainbow {
  0%   { border-color: rgba(255, 64,129,0.50); }
  25%  { border-color: rgba( 80,200,255,0.50); }
  50%  { border-color: rgba( 90,230,110,0.50); }
  75%  { border-color: rgba(255,200,  0,0.50); }
  100% { border-color: rgba(255, 64,129,0.50); }
}
@keyframes fx-hue-spin {
  0%   { filter: hue-rotate(  0deg) saturate(1.5); }
  100% { filter: hue-rotate(360deg) saturate(1.5); }
}
@keyframes fx-pop {
  0%   { transform: scale(1.00); }
  28%  { transform: scale(1.07); }
  58%  { transform: scale(0.97); }
  100% { transform: scale(1.00); }
}

/* Full wrapper border cycles through the spectrum */
.page-wrapper { animation: fx-rainbow 6s ease-in-out infinite; }

/* Feature icons spin through all hues */
.feature-icon { animation: fx-hue-spin 8s linear infinite; }

/* Cards pop on hover */
.card:hover, .game-card:hover, .feature-card:hover {
  animation: fx-pop 0.42s ease-out forwards;
}

/* Candy-gradient hero overlay */
.hero::before {
  content: '';
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background: linear-gradient(135deg,
    rgba(255,64,129,0.11) 0%,
    rgba(80,200,255,0.09) 35%,
    rgba(90,230,110,0.08) 65%,
    rgba(255,200,0,0.09)  100%
  );
}
""",


# ────────────────────────────────────────────────────────────────────────────
"rpg": """
/* THEME: rpg — burnished gold, arcane scroll-unfurl, runic pulse */
:root {
  --accent:      #c9a227;
  --accent-hover:#ffd700;
  --accent-glow: rgba(201, 162, 39, 0.38);
}

@keyframes fx-runicpulse {
  0%, 100% { text-shadow: 0 0  6px rgba(201,162,39,0.30); }
  50%       { text-shadow: 0 0 22px rgba(201,162,39,0.70), 0 0 40px rgba(255,215,0,0.30); }
}
@keyframes fx-scroll-unfurl {
  0%   { transform: scaleY(0.92); opacity: 0.70; }
  50%  { transform: scaleY(1.04); opacity: 1.00; }
  100% { transform: scaleY(0.92); opacity: 0.70; }
}
@keyframes fx-rpg-glow {
  0%, 100% { filter: drop-shadow(0 0  8px rgba(201,162,39,0.15)); }
  50%       { filter: drop-shadow(0 0 20px rgba(201,162,39,0.45)); }
}

/* Headings pulse with runic gold light */
h1, h2 { animation: fx-runicpulse 5s ease-in-out infinite; }

/* Hero radiates two warm radial glows */
.hero::before {
  content: '';
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background:
    radial-gradient(ellipse 60% 50% at 30% 70%, rgba(201,162,39,0.14) 0%, transparent 60%),
    radial-gradient(ellipse 40% 35% at 72% 28%, rgba(255,215,0,0.09) 0%, transparent 60%);
  animation: fx-scroll-unfurl 10s ease-in-out infinite;
}

/* Cards pulse with gold aura */
.card, .game-card, .feature-card {
  animation: fx-rpg-glow 6s ease-in-out infinite;
}
""",

# ────────────────────────────────────────────────────────────────────────────
"strategy": """
/* THEME: strategy — steel blue, tactical grid overlay, march sweep */
:root {
  --accent:      #4d94ff;
  --accent-hover:#80b3ff;
  --accent-glow: rgba(77, 148, 255, 0.35);
}

@keyframes fx-marching {
  0%   { background-position: 0 0; }
  100% { background-position: 40px 40px; }
}
@keyframes fx-tactical-ping {
  0%, 100% { box-shadow: 0 0 0 0 rgba(77,148,255,0.0); }
  40%       { box-shadow: 0 0 0 8px rgba(77,148,255,0.20); }
  80%       { box-shadow: 0 0 0 18px rgba(77,148,255,0.0); }
}

/* Subtle marching-grid overlay on hero */
.hero::before {
  content: '';
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background-image:
    linear-gradient(rgba(77,148,255,0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(77,148,255,0.04) 1px, transparent 1px);
  background-size: 40px 40px;
  animation: fx-marching 8s linear infinite;
}

/* Game cards ping like tactical map icons */
.game-card { animation: fx-tactical-ping 5s ease-in-out infinite; }
""",

# ────────────────────────────────────────────────────────────────────────────
"puzzle": """
/* THEME: puzzle — teal-cyan, rotating geometric orbits */
:root {
  --accent:      #00d4aa;
  --accent-hover:#00f7c8;
  --accent-glow: rgba(0, 212, 170, 0.35);
}

@keyframes fx-orbit {
  0%   { transform: rotate(  0deg); }
  100% { transform: rotate(360deg); }
}
@keyframes fx-piece-shift {
  0%, 100% { transform: translate(0, 0) rotate(0deg); }
  25%       { transform: translate( 3px, -3px) rotate( 4deg); }
  75%       { transform: translate(-3px,  3px) rotate(-4deg); }
}

/* Feature icons orbit gently */
.feature-icon { animation: fx-orbit 18s linear infinite; }

/* Hero: soft teal vortex gradient */
.hero::before {
  content: '';
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background: conic-gradient(
    from 180deg at 50% 55%,
    rgba(0,212,170,0.08) 0deg,
    transparent 60deg,
    rgba(0,247,200,0.05) 120deg,
    transparent 200deg,
    rgba(0,212,170,0.07) 300deg,
    transparent 360deg
  );
  animation: fx-orbit 30s linear infinite;
}

/* Cards shift playfully on reveal */
.card, .feature-card { animation: fx-piece-shift 8s ease-in-out infinite; }
""",

# ────────────────────────────────────────────────────────────────────────────
"arcade": """
/* THEME: arcade — phosphor green, scanlines, pixel flicker */
:root {
  --accent:      #39ff14;
  --accent-hover:#7fff00;
  --accent-glow: rgba(57, 255, 20, 0.38);
}

@keyframes fx-scanlines-scroll {
  0%   { background-position: 0 0; }
  100% { background-position: 0 -8px; }
}
@keyframes fx-pixel-flicker {
  0%, 94%, 100% { opacity: 1; }
  95%            { opacity: 0.85; }
  97%            { opacity: 0.96; }
  98%            { opacity: 0.80; }
}
@keyframes fx-blink {
  0%, 48%, 100% { opacity: 1; }
  50%, 98%      { opacity: 0; }
}

/* Persistent scanline overlay across the whole page */
body::after {
  content: '';
  position: fixed;
  inset: 0;
  z-index: 9998;
  pointer-events: none;
  background-image: repeating-linear-gradient(
    to bottom,
    rgba(0,0,0,0.12) 0px,
    rgba(0,0,0,0.12) 2px,
    transparent       2px,
    transparent       4px
  );
  background-size: 100% 4px;
  animation: fx-scanlines-scroll 0.18s linear infinite;
}

/* Whole page flickers like a CRT */
.page-wrapper { animation: fx-pixel-flicker 7s ease-in-out infinite; }

/* Hero badge blinks like an INSERT COIN prompt */
.hero-badge { animation: fx-blink 1.2s step-start infinite; }
""",

# ────────────────────────────────────────────────────────────────────────────
"racing": """
/* THEME: racing — speed orange, motion blur streaks, rpm needle */
:root {
  --accent:      #ff6b00;
  --accent-hover:#ff8c42;
  --accent-glow: rgba(255, 107, 0, 0.38);
}

@keyframes fx-speedstreak {
  0%   { transform: translateX(-110%); opacity: 0;    }
  20%  { opacity: 0.55; }
  80%  { opacity: 0.55; }
  100% { transform: translateX(110%);  opacity: 0;    }
}
@keyframes fx-vibrate {
  0%, 100% { transform: translate(0, 0) rotate(0deg); }
  20%       { transform: translate( 1px, -1px) rotate( 0.4deg); }
  40%       { transform: translate(-1px,  1px) rotate(-0.4deg); }
  60%       { transform: translate( 1px,  0px) rotate( 0.2deg); }
  80%       { transform: translate(-1px, -1px) rotate(-0.2deg); }
}

/* Motion blur streak sweeps across the hero */
.hero::before {
  content: '';
  position: absolute;
  top: 42%; left: 0; right: 0;
  height: 3px;
  z-index: 1;
  pointer-events: none;
  background: linear-gradient(90deg, transparent 0%, var(--accent) 40%, #fff 50%, var(--accent) 60%, transparent 100%);
  filter: blur(3px);
  animation: fx-speedstreak 2.8s ease-in-out infinite;
}

/* Hero badge vibrates at high RPM */
.hero-badge { animation: fx-vibrate 0.12s linear infinite; }

/* Card shake on hover */
.game-card:hover { animation: fx-vibrate 0.08s linear infinite; }
""",

# ────────────────────────────────────────────────────────────────────────────
"neon": """
/* TONE: neon — electric cyan/magenta cyberpunk palette */
:root {
  --accent:      #00e5ff;
  --accent-hover:#80f0ff;
  --accent-glow: rgba(0, 229, 255, 0.40);
}

@keyframes fx-neon-pulse {
  0%, 100% { opacity: 0.80; filter: drop-shadow(0 0 8px  rgba(0,229,255,0.40)); }
  50%       { opacity: 1.00; filter: drop-shadow(0 0 22px rgba(0,229,255,0.80)); }
}
@keyframes fx-neon-bg-drift {
  0%, 100% { background-position: 0% 50%; }
  50%       { background-position: 100% 50%; }
}

/* Background gradient shifts like a hologram */
body {
  background: linear-gradient(135deg, #000014 0%, #0a001e 50%, #00001a 100%);
  background-size: 300% 300%;
  animation: fx-neon-bg-drift 14s ease-in-out infinite;
}

/* Accent line on navbar pulsates neon */
.navbar::before { animation: fx-neon-pulse 2.5s ease-in-out infinite; }

/* Card borders glow cyan */
.card, .game-card, .feature-card {
  border-color: rgba(0,229,255,0.28);
  box-shadow: 0 0 0 1px rgba(0,229,255,0.08), inset 0 0 20px rgba(0,229,255,0.04);
  animation: fx-neon-pulse 4s ease-in-out infinite;
}

/* Hero: dual neon sweep */
.hero::before {
  content: '';
  position: absolute;
  inset: 0; z-index: 0; pointer-events: none;
  background:
    radial-gradient(ellipse 50% 40% at 20% 60%, rgba(0,229,255,0.12) 0%, transparent 55%),
    radial-gradient(ellipse 40% 35% at 80% 35%, rgba(255,0,200,0.09) 0%, transparent 55%);
}
""",

# ────────────────────────────────────────────────────────────────────────────
"epic": """
/* TONE: epic — deep gold, god-rays, monumental sweep */
:root {
  --accent:      #e8b84b;
  --accent-hover:#ffd966;
  --accent-glow: rgba(232, 184, 75, 0.40);
}

@keyframes fx-godray {
  0%, 100% { transform: rotate(-8deg) translateX(-30%) scaleY(1.0); opacity: 0.10; }
  50%       { transform: rotate( 3deg) translateX( 20%) scaleY(1.15); opacity: 0.22; }
}
@keyframes fx-epic-rise {
  0%, 100% { letter-spacing: -0.02em; }
  50%       { letter-spacing:  0.01em; }
}
@keyframes fx-crown-glow {
  0%, 100% { filter: drop-shadow(0 0  6px rgba(232,184,75,0.25)); }
  50%       { filter: drop-shadow(0 0 28px rgba(232,184,75,0.65)); }
}

/* God-ray sweeping the hero */
.hero::before {
  content: '';
  position: absolute;
  top: -20%; left: 0; right: 0; bottom: -10%;
  z-index: 0; pointer-events: none;
  background: conic-gradient(
    from 260deg at 50% 0%,
    transparent 0deg,
    rgba(232,184,75,0.12) 10deg,
    transparent 25deg,
    rgba(255,215,0,0.07) 35deg,
    transparent 55deg
  );
  animation: fx-godray 11s ease-in-out infinite;
}

/* Headings slowly breathe */
h1 { animation: fx-epic-rise 8s ease-in-out infinite; }

/* Feature icons crowned with gold glow */
.feature-icon { animation: fx-crown-glow 5s ease-in-out infinite; }
""",

}   # end _TOPIC_CSS

# Fallback for unknown topics
_TOPIC_CSS["default"] = _TOPIC_CSS["fantasy"]


# ═══════════════════════════════════════════════════════════════════════════════
#  Per-variant CSS overrides
# ═══════════════════════════════════════════════════════════════════════════════

# Palette → bg colour values
_PALETTE_COLORS: dict[str, tuple[str, str, str]] = {
    # name:       (bg-primary,  bg-secondary, card-tint)
    "midnight": ("#080812", "#0f0f22", "rgba(15, 15, 40, 0.97)"),
    "charcoal": ("#0a0a0a", "#141414", "rgba(20, 20, 20, 0.97)"),
    "slate":    ("#0b0e1c", "#131828", "rgba(16, 20, 38, 0.97)"),
    "forest":   ("#060f09", "#0c1a10", "rgba(10, 22, 14, 0.97)"),
    "volcanic": ("#0f0808", "#1c1010", "rgba(24, 12, 10, 0.97)"),
    "amethyst": ("#0d0814", "#16101e", "rgba(20, 12, 30, 0.97)"),
    "abyss":    ("#060810", "#0c1018", "rgba(10, 14, 24, 0.97)"),
    "onyx":     ("#0c0b0c", "#141214", "rgba(20, 18, 20, 0.97)"),
}

# Page-wrapper accent glow colour per palette
_PALETTE_GLOW: dict[str, str] = {
    "midnight": "rgba(108, 99, 255, 0.14)",
    "charcoal": "rgba(130, 130, 130, 0.10)",
    "slate":    "rgba( 80, 120, 255, 0.13)",
    "forest":   "rgba( 40, 200,  80, 0.11)",
    "volcanic": "rgba(220,  60,  30, 0.13)",
    "amethyst": "rgba(160,  40, 220, 0.14)",
    "abyss":    "rgba( 40,  80, 200, 0.12)",
    "onyx":     "rgba(180, 180, 200, 0.08)",
}

# Footer treatments per palette family
_FOOTER_PALETTE: dict[str, str] = {
    # cool blue-purple (midnight, slate, abyss)
    "cool": "rgba(8, 8, 24, 0.98)",
    # neutral dark (charcoal, onyx)
    "neutral": "rgba(10, 10, 12, 0.98)",
    # green tint (forest)
    "green": "rgba(6, 14, 8, 0.98)",
    # warm ember (volcanic)
    "warm": "rgba(16, 8, 6, 0.98)",
    # deep purple (amethyst)
    "purple": "rgba(12, 6, 20, 0.98)",
}
_PALETTE_FOOTER_FAMILY: dict[str, str] = {
    "midnight": "cool",
    "charcoal": "neutral",
    "slate":    "cool",
    "forest":   "green",
    "volcanic": "warm",
    "amethyst": "purple",
    "abyss":    "cool",
    "onyx":     "neutral",
}


# ── Navbar style CSS overrides ─────────────────────────────────────────────────
# Each entry produces dramatically different header appearance.
# Rules are appended after the base navbar CSS in _variant_css().
_NAV_STYLE_CSS: dict[str, str] = {

# ────────────────────────────────────────────────────────────────────────────
"glass": "",   # default: base CSS handles it — transparent → blur on scroll

# ────────────────────────────────────────────────────────────────────────────
"solid": """
/* NAV: solid — opaque from the very first pixel, always-visible panel */
.navbar {
  height: 80px;
  background: linear-gradient(
    180deg, rgba(10,10,28,0.99) 0%, rgba(6,6,18,0.99) 100%
  );
  border-bottom: 2px solid rgba(108,99,255,0.35);
  box-shadow: 0 4px 24px rgba(0,0,0,0.70);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}
.navbar.scrolled {
  height: 58px;
  background: linear-gradient(
    180deg, rgba(6,6,18,1.0) 0%, rgba(4,4,14,1.0) 100%
  );
  border-bottom-color: rgba(108,99,255,0.22);
  box-shadow: 0 2px 16px rgba(0,0,0,0.80);
}
.navbar::before { display: none; }
.navbar-brand { font-size: 1.32rem; letter-spacing: 0.01em; }
.navbar.scrolled .navbar-brand { font-size: 1.12rem; }
""",

# ────────────────────────────────────────────────────────────────────────────
"glow": """
/* NAV: glow — transparent start, vivid accent ring materialises on scroll */
.navbar.scrolled {
  background: linear-gradient(
    180deg, rgba(10,10,26,0.92) 0%, rgba(8,8,20,0.90) 100%
  );
  border-bottom-color: var(--accent);
  box-shadow:
    0 0  0  1px var(--accent),
    0 4px 32px var(--accent-glow),
    0 0  60px var(--accent-glow),
    0 8px 40px rgba(0,0,0,0.65);
  backdrop-filter: blur(16px) saturate(160%);
  -webkit-backdrop-filter: blur(16px) saturate(160%);
}
.navbar.scrolled::before { opacity: 1.0; }
.navbar-brand img {
  box-shadow: 0 0 0 2px var(--accent), 0 0 24px var(--accent-glow);
}
.navbar.scrolled .navbar-brand img {
  box-shadow: 0 0 0 2px var(--accent), 0 0 14px var(--accent-glow);
}
""",

# ────────────────────────────────────────────────────────────────────────────
"accent": """
/* NAV: accent — vivid accent-gradient tint, Exo 2 display font */
.navbar {
  height: 96px;
  background: linear-gradient(
    135deg,
    color-mix(in srgb, var(--accent) 22%, rgba(10,10,26,0.97)) 0%,
    rgba(10,10,26,0.97) 60%
  );
  border-bottom: 1px solid rgba(255,255,255,0.08);
  box-shadow: 0 4px 40px rgba(0,0,0,0.50);
  backdrop-filter: blur(14px) saturate(120%);
  -webkit-backdrop-filter: blur(14px) saturate(120%);
}
.navbar.scrolled {
  height: 62px;
  background: linear-gradient(
    135deg,
    color-mix(in srgb, var(--accent) 14%, rgba(8,8,20,0.99)) 0%,
    rgba(8,8,20,0.99) 60%
  );
}
.navbar::before {
  height: 3px;
  background: linear-gradient(
    90deg, transparent 0%, var(--accent) 20%, #fff 50%, var(--accent) 80%, transparent 100%
  );
  opacity: 0.75;
}
.navbar.scrolled::before { opacity: 0.45; }
.navbar-brand {
  font-family: 'Exo 2', 'Space Grotesk', sans-serif;
  font-size: 1.48rem;
  font-weight: 800;
  font-style: italic;
  letter-spacing: 0.02em;
}
.navbar.scrolled .navbar-brand { font-size: 1.22rem; }
.navbar-brand span {
  background: linear-gradient(135deg, #ffffff 0%, var(--accent-hover) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.nav-menu a {
  color: rgba(255,255,255,0.82);
  font-family: 'Exo 2', 'Inter', sans-serif;
  font-weight: 600;
  font-size: 0.94rem;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
.nav-menu a:hover, .nav-menu a.active { color: #fff; }
""",

# ────────────────────────────────────────────────────────────────────────────
"minimal": """
/* NAV: minimal — ultra-clean, near-invisible, type-forward */
.navbar {
  height: 66px;
  background: rgba(8,8,20,0.38);
  border-bottom: 1px solid rgba(255,255,255,0.04);
  box-shadow: none;
}
.navbar.scrolled {
  height: 54px;
  background: rgba(8,8,22,0.82);
  border-bottom-color: rgba(255,255,255,0.07);
  box-shadow: 0 1px 12px rgba(0,0,0,0.40);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}
.navbar::before { display: none; }
.navbar-brand {
  font-family: 'Inter', sans-serif;
  font-size: 1.05rem;
  font-weight: 600;
  letter-spacing: 0.03em;
}
.navbar.scrolled .navbar-brand { font-size: 0.98rem; }
.navbar-brand span {
  background: none;
  -webkit-text-fill-color: var(--text);
  color: var(--text);
}
.navbar-brand img {
  width: 30px; height: 30px;
  border-radius: 8px;
  box-shadow: none;
  border: 1px solid rgba(255,255,255,0.12);
}
.navbar.scrolled .navbar-brand img { width: 26px; height: 26px; }
.nav-menu { gap: 1.8rem; }
.nav-menu a {
  font-size: 0.86rem;
  font-weight: 400;
  color: rgba(200,200,222,0.58);
  letter-spacing: 0.06em;
  text-transform: uppercase;
}
.nav-menu a::after { display: none; }
.nav-menu a:hover { color: var(--text); }
.nav-menu a.active { color: var(--accent); font-weight: 600; }
""",

# ────────────────────────────────────────────────────────────────────────────
"bold": """
/* NAV: bold — tall, dramatic, Orbitron display font, accent bottom border */
.navbar {
  height: 112px;
  background: linear-gradient(
    180deg, rgba(18,12,36,0.99) 0%, rgba(10,8,24,0.99) 100%
  );
  border-bottom: 3px solid var(--accent);
  padding: 0 3rem;
  box-shadow: 0 4px 32px rgba(0,0,0,0.75);
}
.navbar.scrolled {
  height: 64px;
  background: linear-gradient(
    180deg, rgba(10,8,24,1.0) 0%, rgba(6,4,16,1.0) 100%
  );
  border-bottom-width: 2px;
  padding: 0 2.5rem;
  box-shadow: 0 3px 20px rgba(0,0,0,0.85);
}
.navbar::before { display: none; }
.navbar-brand {
  font-family: 'Orbitron', 'Space Grotesk', sans-serif;
  font-size: 1.6rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}
.navbar.scrolled .navbar-brand { font-size: 1.15rem; }
.navbar-brand img { width: 54px; height: 54px; border-radius: 14px; }
.navbar.scrolled .navbar-brand img { width: 36px; height: 36px; border-radius: 9px; }
.navbar-brand span {
  background: linear-gradient(90deg, var(--accent) 0%, #ffffff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.nav-menu a {
  font-family: 'Orbitron', 'Space Grotesk', sans-serif;
  font-size: 0.78rem;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: rgba(220,215,255,0.70);
}
.nav-menu a:hover, .nav-menu a.active { color: var(--accent); }
.nav-menu a::after { background: var(--accent); }
""",

}   # end _NAV_STYLE_CSS


def _variant_css(v: SiteVariant) -> str:
    """
    Generate all per-batch CSS from the variant's seed and dimension values.

    Nothing is hard-coded here: every pixel value, timing, opacity, and
    proportion is computed from ``v.seed`` so two batches with the same
    nav_style or hero_layout still produce measurably different CSS.
    Only the CSS required by the chosen layouts is emitted.
    """
    h = v.seed

    # ── Parametric helpers ────────────────────────────────────────────────────
    def vi(shift: int, lo: int, hi: int) -> int:
        """Integer in [lo, hi) extracted from seed bits at `shift`."""
        return lo + (h >> shift) % max(1, hi - lo)

    def vf(shift: int, lo: float, hi: float, steps: int = 16) -> float:
        """Float in [lo, hi) with `steps` quantisation."""
        return lo + ((h >> shift) % steps) / steps * (hi - lo)

    lines: list[str] = []

    # ── 1. Custom properties: full palette CSS vars + radius + transition ──────
    p    = v.palette if isinstance(v.palette, dict) else {}
    bp   = p.get("bg_page",    "#080812")
    bs   = p.get("bg_section", "#0f0f22")
    ct   = p.get("card_bg",    "rgba(15,15,40,0.97)")
    glow = p.get("glow",       "rgba(108,99,255,0.14)")
    r    = v.radius
    rsm  = max(3, r // 2)
    rlg  = r * 2
    trans_dur = vf(64, 0.20, 0.42)
    lines.append(f"""
:root {{
  /* Palette: {p.get('name', 'default')} ({p.get('family', 'dark')}) */
  --bg-primary:      {bp};
  --bg-secondary:    {bs};
  --accent:          {p.get('primary',   '#6c63ff')};
  --accent-hover:    {p.get('primary_h', '#8b84ff')};
  --accent-glow:     {p.get('glow',      'rgba(108,99,255,0.35)')};
  --secondary:       {p.get('secondary', '#2563eb')};
  --text:            {p.get('text',      '#f0effe')};
  --text-secondary:  {p.get('text2',     'rgba(240,239,254,0.75)')};
  --text-muted:      {p.get('text3',     'rgba(240,239,254,0.50)')};
  --card-bg:         {ct};
  --card-border:     {p.get('border',    'rgba(108,99,255,0.22)')};
  --nav-bg:          {ct};
  --grad-a:          {p.get('grad_a',    '#6c63ff')};
  --grad-b:          {p.get('grad_b',    '#2563eb')};
  --glow:            {p.get('glow',      'rgba(108,99,255,0.35)')};
  --radius:          {r}px;
  --radius-sm:       {rsm}px;
  --radius-lg:       {rlg}px;
  --transition:      {trans_dur:.2f}s ease;
}}""")

    # ── 2. Page-wrapper: unique background per batch ───────────────────────────
    bg_opacity = vf(68, 0.85, 0.95)
    blur_px    = vi(72, 4, 16)
    bdr_opacity = vf(76, 0.18, 0.44)
    glow_radius = vi(80, 80, 160)
    pw_bg_mode  = (h >> 84) % 3

    bpr = int(bp[1:3], 16)
    bpg = int(bp[3:5], 16)
    bpb = int(bp[5:7], 16)
    bsr = int(bs[1:3], 16)
    bsg = int(bs[3:5], 16)
    bsb = int(bs[5:7], 16)

    if pw_bg_mode == 0:
        pw_bg = f"rgba({bpr},{bpg},{bpb},{bg_opacity:.2f})"
    elif pw_bg_mode == 1:
        pw_bg = (f"linear-gradient(180deg,"
                 f"rgba({bpr},{bpg},{bpb},{bg_opacity:.2f}) 0%,"
                 f"rgba({bsr},{bsg},{bsb},{min(bg_opacity+0.04,0.99):.2f}) 100%)")
    else:
        angle = vi(86, 120, 160)
        pw_bg = (f"linear-gradient({angle}deg,"
                 f"rgba({bpr},{bpg},{bpb},{bg_opacity:.2f}) 0%,"
                 f"rgba({min(bsr+4,255)},{min(bsg+2,255)},{min(bsb+6,255)},{min(bg_opacity+0.03,0.99):.2f}) 55%)")

    lines.append(f"""
.page-wrapper {{
  background: {pw_bg};
  backdrop-filter: blur({blur_px}px);
  -webkit-backdrop-filter: blur({blur_px}px);
  border: 1px solid color-mix(in srgb, var(--accent) {int(bdr_opacity * 100)}%, transparent);
  border-radius: {rlg}px;
  box-shadow:
    0 2px 8px   rgba(0,0,0,0.58),
    0 14px 40px rgba(0,0,0,0.50),
    0 40px {glow_radius}px rgba(0,0,0,0.44),
    0 0   {glow_radius}px {glow},
    inset 0 1px 0 rgba(255,255,255,0.05);
}}""")

    # ── 3. Section spacing ────────────────────────────────────────────────────
    pad = {"tight": "4rem", "normal": "6rem", "generous": "9rem"}[v.spacing]
    hdr_gap = vf(88, 1.2, 1.9)
    lines.append(f"""
.section {{ padding: {pad} 1.5rem; }}
.section-header {{ margin-bottom: {hdr_gap:.1f}rem; }}""")

    # ── 4. Card style (computed values) ───────────────────────────────────────
    lift = vf(92, 2.0, 8.0)
    ctrans = vf(96, 0.22, 0.40)

    if v.card_style == "glass":
        g_opacity = vf(100, 0.03, 0.09)
        g_blur    = vi(104, 14, 30)
        g_sat     = vi(108, 118, 185)
        g_border  = vf(112, 0.06, 0.16)
        lines.append(f"""
.card, .game-card, .feature-card, .feature-horiz-card {{
  background: rgba(255,255,255,{g_opacity:.2f});
  backdrop-filter: blur({g_blur}px) saturate({g_sat}%);
  -webkit-backdrop-filter: blur({g_blur}px) saturate({g_sat}%);
  border-color: rgba(255,255,255,{g_border:.2f});
}}
.card:hover, .game-card:hover, .feature-card:hover, .feature-horiz-card:hover {{
  transform: translateY(-{lift:.0f}px);
  transition: transform {ctrans:.2f}s ease, box-shadow {ctrans:.2f}s ease;
}}""")
    elif v.card_style == "glow":
        g_spread = vi(100, 16, 44)
        lines.append(f"""
.card:hover, .game-card:hover, .feature-card:hover, .feature-horiz-card:hover {{
  transform: translateY(-{lift:.0f}px);
  box-shadow:
    0 0 0 1px var(--accent),
    0 6px {g_spread}px var(--accent-glow),
    0 24px 64px rgba(0,0,0,0.50);
  transition: transform {ctrans:.2f}s ease, box-shadow {ctrans:.2f}s ease;
}}""")
    else:  # solid
        lines.append(f"""
.card:hover, .game-card:hover, .feature-card:hover {{
  transform: translateY(-{lift:.0f}px);
  transition: transform {ctrans:.2f}s ease, box-shadow {ctrans:.2f}s ease;
}}""")

    # ── 5. Typography (computed per-batch sizes) ───────────────────────────────
    if v.typography == "compact":
        h1min = vf(116, 1.75, 2.1);  h1max = vf(120, 2.8, 3.4);  h1vw = vf(124, 4.5, 6.0)
        h2max = vf(128, 1.8, 2.2);   tls = vf(132, 0.005, 0.018)
        lines.append(f"""
h1, h2, h3, h4 {{ letter-spacing: -{tls:.3f}em; }}
.hero h1 {{ font-size: clamp({h1min:.2f}rem, {h1vw:.1f}vw, {h1max:.2f}rem); }}
.section-header h2 {{ font-size: clamp(1.5rem, 3vw, {h2max:.2f}rem); }}""")
    elif v.typography == "dramatic":
        h1min = vf(116, 2.4, 2.9);  h1max = vf(120, 4.2, 5.4);  h1vw = vf(124, 6.5, 8.5)
        h2max = vf(128, 2.6, 3.3);  tls = vf(132, 0.030, 0.058)
        badge_ls = vf(136, 3.0, 6.0);  badge_fs = vf(140, 0.65, 0.80)
        lines.append(f"""
h1, h2, h3, h4 {{ letter-spacing: -{tls:.3f}em; font-weight: 800; }}
.hero h1 {{ font-size: clamp({h1min:.2f}rem, {h1vw:.1f}vw, {h1max:.2f}rem); }}
.section-header h2 {{ font-size: clamp(1.9rem, 4vw, {h2max:.2f}rem); }}
.hero-badge {{ letter-spacing: {badge_ls:.1f}px; font-size: {badge_fs:.2f}rem; }}""")
    else:  # regular
        h1max = vf(116, 3.4, 4.1)
        lines.append(f"""
.hero h1 {{ font-size: clamp(2.2rem, 6vw, {h1max:.2f}rem); }}""")

    # ── 6. Hero — only the chosen layout ─────────────────────────────────────
    if v.hero_layout == "left":
        ml_vw  = vi(144, 4, 10);  ml_max = vi(148, 5, 9);  cw = vi(152, 540, 740)
        lines.append(f"""
.hero {{
  min-height: {v.hero_height};
  justify-content: flex-start;
  text-align: left;
}}
.hero-content {{
  max-width: {cw}px;
  margin-left: clamp(2rem, {ml_vw}vw, {ml_max}rem);
}}
.hero p {{ margin-left: 0; margin-right: 0; }}
.hero-badge {{ margin-left: 0; }}
.cta-group {{ justify-content: flex-start; }}""")

    elif v.hero_layout == "split":
        cw    = vi(144, 460, 600);  gap = vi(148, 2, 5);  img_h = vi(152, 130, 210)
        stag  = vi(156, 1, 4);  htrans = vf(160, 0.28, 0.52);  lift2 = vi(164, 3, 8)
        lines.append(f"""
.hero {{
  min-height: {v.hero_height};
  justify-content: flex-start;
  text-align: left;
  align-items: stretch;
}}
.hero-split-wrap {{
  position: relative; z-index: 1;
  display: grid; grid-template-columns: 1fr 1fr;
  align-items: center; gap: {gap}rem;
  width: 100%; max-width: 1200px;
  margin: 0 auto; padding: 0 2rem;
}}
.hero-content {{ max-width: {cw}px; }}
.hero p {{ margin-left: 0; margin-right: 0; }}
.cta-group {{ justify-content: flex-start; }}
.hero-split-visual {{ display: flex; flex-direction: column; gap: 1rem; }}
.hero-preview-card {{
  border-radius: var(--radius-lg); overflow: hidden;
  border: 1px solid color-mix(in srgb, var(--accent) 30%, transparent);
  box-shadow: 0 8px 32px rgba(0,0,0,0.55);
  transition: transform {htrans:.2f}s ease, box-shadow {htrans:.2f}s ease;
}}
.hero-preview-card img {{
  width: 100%; height: {img_h}px; object-fit: cover; display: block;
}}
.hero-preview-card:hover {{
  transform: translateY(-{lift2}px) scale(1.02);
  box-shadow: 0 16px 48px rgba(0,0,0,0.65);
}}
.hero-preview-card-lower {{ margin-left: {stag}rem; }}
@media (max-width: 860px) {{
  .hero-split-wrap {{ grid-template-columns: 1fr; }}
  .hero-split-visual {{ display: none; }}
}}""")

    else:  # centered
        lines.append(f"""
.hero {{ min-height: {v.hero_height}; }}""")

    # ── 7. Game gallery — only the chosen layout ──────────────────────────────
    thumb_h  = vi(168, 175, 275)
    gap_rem  = vf(172, 1.2, 2.6)

    if v.game_layout == "featured":
        feat_fr  = vf(176, 1.3, 1.95)
        sec_h    = vi(180, 155, 225)
        lines.append(f"""
.game-grid {{
  grid-template-columns: {feat_fr:.2f}fr 1fr;
  gap: {gap_rem:.2f}rem;
}}
.game-card-primary .game-card-thumb   {{ height: {thumb_h + vi(184,40,95)}px; }}
.game-card-secondary .game-card-thumb  {{ height: {sec_h}px; }}
@media (max-width: 760px) {{
  .game-grid {{ grid-template-columns: 1fr; }}
}}""")

    elif v.game_layout == "list":
        lw    = vi(176, 175, 290);  lh = vi(180, 115, 180)
        lpad  = vf(184, 1.2, 2.1);  litem_gap = vf(188, 1.3, 2.4)
        img_t = vf(192, 0.34, 0.56)
        lines.append(f"""
.game-grid {{
  display: flex; flex-direction: column;
  gap: {gap_rem:.2f}rem;
}}
.game-card {{
  display: flex; gap: {litem_gap:.1f}rem;
  align-items: center; padding: {lpad:.1f}rem;
  border-radius: var(--radius); overflow: visible;
}}
.game-card-thumb {{
  flex-shrink: 0;
  width: {lw}px; height: {lh}px;
  border-radius: var(--radius);
  overflow: hidden; border: 1px solid var(--card-border);
}}
.game-card-thumb img {{
  width: 100%; height: 100%; object-fit: cover;
  transition: transform {img_t:.2f}s ease;
}}
.game-card:hover .game-card-thumb img {{ transform: scale(1.06); }}
.game-card-body {{ flex: 1; }}
@media (max-width: 640px) {{
  .game-card {{ flex-direction: column; }}
  .game-card-thumb {{ width: 100%; height: 190px; }}
}}""")

    else:  # grid
        lines.append(f"""
.game-grid {{
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: {gap_rem:.2f}rem;
}}
.game-card-thumb {{ height: {thumb_h}px; }}""")

    # ── 8. Feature section — only the chosen layout ───────────────────────────
    f_gap = vf(196, 1.2, 2.3);  f_pad = vf(200, 1.3, 2.3)

    if v.feat_layout == "numbered":
        num_sz    = vf(204, 2.6, 4.4);  num_op = vf(208, 0.42, 0.68)
        num_ls    = vf(212, 0.03, 0.08);  num_mb = vf(216, 0.7, 1.4)
        num_trans = vf(220, 0.18, 0.36)
        lines.append(f"""
.features-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(270px, 1fr));
  gap: {f_gap:.2f}rem;
}}
.features-grid.features-count-3 {{
  grid-template-columns: repeat(3, minmax(0, 1fr));
}}
.features-grid.features-count-4 {{
  grid-template-columns: repeat(4, minmax(0, 1fr));
}}
.features-grid.features-count-6 {{
  grid-template-columns: repeat(3, minmax(0, 1fr));
}}
.feature-card {{ text-align: left; padding: {f_pad:.1f}rem; }}
.feature-number {{
  font-family: 'Space Grotesk', sans-serif;
  font-size: {num_sz:.1f}rem; font-weight: 800;
  line-height: 1; color: var(--accent);
  opacity: {num_op:.2f};
  letter-spacing: -{num_ls:.2f}em;
  margin-bottom: {num_mb:.1f}rem;
  transition: opacity {num_trans:.2f}s ease;
}}
.feature-card:hover .feature-number {{ opacity: 1; }}""")

    elif v.feat_layout == "horizontal":
        icon_sz   = vi(204, 56, 90);  horiz_min = vi(208, 310, 430)
        h_gap     = vf(212, 1.0, 1.7);  icon_rad = vi(216, 10, 20)
        h3_fs     = vf(220, 0.96, 1.16);  p_fs = vf(224, 0.87, 1.02)
        lines.append(f"""
.features-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax({horiz_min}px, 1fr));
  gap: {f_gap:.2f}rem;
}}
.features-grid.features-count-3 {{
  grid-template-columns: repeat(3, minmax(0, 1fr));
}}
.features-grid.features-count-4 {{
  grid-template-columns: repeat(4, minmax(0, 1fr));
}}
.features-grid.features-count-6 {{
  grid-template-columns: repeat(3, minmax(0, 1fr));
}}
.feature-horiz-card {{
  display: flex; align-items: flex-start; gap: {h_gap:.1f}rem;
  background: var(--card-bg);
  border: 1px solid var(--card-border); border-radius: var(--radius);
  padding: {f_pad:.1f}rem;
  backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
  transition: border-color var(--transition), transform var(--transition),
              box-shadow var(--transition);
}}
.feature-horiz-card:hover {{
  border-color: var(--accent);
  transform: translateY(-{vi(228,2,6)}px);
  box-shadow: var(--shadow);
}}
.feature-horiz-card .feature-icon {{
  width: {icon_sz}px; height: {icon_sz}px;
  border-radius: {icon_rad}px; flex-shrink: 0; margin: 0;
  overflow: hidden; border: 1px solid var(--card-border);
}}
.feature-horiz-body h3 {{ font-size: {h3_fs:.2f}rem; margin-bottom: 0.4rem; }}
.feature-horiz-body p  {{ color: var(--text-secondary); font-size: {p_fs:.2f}rem; line-height: 1.65; }}
@media (max-width: 640px) {{
  .features-grid {{ grid-template-columns: 1fr; }}
}}""")

    else:  # icons
        icon_sz  = vi(204, 60, 92);  icon_rad = vi(208, 12, 24)
        icon_mb  = vf(212, 1.0, 1.7)
        lines.append(f"""
.features-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: {f_gap:.2f}rem;
}}
.features-grid.features-count-3 {{
  grid-template-columns: repeat(3, minmax(0, 1fr));
}}
.features-grid.features-count-4 {{
  grid-template-columns: repeat(4, minmax(0, 1fr));
}}
.features-grid.features-count-6 {{
  grid-template-columns: repeat(3, minmax(0, 1fr));
}}
.feature-icon {{
  width: {icon_sz}px; height: {icon_sz}px;
  border-radius: {icon_rad}px; overflow: hidden;
  margin: 0 auto {icon_mb:.1f}rem;
  border: 1px solid var(--card-border);
}}""")

    # ── 9. Navbar — computed values per nav_style ─────────────────────────────
    lines.append(_build_nav_css(v, h, vi, vf))

    # ── 10. Footer — computed values per footer_style ─────────────────────────
    lines.append(_build_footer_css(v, h, vi, vf))

    # ── 11. Optional section CSS — only emitted if section is included ────────
    if "stats" in v.extra_sections:
        lines.append(_section_stats_css(h, vi, vf))
    if "testimonials" in v.extra_sections:
        lines.append(_section_testimonials_css(h, vi, vf))
    if "about" in v.extra_sections:
        lines.append(_section_about_css(h, vi, vf))
    if "cta_banner" in v.extra_sections:
        lines.append(_section_cta_css(h, vi, vf))

    # ── 12. Font family overrides from font_set ────────────────────────────────
    if hasattr(v, 'font_set') and isinstance(v.font_set, dict):
        fs = v.font_set
        lines.append(f"""
/* Font set: {fs.get('name', 'default')} */
body {{
  font-family: {fs['body_css']};
  font-size: {fs['body_size']};
  line-height: {fs['body_lh']};
}}
h1, h2, h3, h4 {{
  font-family: {fs['heading_css']};
  font-weight: {fs['h_weight']};
  letter-spacing: {fs['h_ls']};
}}
.navbar-brand, .navbar-brand span {{
  font-family: {fs['logo_css']};
  font-weight: {fs['logo_weight']};
}}
.hero-badge, .stat-number, .feature-number {{
  font-family: {fs['accent_css']};
}}""")

    # ── 13. Animation overrides from animation_set ────────────────────────────
    if hasattr(v, 'animation_set') and isinstance(v.animation_set, dict):
        from generator.variation_data.animations import ANIM_IN_KEYFRAMES, HOVER_CARD_EFFECTS
        anim = v.animation_set
        ain  = anim.get('anim_in', 'fade-up')
        dur  = anim.get('duration', '0.55s')
        ease = anim.get('easing',   'cubic-bezier(0.22, 1, 0.36, 1)')
        stag = anim.get('stagger',  '0.08s')
        _states = {
            'fade-up':    ('opacity:0;transform:translateY(24px)',  'opacity:1;transform:translateY(0)'),
            'fade-down':  ('opacity:0;transform:translateY(-24px)', 'opacity:1;transform:translateY(0)'),
            'fade-left':  ('opacity:0;transform:translateX(-28px)', 'opacity:1;transform:translateX(0)'),
            'fade-right': ('opacity:0;transform:translateX(28px)',  'opacity:1;transform:translateX(0)'),
            'zoom-in':    ('opacity:0;transform:scale(0.90)',       'opacity:1;transform:scale(1)'),
            'zoom-out':   ('opacity:0;transform:scale(1.10)',       'opacity:1;transform:scale(1)'),
            'flip-up':    ('opacity:0;transform:rotateX(-20deg) translateY(20px)', 'opacity:1;transform:rotateX(0) translateY(0)'),
            'blur-in':    ('opacity:0;filter:blur(14px)',           'opacity:1;filter:blur(0)'),
            'fade':       ('opacity:0',                             'opacity:1'),
            'rise':       ('opacity:0;transform:translateY(48px)',  'opacity:1;transform:translateY(0)'),
        }
        fi, fv = _states.get(ain, _states['fade-up'])
        if ain == 'blur-in':
            tr = f"transition:opacity {dur} {ease},filter {dur} {ease}"
        elif ain == 'fade':
            tr = f"transition:opacity {dur} {ease}"
        else:
            tr = f"transition:opacity {dur} {ease},transform {dur} {ease}"
        lines.append(f"""
/* Animation: {anim.get('name', 'default')} */
.fade-in {{ {fi};{tr}; }}
.fade-in.visible {{ {fv}; }}
.fade-in-delay-1 {{ transition-delay:{stag}; }}
.fade-in-delay-2 {{ transition-delay:calc({stag} * 2); }}
.fade-in-delay-3 {{ transition-delay:calc({stag} * 3); }}
.fade-in-delay-4 {{ transition-delay:calc({stag} * 4); }}
.fade-in-delay-5 {{ transition-delay:calc({stag} * 5); }}
.fade-in-delay-6 {{ transition-delay:calc({stag} * 6); }}""")
        hc = HOVER_CARD_EFFECTS.get(anim.get('hover_card', ''), '')
        if hc:
            ct2 = vf(350, 0.22, 0.35)
            lines.append(f"""
.card:hover,.game-card:hover,.feature-card:hover,.feature-horiz-card:hover {{
  {hc}
  transition:transform {ct2:.2f}s ease,box-shadow {ct2:.2f}s ease,filter {ct2:.2f}s ease;
}}""")

    return "\n".join(lines)


def _palette_priority_css(v: SiteVariant) -> str:
    """
    Re-assert palette variables after topic FX so topic animation packs do not
    overwrite the chosen batch palette.
    """
    p = v.palette if isinstance(v.palette, dict) else {}
    return f"""
:root {{
  --bg-primary:      {p.get('bg_page', '#080812')};
  --bg-secondary:    {p.get('bg_section', '#0f0f22')};
  --accent:          {p.get('primary', '#6c63ff')};
  --accent-hover:    {p.get('primary_h', '#8b84ff')};
  --accent-glow:     {p.get('glow', 'rgba(108,99,255,0.35)')};
  --secondary:       {p.get('secondary', '#2563eb')};
  --text:            {p.get('text', '#f0effe')};
  --text-secondary:  {p.get('text2', 'rgba(240,239,254,0.75)')};
  --text-muted:      {p.get('text3', 'rgba(240,239,254,0.50)')};
  --card-bg:         {p.get('card_bg', 'rgba(15,15,40,0.97)')};
  --card-border:     {p.get('border', 'rgba(108,99,255,0.22)')};
  --nav-bg:          {p.get('card_bg', 'rgba(15,15,40,0.97)')};
  --grad-a:          {p.get('grad_a', '#6c63ff')};
  --grad-b:          {p.get('grad_b', '#2563eb')};
  --glow:            {p.get('glow', 'rgba(108,99,255,0.35)')};
}}
"""


# ── Navbar CSS builder (parametric) ───────────────────────────────────────────

_NAV_FONTS = {
    "glass":   ("'Space Grotesk', 'Inter', sans-serif",  "'Inter', sans-serif"),
    "solid":   ("'Space Grotesk', sans-serif",            "'Inter', sans-serif"),
    "glow":    ("'Space Grotesk', sans-serif",            "'Inter', sans-serif"),
    "accent":  ("'Exo 2', 'Space Grotesk', sans-serif",   "'Exo 2', 'Inter', sans-serif"),
    "minimal": ("'Inter', sans-serif",                    "'Inter', sans-serif"),
    "bold":    ("'Orbitron', 'Space Grotesk', sans-serif","'Orbitron', 'Space Grotesk', sans-serif"),
}


def _nav_variant_overrides(v: SiteVariant, h: int, vi, vf, brand_font: str, link_font: str) -> str:
    """Apply the selected header/menu variant on top of the base nav style."""
    tall, short = v.header_height if isinstance(v.header_height, tuple) else (92, 64)
    bg_type = getattr(v, 'header_bg', 'glass')
    logo_pos = getattr(v, 'header_logo_pos', 'left')
    nav_style = getattr(v, 'header_nav_style', 'plain')
    border_style = getattr(v, 'header_border', 'none')
    scroll_behavior = getattr(v, 'header_scroll', 'shrink-smooth')
    menu_hover = getattr(v, 'menu_hover', 'underline-slide')
    menu_spacing = getattr(v, 'menu_spacing', 'normal')
    font_tx = getattr(v, 'header_font_tx', 'none')
    letter_sp = getattr(v, 'header_letter_sp', '0em')
    cta_style = getattr(v, 'header_cta', 'none')

    spacing_map = {"compact": "1.2rem", "normal": "2rem", "relaxed": "2.8rem", "wide": "3.6rem"}

    bg_css = {
        "transparent": ".navbar { background: transparent; backdrop-filter: none; -webkit-backdrop-filter: none; } .navbar.scrolled { background: rgba(8,8,20,0.94); }",
        "glass": "",
        "solid-dark": ".navbar, .navbar.scrolled { background: rgba(6,8,18,0.98); }",
        "gradient-v": ".navbar { background: linear-gradient(180deg, rgba(8,8,20,0.98) 0%, rgba(8,8,20,0.76) 72%, transparent 100%); }",
        "gradient-h": ".navbar { background: linear-gradient(90deg, color-mix(in srgb, var(--accent) 18%, rgba(8,8,20,0.96)) 0%, rgba(8,8,20,0.92) 50%, color-mix(in srgb, var(--grad-b) 14%, rgba(8,8,20,0.96)) 100%); }",
        "frosted": ".navbar, .navbar.scrolled { background: rgba(10,12,24,0.78); backdrop-filter: blur(22px) saturate(160%); -webkit-backdrop-filter: blur(22px) saturate(160%); }",
        "dark-tinted": ".navbar { background: color-mix(in srgb, var(--accent) 10%, rgba(8,8,20,0.94)); } .navbar.scrolled { background: color-mix(in srgb, var(--accent) 6%, rgba(8,8,20,0.99)); }",
        "accent-bar": ".navbar::before { display: block; height: 4px; opacity: 0.92; }",
    }.get(bg_type, "")

    border_css = {
        "none": ".navbar { border-bottom-color: transparent; }",
        "bottom-subtle": ".navbar { border-bottom: 1px solid rgba(255,255,255,0.08); }",
        "bottom-accent": ".navbar { border-bottom: 1px solid var(--accent); }",
        "bottom-gradient": ".navbar::after { content:''; position:absolute; left:0; right:0; bottom:0; height:1px; background:linear-gradient(90deg, transparent, var(--accent), var(--grad-b), transparent); }",
        "glow-bottom": ".navbar { border-bottom: 1px solid rgba(108,99,255,0.22); box-shadow: 0 10px 32px rgba(0,0,0,0.55), 0 1px 0 var(--accent), 0 8px 30px var(--accent-glow); }",
    }.get(border_style, "")

    scroll_css = {
        "shrink-smooth": ".navbar { transition: height 0.38s cubic-bezier(0.4, 0, 0.2, 1), background 0.50s ease, border-color 0.50s ease, box-shadow 0.50s ease; }",
        "shrink-fast": ".navbar { transition: height 0.18s ease-out, background 0.24s ease, border-color 0.24s ease, box-shadow 0.24s ease; }",
        "fade-bg-in": ".navbar { transition: background 0.45s ease, border-color 0.45s ease, box-shadow 0.45s ease, opacity 0.30s ease; }",
        "color-shift": ".navbar.scrolled { filter: saturate(1.12) hue-rotate(8deg); }",
        "static": f".navbar, .navbar.scrolled {{ height: {tall}px; }}",
    }.get(scroll_behavior, "")

    nav_style_css = {
        "plain": "",
        "pill-bg": ".nav-menu a { border-radius: 999px; padding: 0.45rem 0.85rem 0.5rem; } .nav-menu a::after { display:none; }",
        "underline": ".nav-menu a::after { bottom: -0.1rem; }",
        "overline": ".nav-menu a::after { top: -0.35rem; bottom: auto; }",
        "dot-sep": ".nav-menu li + li::before { content:'•'; color: var(--text-muted); margin-right: 1rem; } .nav-menu li { display:flex; align-items:center; }",
        "filled-btn": ".nav-menu a { padding: 0.5rem 0.95rem; border-radius: 999px; background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.08); } .nav-menu a::after { display:none; }",
        "ghost-btn": ".nav-menu a { padding: 0.5rem 0.95rem; border-radius: 999px; border: 1px solid var(--card-border); } .nav-menu a::after { display:none; }",
        "minimal": ".nav-menu a { opacity: 0.82; } .nav-menu a::after { display:none; }",
        "bold-caps": ".nav-menu a { font-weight: 800; text-transform: uppercase; } .nav-menu a::after { display:none; }",
        "gradient-text": ".nav-menu a:hover, .nav-menu a.active { background: linear-gradient(90deg, var(--accent), var(--grad-b)); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; } .nav-menu a::after { display:none; }",
        "slide-fill": ".nav-menu a { overflow:hidden; border-radius: 999px; padding: 0.45rem 0.8rem 0.5rem; } .nav-menu a::before { content:''; position:absolute; inset:auto 0 0 0; height:100%; background: rgba(255,255,255,0.08); transform: translateY(100%); transition: transform var(--transition); z-index:-1; } .nav-menu a:hover::before, .nav-menu a.active::before { transform: translateY(0); } .nav-menu a::after { display:none; }",
        "glow": ".nav-menu a:hover, .nav-menu a.active { color: var(--text); text-shadow: 0 0 18px var(--accent-glow); }",
    }.get(nav_style, "")

    hover_css = {
        "underline-slide": ".nav-menu a::after { width: 0; } .nav-menu a:hover::after, .nav-menu a.active::after { width: 100%; }",
        "fill-bg": ".nav-menu a:hover, .nav-menu a.active { background: rgba(255,255,255,0.08); color: var(--text); } .nav-menu a::after { display:none; }",
        "glow-text": ".nav-menu a:hover, .nav-menu a.active { color: var(--text); text-shadow: 0 0 16px var(--accent-glow); }",
        "scale-up": ".nav-menu a:hover, .nav-menu a.active { transform: scale(1.06); color: var(--text); } .nav-menu a { display:inline-block; }",
        "color-shift": ".nav-menu a:hover, .nav-menu a.active { color: var(--accent); }",
        "overline": ".nav-menu a::after { top: -0.4rem; bottom: auto; } .nav-menu a:hover::after, .nav-menu a.active::after { width: 100%; }",
        "bold-weight": ".nav-menu a:hover, .nav-menu a.active { color: var(--text); font-weight: 800; } .nav-menu a::after { display:none; }",
    }.get(menu_hover, "")

    # Keep the brand anchored on the left for every generated header layout.
    logo_css = {
        "left": "",
        "center": "",
        "right": "",
        "left-offset": "",
    }.get(logo_pos, "")

    cta_css = {
        "none": ".nav-cta { display:none; }",
        "outlined": ".nav-cta { background: transparent; color: var(--text); border-color: var(--card-border); }",
        "filled": ".nav-cta { background: var(--accent); color: #fff; border-color: var(--accent); box-shadow: 0 8px 22px var(--accent-glow); }",
        "gradient": ".nav-cta { background: linear-gradient(135deg, var(--grad-a), var(--grad-b)); color: #fff; }",
        "ghost-glow": ".nav-cta { background: transparent; color: var(--text); border-color: rgba(255,255,255,0.16); box-shadow: 0 0 20px rgba(255,255,255,0.05); } .nav-cta:hover { box-shadow: 0 0 30px var(--accent-glow); border-color: var(--accent); }",
    }.get(cta_style, "")

    return f"""
.navbar {{ min-height: {tall}px; }}
.navbar-brand {{ font-family: {brand_font}; text-transform: {font_tx}; letter-spacing: {letter_sp}; }}
.nav-menu {{ gap: {spacing_map.get(menu_spacing, "2rem")}; }}
.nav-menu a {{ font-family: {link_font}; text-transform: {font_tx}; letter-spacing: {letter_sp}; }}
.nav-cta {{ font-family: {link_font}; text-transform: {font_tx}; letter-spacing: {letter_sp}; }}
{bg_css}
{border_css}
{scroll_css}
{nav_style_css}
{hover_css}
{logo_css}
{cta_css}
@media (max-width: 768px) {{
  .navbar {{
    justify-content: space-between;
    gap: 0.75rem;
  }}
  .navbar-brand {{
    position: static;
    transform: none;
    margin-left: 0;
    margin-right: auto;
    max-width: calc(100% - 4.5rem);
  }}
  .navbar-brand span {{
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }}
  .navbar-logo-center .nav-menu, .navbar-logo-right .nav-menu {{ margin-right: 0; }}
  .nav-menu {{
    gap: 0;
  }}
  .nav-menu li {{
    display: block;
    width: 100%;
  }}
  .nav-menu li + li::before {{
    content: none;
    display: none;
  }}
  .nav-menu a {{
    display: block;
    width: 100%;
    transform: none;
    text-align: left;
    overflow: visible;
  }}
  .nav-menu a::before {{
    display: none;
    content: none;
  }}
  .nav-menu a::after {{
    display: none;
    content: none;
  }}
}}
"""


def _build_nav_css(v: SiteVariant, h: int, vi, vf) -> str:
    """Generate navbar CSS for this batch — height, bg, font, transitions."""
    # Prefer font_set fonts; fall back to nav_style lookup
    if hasattr(v, 'font_set') and isinstance(v.font_set, dict):
        brand_font = v.font_set['logo_css']
        link_font  = v.font_set['body_css']
    else:
        brand_font, link_font = _NAV_FONTS.get(v.nav_style, _NAV_FONTS["glass"])

    if v.nav_style == "glass":
        tall   = vi(232, 84, 104);  short = vi(236, 58, 72)
        t_bg   = vf(240, 0.48, 0.62);  t_blur = vi(244, 14, 24);  t_sat = vi(248, 140, 180)
        bdr_op = vf(252, 0.22, 0.38)
        return f"""
.navbar {{ height: {tall}px; }}
.navbar.scrolled {{
  height: {short}px;
  background: linear-gradient(180deg, rgba(10,10,26,{t_bg:.2f}) 0%, rgba(8,8,20,{t_bg-0.02:.2f}) 100%);
  backdrop-filter: blur({t_blur}px) saturate({t_sat}%);
  -webkit-backdrop-filter: blur({t_blur}px) saturate({t_sat}%);
  border-bottom-color: rgba(108,99,255,{bdr_op:.2f});
  box-shadow: 0 1px 0 rgba(108,99,255,{bdr_op*0.8:.2f}), 0 6px {vi(256,24,48)}px rgba(0,0,0,0.65);
}}
.navbar-brand {{ font-family: {brand_font}; font-size: {vf(260,1.32,1.55):.2f}rem; }}
.navbar.scrolled .navbar-brand {{ font-size: {vf(264,1.10,1.30):.2f}rem; }}
.nav-menu a {{ font-family: {link_font}; font-size: {vf(268,0.88,1.00):.2f}rem; }}""" + _nav_variant_overrides(v, h, vi, vf, brand_font, link_font)

    elif v.nav_style == "solid":
        tall   = vi(232, 74, 92);  short = vi(236, 54, 68)
        bg_a   = vf(240, 0.97, 1.0)
        bdr_op = vf(244, 0.25, 0.45);  sh_size = vi(248, 16, 40)
        ls     = vf(252, 0.00, 0.025)
        return f"""
.navbar {{
  height: {tall}px;
  background: linear-gradient(180deg, rgba(10,10,28,{bg_a:.2f}) 0%, rgba(6,6,18,{bg_a:.2f}) 100%);
  border-bottom: {1 + (h>>256)%2}px solid rgba(108,99,255,{bdr_op:.2f});
  box-shadow: 0 {vi(260,2,6)}px {sh_size}px rgba(0,0,0,0.72);
  backdrop-filter: blur({vi(264,10,18)}px);
  -webkit-backdrop-filter: blur({vi(264,10,18)}px);
}}
.navbar.scrolled {{
  height: {short}px;
  background: linear-gradient(180deg, rgba(6,6,18,1.0) 0%, rgba(4,4,14,1.0) 100%);
  box-shadow: 0 {vi(268,1,3)}px {vi(272,12,28)}px rgba(0,0,0,0.85);
}}
.navbar::before {{ display: none; }}
.navbar-brand {{ font-family: {brand_font}; font-size: {vf(276,1.24,1.46):.2f}rem; letter-spacing: {ls:.3f}em; }}
.navbar.scrolled .navbar-brand {{ font-size: {vf(280,1.06,1.26):.2f}rem; }}
.nav-menu a {{ font-family: {link_font}; font-size: {vf(284,0.88,1.00):.2f}rem; }}""" + _nav_variant_overrides(v, h, vi, vf, brand_font, link_font)

    elif v.nav_style == "glow":
        tall  = vi(232, 84, 104);  short = vi(236, 58, 72)
        glow_size = vi(240, 28, 60);  glow_outer = vi(244, 40, 80)
        bg_a  = vf(248, 0.88, 0.96);  blur = vi(252, 14, 24)
        return f"""
.navbar {{ height: {tall}px; }}
.navbar.scrolled {{
  height: {short}px;
  background: linear-gradient(180deg, rgba(10,10,26,{bg_a:.2f}) 0%, rgba(8,8,20,{bg_a-0.03:.2f}) 100%);
  border-bottom-color: var(--accent);
  backdrop-filter: blur({blur}px) saturate({vi(256,145,175)}%);
  -webkit-backdrop-filter: blur({blur}px) saturate({vi(256,145,175)}%);
  box-shadow:
    0 0 0 1px var(--accent),
    0 4px {glow_size}px var(--accent-glow),
    0 0 {glow_outer}px var(--accent-glow),
    0 8px 40px rgba(0,0,0,0.65);
}}
.navbar.scrolled::before {{ opacity: 1.0; }}
.navbar-brand img {{
  box-shadow: 0 0 0 {vi(260,1,3)}px var(--accent), 0 0 {vi(264,16,32)}px var(--accent-glow);
}}
.navbar-brand {{ font-family: {brand_font}; font-size: {vf(268,1.30,1.52):.2f}rem; }}
.navbar.scrolled .navbar-brand {{ font-size: {vf(272,1.10,1.30):.2f}rem; }}
.nav-menu a {{ font-family: {link_font}; font-size: {vf(276,0.90,1.02):.2f}rem; }}""" + _nav_variant_overrides(v, h, vi, vf, brand_font, link_font)

    elif v.nav_style == "accent":
        tall  = vi(232, 88, 108);  short = vi(236, 58, 74)
        ac_pct_tall  = vi(240, 16, 28);  ac_pct_short = vi(244, 10, 18)
        bg_a  = vf(248, 0.95, 0.99);  blur = vi(252, 12, 20)
        fs    = vf(256, 1.38, 1.58);  ls = vf(260, 0.01, 0.04)
        link_fs = vf(264, 0.88, 1.00);  link_ls = vf(268, 0.02, 0.06)
        return f"""
.navbar {{
  height: {tall}px;
  background: linear-gradient(135deg,
    color-mix(in srgb, var(--accent) {ac_pct_tall}%, rgba(10,10,26,{bg_a:.2f})) 0%,
    rgba(10,10,26,{bg_a:.2f}) 65%);
  border-bottom: 1px solid rgba(255,255,255,0.07);
  box-shadow: 0 4px {vi(272,28,52)}px rgba(0,0,0,0.52);
  backdrop-filter: blur({blur}px) saturate({vi(276,110,145)}%);
  -webkit-backdrop-filter: blur({blur}px) saturate({vi(276,110,145)}%);
}}
.navbar.scrolled {{
  height: {short}px;
  background: linear-gradient(135deg,
    color-mix(in srgb, var(--accent) {ac_pct_short}%, rgba(8,8,20,0.99)) 0%,
    rgba(8,8,20,0.99) 65%);
}}
.navbar::before {{
  height: {vi(280,2,4)}px;
  background: linear-gradient(90deg, transparent 0%, var(--accent) 20%, #fff 50%, var(--accent) 80%, transparent 100%);
  opacity: {vf(284,0.65,0.88):.2f};
}}
.navbar.scrolled::before {{ opacity: {vf(288,0.35,0.55):.2f}; }}
.navbar-brand {{
  font-family: {brand_font}; font-size: {fs:.2f}rem;
  font-weight: 800; font-style: italic; letter-spacing: {ls:.3f}em;
}}
.navbar.scrolled .navbar-brand {{ font-size: {vf(292,1.16,1.36):.2f}rem; }}
.navbar-brand span {{
  background: linear-gradient(135deg, #fff 0%, var(--accent-hover) 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}}
.nav-menu a {{
  font-family: {link_font}; color: rgba(255,255,255,{vf(296,0.78,0.92):.2f});
  font-weight: 600; font-size: {link_fs:.2f}rem;
  letter-spacing: {link_ls:.3f}em; text-transform: uppercase;
}}
.nav-menu a:hover, .nav-menu a.active {{ color: #fff; }}""" + _nav_variant_overrides(v, h, vi, vf, brand_font, link_font)

    elif v.nav_style == "minimal":
        tall  = vi(232, 60, 74);  short = vi(236, 50, 62)
        bg_a  = vf(240, 0.30, 0.52);  s_bg_a = vf(244, 0.76, 0.90)
        blur  = vi(248, 8, 16);  fs = vf(252, 0.96, 1.10)
        link_fs = vf(256, 0.80, 0.92);  link_ls = vf(260, 0.04, 0.09)
        img_sz  = vi(264, 26, 34)
        return f"""
.navbar {{
  height: {tall}px;
  background: rgba(8,8,20,{bg_a:.2f});
  border-bottom: 1px solid rgba(255,255,255,{vf(268,0.03,0.07):.2f});
  box-shadow: none;
}}
.navbar.scrolled {{
  height: {short}px;
  background: rgba(8,8,22,{s_bg_a:.2f});
  border-bottom-color: rgba(255,255,255,{vf(272,0.06,0.10):.2f});
  box-shadow: 0 1px {vi(276,8,20)}px rgba(0,0,0,0.42);
  backdrop-filter: blur({blur}px);
  -webkit-backdrop-filter: blur({blur}px);
}}
.navbar::before {{ display: none; }}
.navbar-brand {{
  font-family: {brand_font}; font-size: {fs:.2f}rem;
  font-weight: 600; letter-spacing: {vf(280,0.01,0.04):.3f}em;
}}
.navbar.scrolled .navbar-brand {{ font-size: {vf(284,0.90,1.04):.2f}rem; }}
.navbar-brand span {{
  background: none; -webkit-text-fill-color: var(--text); color: var(--text);
}}
.navbar-brand img {{
  width: {img_sz}px; height: {img_sz}px; border-radius: {vi(288,6,12)}px;
  box-shadow: none; border: 1px solid rgba(255,255,255,0.12);
}}
.navbar.scrolled .navbar-brand img {{ width: {img_sz-4}px; height: {img_sz-4}px; }}
.nav-menu {{ gap: {vf(292,1.4,2.2):.1f}rem; }}
.nav-menu a {{
  font-family: {link_font}; font-size: {link_fs:.2f}rem; font-weight: 400;
  color: rgba(200,200,222,{vf(296,0.50,0.70):.2f});
  letter-spacing: {link_ls:.3f}em; text-transform: uppercase;
}}
.nav-menu a::after {{ display: none; }}
.nav-menu a:hover {{ color: var(--text); }}
.nav-menu a.active {{ color: var(--accent); font-weight: 600; }}""" + _nav_variant_overrides(v, h, vi, vf, brand_font, link_font)

    else:  # bold
        tall  = vi(232, 96, 122);  short = vi(236, 58, 74)
        bdr   = vi(240, 2, 4);  sh = vi(244, 24, 44);  pad_h = vi(248, 24, 40)
        fs    = vf(252, 1.46, 1.80);  fs_s = vf(256, 1.10, 1.32)
        ls    = vf(260, 0.04, 0.10);  img_sz = vi(264, 46, 60)
        link_fs = vf(268, 0.74, 0.88);  link_ls = vf(272, 0.09, 0.15)
        return f"""
.navbar {{
  height: {tall}px;
  background: linear-gradient(180deg, rgba(18,12,36,0.99) 0%, rgba(10,8,24,0.99) 100%);
  border-bottom: {bdr}px solid var(--accent);
  padding: 0 {pad_h/10:.1f}rem;
  box-shadow: 0 4px {sh}px rgba(0,0,0,0.78);
}}
.navbar.scrolled {{
  height: {short}px;
  background: linear-gradient(180deg, rgba(10,8,24,1.0) 0%, rgba(6,4,16,1.0) 100%);
  border-bottom-width: {max(1, bdr-1)}px;
  padding: 0 {(pad_h-4)/10:.1f}rem;
}}
.navbar::before {{ display: none; }}
.navbar-brand {{
  font-family: {brand_font}; font-size: {fs:.2f}rem;
  font-weight: 700; letter-spacing: {ls:.3f}em; text-transform: uppercase;
}}
.navbar.scrolled .navbar-brand {{ font-size: {fs_s:.2f}rem; }}
.navbar-brand img {{ width: {img_sz}px; height: {img_sz}px; border-radius: {vi(276,12,18)}px; }}
.navbar.scrolled .navbar-brand img {{ width: {img_sz-16}px; height: {img_sz-16}px; border-radius: {vi(280,8,13)}px; }}
.navbar-brand span {{
  background: linear-gradient(90deg, var(--accent) 0%, #fff 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}}
.nav-menu a {{
  font-family: {link_font}; font-size: {link_fs:.2f}rem; font-weight: 600;
  letter-spacing: {link_ls:.3f}em; text-transform: uppercase;
  color: rgba(220,215,255,{vf(284,0.60,0.78):.2f});
}}
.nav-menu a:hover, .nav-menu a.active {{ color: var(--accent); }}""" + _nav_variant_overrides(v, h, vi, vf, brand_font, link_font)


# ── Footer CSS builder (parametric) ───────────────────────────────────────────

_FOOTER_BG: dict[str, str] = {
    "midnight": "rgba(6,6,18,0.98)",   "charcoal": "rgba(8,8,8,0.98)",
    "slate":    "rgba(7,9,18,0.98)",   "forest":   "rgba(4,10,6,0.98)",
    "volcanic": "rgba(12,5,4,0.98)",   "amethyst": "rgba(9,4,16,0.98)",
    "abyss":    "rgba(4,6,12,0.98)",   "onyx":     "rgba(8,7,8,0.98)",
}

_FOOTER_TITLE_FONTS = [
    "'Space Grotesk', sans-serif",
    "'Rajdhani', 'Inter', sans-serif",
    "'Exo 2', 'Inter', sans-serif",
    "'Inter', sans-serif",
    "'Orbitron', 'Space Grotesk', sans-serif",
]


def _build_footer_css(v: SiteVariant, h: int, vi, vf) -> str:
    # Derive footer bg from palette if available
    if hasattr(v, 'palette') and isinstance(v.palette, dict):
        _bp = v.palette.get('bg_page', '#060612')
        _r, _g, _b = int(_bp[1:3], 16), int(_bp[3:5], 16), int(_bp[5:7], 16)
        footer_bg = f"rgba({_r},{_g},{_b},0.98)"
    else:
        footer_bg = _FOOTER_BG.get(v.palette, "rgba(6,6,18,0.98)")
    pad_t = vf(288, 2.8, 5.8);  pad_s = vf(292, 1.5, 2.5);  pad_b = vf(296, 1.2, 2.4)
    # Use font_set logo font for footer titles if available
    if hasattr(v, 'font_set') and isinstance(v.font_set, dict):
        title_font = v.font_set['logo_css']
    else:
        title_font = _FOOTER_TITLE_FONTS[(h >> 300) % len(_FOOTER_TITLE_FONTS)]
    title_ls    = vf(304, 0.06, 0.16);  title_fs = vf(308, 0.72, 0.86)
    link_fs     = vf(312, 0.86, 1.00);  link_col_op = vf(316, 0.55, 0.78)
    brand_logo_fs = vf(320, 1.05, 1.45)

    base = f"""
.footer {{
  background: {footer_bg};
  padding: {pad_t:.1f}rem {pad_s:.1f}rem {pad_b:.1f}rem;
}}
.footer-brand-logo span {{
  font-family: {title_font}; font-size: {brand_logo_fs:.2f}rem;
}}
.footer-col-title {{
  font-family: {title_font};
  font-size: {title_fs:.2f}rem; font-weight: 700;
  letter-spacing: {title_ls:.3f}em; text-transform: uppercase;
}}
.footer-links a {{
  font-size: {link_fs:.2f}rem;
  color: rgba(196,194,224,{link_col_op:.2f});
}}
.footer-links a:hover {{ color: var(--text); }}"""

    if v.footer_style == "wide":
        bdr_w = vi(324, 1, 3)
        return base + f"""
.footer {{ border-top: {bdr_w}px solid var(--accent); }}
.footer-col-title {{ color: var(--accent); }}
.footer-links a:hover {{ color: var(--accent); padding-left: {vi(328,4,8)}px; transition: color {vf(332,0.18,0.30):.2f}s ease, padding-left {vf(332,0.18,0.30):.2f}s ease; }}"""

    elif v.footer_style == "centered":
        return base + f"""
.footer {{ border-top: 1px solid rgba(255,255,255,{vf(324,0.04,0.09):.2f}); }}
.footer-col-title {{ color: var(--text-muted); letter-spacing: {vf(328,0.12,0.20):.3f}em; }}"""

    elif v.footer_style == "compact":
        bdr_w = vi(324, 2, 4)
        return base + f"""
.footer {{ border-top: {bdr_w}px solid color-mix(in srgb, var(--accent) {int(vf(328,0.15,0.28) * 100)}%, transparent); }}
.footer-col-title {{
  color: var(--text);
  padding-bottom: {vf(332,0.4,0.7):.1f}rem;
  border-bottom: 1px solid rgba(255,255,255,{vf(336,0.06,0.12):.2f});
  margin-bottom: {vf(340,0.7,1.1):.1f}rem;
}}
.footer-bottom {{ border-top: 1px solid rgba(255,255,255,{vf(344,0.04,0.08):.2f}); padding-top: {vf(348,1.0,1.5):.1f}rem; }}"""

    else:  # standard
        return base + f"""
.footer {{ border-top: 1px solid color-mix(in srgb, var(--accent) {int(vf(324,0.12,0.28) * 100)}%, transparent); }}
.footer-col-title {{ color: var(--text-muted); }}"""


# ── Optional section CSS builders ─────────────────────────────────────────────

def _section_stats_css(h: int, vi, vf) -> str:
    cols   = 3 + (h >> 352) % 2   # 3 or 4 columns
    gap    = vf(356, 1.5, 3.0)
    num_fs = vf(360, 2.4, 3.8)
    return f"""
.stats-section {{ padding: {vf(364,3,6):.1f}rem 1.5rem; background: color-mix(in srgb, var(--accent) {int(vf(368,0.04,0.09) * 100)}%, transparent); }}
.stats-grid {{
  display: grid; grid-template-columns: repeat({cols}, 1fr);
  gap: {gap:.1f}rem; max-width: 1000px; margin: 0 auto;
  text-align: center;
}}
.stats-grid.stats-count-4 {{
  grid-template-columns: repeat(4, 1fr);
}}
.stat-item {{ padding: {vf(372,1.5,2.5):.1f}rem; }}
.stat-number {{
  font-family: 'Space Grotesk', sans-serif;
  font-size: {num_fs:.1f}rem; font-weight: 800;
  color: var(--accent); line-height: 1;
  margin-bottom: {vf(376,0.3,0.6):.1f}rem;
}}
.stat-label {{ font-size: {vf(380,0.86,1.0):.2f}rem; color: var(--text-secondary); }}
@media (max-width: 600px) {{
  .stats-grid {{ grid-template-columns: repeat(2,1fr); }}
}}"""


def _section_testimonials_css(h: int, vi, vf) -> str:
    cols = 3
    gap  = vf(384, 1.2, 2.2)
    return f"""
.testimonials-section {{ padding: {vf(388,4,8):.1f}rem 1.5rem; }}
.testimonials-grid {{
  display: grid; grid-template-columns: repeat(auto-fit, minmax({vi(392,260,320)}px, 1fr));
  gap: {gap:.1f}rem; max-width: 1100px; margin: 0 auto;
}}
.testimonial-card {{
  background: var(--card-bg); border: 1px solid var(--card-border);
  border-radius: var(--radius); padding: {vf(396,1.5,2.2):.1f}rem;
  position: relative;
}}
.testimonial-quote {{
  font-size: {vf(400,0.92,1.06):.2f}rem; color: var(--text-secondary);
  line-height: 1.75; margin-bottom: 1.2rem; font-style: italic;
}}
.testimonial-author {{
  font-weight: 700; font-size: 0.9rem; color: var(--accent);
}}
.testimonial-card::before {{
  content: '"'; position: absolute; top: -0.5rem; left: 1rem;
  font-size: {vi(404,3,6)}rem; color: var(--accent); opacity: 0.25;
  font-family: Georgia, serif; line-height: 1;
}}"""


def _section_about_css(h: int, vi, vf) -> str:
    return f"""
.about-section {{
  padding: {vf(408,4,8):.1f}rem 1.5rem;
  background: linear-gradient(180deg, color-mix(in srgb, var(--accent) {int(vf(412,0.05,0.11) * 100)}%, transparent) 0%, transparent 100%);
  border-bottom: 1px solid var(--card-border);
}}
.about-inner {{
  max-width: {vi(416,680,900)}px; margin: 0 auto; text-align: center;
}}
.about-inner h2 {{ font-size: clamp(1.6rem, 3.5vw, {vf(420,2.2,3.0):.1f}rem); margin-bottom: {vf(424,1.0,1.6):.1f}rem; }}
.about-inner p {{
  color: var(--text-secondary); font-size: {vf(428,1.0,1.15):.2f}rem;
  line-height: 1.8; max-width: 640px; margin: 0 auto;
}}"""


def _section_cta_css(h: int, vi, vf) -> str:
    return f"""
.cta-banner {{
  padding: {vf(432,3.5,6.5):.1f}rem 1.5rem;
  background: linear-gradient({vi(436,120,180)}deg,
    color-mix(in srgb, var(--accent) {vi(440,18,35)}%, rgba(8,8,22,0.98)) 0%,
    rgba(8,8,22,0.98) 100%);
  text-align: center;
  border-top: 1px solid color-mix(in srgb, var(--accent) {int(vf(444,0.20,0.40) * 100)}%, transparent);
  border-bottom: 1px solid color-mix(in srgb, var(--accent) {int(vf(448,0.20,0.40) * 100)}%, transparent);
}}
.cta-banner h2 {{
  font-size: clamp(1.6rem, 3.5vw, {vf(452,2.2,3.0):.1f}rem);
  margin-bottom: {vf(456,0.75,1.25):.2f}rem;
}}
.cta-banner p {{
  color: rgba(255,255,255,{vf(460,0.72,0.90):.2f});
  font-size: {vf(464,1.0,1.15):.2f}rem;
  max-width: 520px; margin: 0 auto {vf(468,1.5,2.5):.1f}rem;
}}"""


_FALLBACK_FONT_IMPORT = (
    "@import url('https://fonts.googleapis.com/css2?"
    "family=Inter:wght@300;400;500;600;700"
    "&family=Space+Grotesk:wght@400;500;600;700;800"
    "&family=Orbitron:wght@400;600;700;900"
    "&family=Rajdhani:wght@400;500;600;700"
    "&display=swap');"
)


def generate_css(container_opacity: float = 0.05,
                 topic:   str = "fantasy",
                 tone:    str = "dark",
                 variant = None) -> str:
    """
    Return the complete styles.css content.

    Parameters
    ----------
    container_opacity
        Accepted for backward compatibility; no longer affects card backgrounds.
    topic
        Injects a topic-specific effect pack (accent colour + animations).
    tone
        Reserved for future tone fine-tuning; currently unused.
    variant
        VariationConfig (or legacy SiteVariant): injects per-batch palette,
        fonts, layout, animation, and section overrides.
    """
    fx           = _TOPIC_CSS.get(topic, _TOPIC_CSS["fantasy"])
    var_css      = _variant_css(variant) if variant is not None else ""
    palette_css  = _palette_priority_css(variant) if variant is not None else ""
    font_imports = (
        variant.font_set["google_url"]
        if (variant is not None
            and hasattr(variant, "font_set")
            and isinstance(variant.font_set, dict))
        else _FALLBACK_FONT_IMPORT
    )
    return (
        _CSS_TEMPLATE
        .replace("[[FONT_IMPORTS]]", font_imports)
        .replace("[[VARIANT_CSS]]",  var_css)
        .replace("[[TOPIC_FX]]",     fx)
    ) + palette_css + GALLERY_CSS


# ═══════════════════════════════════════════════════════════════════════════════
#  JavaScript
# ═══════════════════════════════════════════════════════════════════════════════

_JS = r"""
/* ================================================================
   script.js — Whitepage Generator
   Cookie banner · Mobile menu · Contact form · Scroll animations
   ================================================================ */

'use strict';

/* ── Cookie banner ──────────────────────────────────────────────── */
(function () {
  var banner  = document.getElementById('cookie-banner');
  if (!banner) return;

  if (localStorage.getItem('wp_cookies') !== null) {
    banner.classList.add('hidden');
    return;
  }

  document.getElementById('btn-accept-cookies')
    && document.getElementById('btn-accept-cookies').addEventListener('click', function () {
      localStorage.setItem('wp_cookies', '1');
      banner.classList.add('hidden');
    });

  document.getElementById('btn-decline-cookies')
    && document.getElementById('btn-decline-cookies').addEventListener('click', function () {
      localStorage.setItem('wp_cookies', '0');
      banner.classList.add('hidden');
    });
}());


/* ── Mobile hamburger menu ──────────────────────────────────────── */
(function () {
  var btn  = document.getElementById('hamburger');
  var menu = document.getElementById('nav-menu');
  if (!btn || !menu) return;

  btn.addEventListener('click', function (e) {
    e.stopPropagation();
    var open = menu.classList.toggle('open');
    btn.classList.toggle('active', open);
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
  });

  document.addEventListener('click', function (e) {
    if (!btn.contains(e.target) && !menu.contains(e.target)) {
      menu.classList.remove('open');
      btn.classList.remove('active');
      btn.setAttribute('aria-expanded', 'false');
    }
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      menu.classList.remove('open');
      btn.classList.remove('active');
    }
  });
}());


/* ── Contact form — simulated submit ────────────────────────────── */
(function () {
  var form = document.getElementById('contact-form');
  if (!form) return;

  function showError(input, msgEl) {
    input.classList.add('is-invalid');
    if (msgEl) msgEl.classList.add('visible');
  }

  function clearError(input, msgEl) {
    input.classList.remove('is-invalid');
    if (msgEl) msgEl.classList.remove('visible');
  }

  ['name', 'email', 'message'].forEach(function (id) {
    var el = document.getElementById(id);
    if (el) el.addEventListener('input', function () {
      clearError(el, document.getElementById(id + '-err'));
    });
  });

  form.addEventListener('submit', function (e) {
    e.preventDefault();

    var nameEl    = document.getElementById('name');
    var emailEl   = document.getElementById('email');
    var messageEl = document.getElementById('message');
    var submitBtn = form.querySelector('button[type="submit"]');
    var success   = document.getElementById('form-success');
    var valid     = true;

    if (!nameEl.value.trim()) {
      showError(nameEl, document.getElementById('name-err'));
      valid = false;
    }

    var emailVal = emailEl.value.trim();
    if (!emailVal || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailVal)) {
      showError(emailEl, document.getElementById('email-err'));
      valid = false;
    }

    if (!messageEl.value.trim()) {
      showError(messageEl, document.getElementById('message-err'));
      valid = false;
    }

    if (!valid) return;

    submitBtn.disabled = true;
    submitBtn.textContent = 'Sending\u2026';

    setTimeout(function () {
      form.style.display = 'none';
      if (success) success.classList.add('visible');
    }, 1100);
  });
}());


/* ── Intersection-observer scroll fade-ins ──────────────────────── */
(function () {
  if (!window.IntersectionObserver) return;

  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

  document.querySelectorAll('.fade-in').forEach(function (el) {
    observer.observe(el);
  });
}());


/* ── Navbar shrink on scroll ────────────────────────────────────── */
(function () {
  var navbar = document.getElementById('navbar');
  if (!navbar) return;

  function update() {
    navbar.classList.toggle('scrolled', window.scrollY > 60);
  }

  window.addEventListener('scroll', update, { passive: true });
  update(); /* apply on load in case the page is already scrolled */
}());


/* ── Active nav link ────────────────────────────────────────────── */
(function () {
  var path     = window.location.pathname;
  var filename = path.split('/').pop() || 'index.php';
  if (filename === '') filename = 'index.php';

  document.querySelectorAll('.nav-menu a').forEach(function (a) {
    var href = (a.getAttribute('href') || '').split('#')[0];
    if (href === filename || (filename === 'index.php' && href === 'index.php')) {
      a.classList.add('active');
    }
  });
}());
""".strip()


def generate_js() -> str:
    """Return the complete script.js content."""
    return _JS


# ═══════════════════════════════════════════════════════════════════════════════
#  SVG Logo
# ═══════════════════════════════════════════════════════════════════════════════

def generate_logo_svg(brand_name: str, topic: str) -> str:
    """
    Generate a minimal SVG logo based on the first letter of the brand name
    and the topic colour palette.
    """
    # Accent colour per topic
    accent = {
        "fantasy":   "#6c63ff",
        "sci-fi":    "#00d4ff",
        "battle":    "#ff4d4d",
        "legend":    "#ffd700",
        "sports":    "#00e676",
        "horror":    "#9c27b0",
        "adventure": "#ff9800",
        "colorful":  "#ff4081",
    }.get(topic, "#6c63ff")

    letter = brand_name[0].upper() if brand_name else "W"

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="80" height="80" viewBox="0 0 80 80">
  <defs>
    <linearGradient id="lg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{accent}"/>
      <stop offset="100%" stop-color="{accent}88"/>
    </linearGradient>
  </defs>
  <rect width="80" height="80" rx="18" fill="url(#lg)"/>
  <text x="50%" y="55%" dominant-baseline="middle" text-anchor="middle"
        font-family="Segoe UI, system-ui, sans-serif"
        font-size="38" font-weight="800" fill="#ffffff"
        letter-spacing="-1">{letter}</text>
</svg>"""
