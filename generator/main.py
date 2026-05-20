"""
Pipeline orchestrator.

Wires together every module in the correct order:
  parse → validate → detect → scaffold → move → infer → generate text →
  generate images → save assets → build PHP → write CSS/JS → validate output
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

from generator.cli          import parse_args
from generator.config       import (
    HTDOCS_ROOT,
    DEFAULT_CONTAINER_OPACITY,
    DEFAULT_TOPIC,
    DEFAULT_TONE,
    TOPIC_KEYWORDS,
    TONE_KEYWORDS,
)
from generator.logger       import get_logger
from generator.game_detector import detect_games
from generator.file_manager  import (
    scaffold_directories,
    move_game_folders,
    write_text,
    write_binary,
)
from generator.ai_text      import generate_site_content, reset_openai_state as reset_openai_text_state
from generator.ai_image_safe import generate_all_images, reset_openai_state as reset_openai_image_state
from generator.template_engine import generate_css, generate_js, generate_logo_svg
from generator.php_generator   import PHPGenerator, build_context
from generator.validator    import validate_output
from generator.utils        import build_brand_name, infer_topic, infer_tone
from generator.variant      import pick_variant

log = get_logger("main")


def _reset_openai_generation_state() -> None:
    """Reset cached OpenAI clients and rotate fresh-generation tokens."""
    reset_openai_text_state()
    reset_openai_image_state()


def run(argv: list[str] | None = None) -> None:
    """
    Full generation pipeline.

    Parameters
    ----------
    argv
        If *None*, reads from ``sys.argv``.  Pass a list of strings to call
        programmatically (useful in tests and batch scripts).
    """
    # ── 1. Parse CLI ───────────────────────────────────────────────────────────
    args = parse_args(argv)
    log.info(f"{'=' * 60}")
    log.info(f"  Whitepage Generator — batch: {args.batch}")
    log.info(f"{'=' * 60}")

    # ── 2. Resolve batch directory ─────────────────────────────────────────────
    batch_dir = HTDOCS_ROOT / args.batch
    log.info(f"Batch dir  : {batch_dir}")

    if not batch_dir.exists():
        log.error(
            f"Batch directory not found: {batch_dir}\n"
            f"Create the folder and add exactly two game sub-directories."
        )
        sys.exit(1)

    # ── 3. Detect game folders (must be exactly 2) ─────────────────────────────
    try:
        game1, game2 = detect_games(batch_dir)
    except (FileNotFoundError, ValueError) as exc:
        log.error(str(exc))
        sys.exit(1)

    log.info(f"Game 1     : {game1.folder!r}  →  {game1.display_name!r}")
    log.info(f"Game 2     : {game2.folder!r}  →  {game2.display_name!r}")

    # ── 4. Infer or accept topic / tone / opacity ──────────────────────────────
    folders = [game1.folder, game2.folder]

    topic   = args.topic   or infer_topic(folders, TOPIC_KEYWORDS, DEFAULT_TOPIC)
    tone    = args.tone    or infer_tone(folders,  TONE_KEYWORDS,  DEFAULT_TONE)
    opacity = args.container_opacity if args.container_opacity is not None \
              else DEFAULT_CONTAINER_OPACITY

    log.info(f"Topic      : {topic}")
    log.info(f"Tone       : {tone}")
    log.info(f"Opacity    : {opacity}")

    # ── 4b. Pick deterministic site variant ───────────────────────────────────
    variant = pick_variant(
        args.batch,
        game_names=[game1.display_name, game2.display_name, game1.folder, game2.folder],
        topic=topic,
        tone=tone,
    )
    _pn = variant.palette["name"] if isinstance(variant.palette, dict) else repr(variant.palette)
    _tn = variant.theme["name"]   if isinstance(variant.theme,   dict) else repr(variant.theme)
    _gi = variant.gallery_item_layout.get("id", "?") if isinstance(variant.gallery_item_layout, dict) else "?"
    _gs = variant.gallery_section_layout.get("id", "?") if isinstance(variant.gallery_section_layout, dict) else "?"
    _hv = variant.header_variant.get("id", "?") if isinstance(getattr(variant, "header_variant", None), dict) else "?"
    _fv = variant.footer_variant.get("id", "?") if isinstance(getattr(variant, "footer_variant", None), dict) else "?"
    _mv = variant.menu_variant.get("id", "?") if isinstance(getattr(variant, "menu_variant", None), dict) else "?"
    log.info(f"Variant    : palette={_pn!r}  theme={_tn!r}  radius={variant.radius}px"
             f"  spacing={variant.spacing!r}  card={variant.card_style!r}"
             f"  hero={variant.hero_layout!r}  games={variant.game_layout!r}"
             f"  feat={variant.feat_layout!r}  typo={variant.typography!r}"
             f"  header={_hv}  footer={_fv}  menu={_mv}"
             f"  gallery=({_gs}, {_gi})  temp={variant.gpt_temp}")

    # ── 5. Scaffold directories ────────────────────────────────────────────────
    scaffold_directories(batch_dir)

    # ── 6. Move game folders into /games/ ─────────────────────────────────────
    try:
        move_game_folders(batch_dir, folders)
    except FileNotFoundError as exc:
        log.error(str(exc))
        sys.exit(1)

    # ── 7. Generate AI text content ────────────────────────────────────────────
    brand_hint = build_brand_name(args.batch)
    log.info(f"Brand hint : {brand_hint!r}")

    try:
        ai_content = generate_site_content(
            game1_name  = game1.display_name,
            game2_name  = game2.display_name,
            topic       = topic,
            tone        = tone,
            brand_hint  = brand_hint,
            temperature = variant.gpt_temp,
            persona     = variant.gpt_persona,
            theme       = variant.theme   if isinstance(variant.theme,   dict) else None,
            palette     = variant.palette if isinstance(variant.palette, dict) else None,
        )
    except Exception as exc:
        log.error(f"Text generation failed: {exc}", exc_info=True)
        sys.exit(1)

    brand_name = ai_content.get("brand_name", brand_hint)
    log.info(f"Brand name : {brand_name!r}")

    # ── 8. Generate AI images ──────────────────────────────────────────────────
    try:
        images = generate_all_images(
            game1_name      = game1.display_name,
            game2_name      = game2.display_name,
            topic           = topic,
            tone            = tone,
            brand_name      = brand_name,
            img_style       = variant.img_style,
            img_composition = variant.img_composition,
            theme           = variant.theme   if isinstance(variant.theme,   dict) else None,
            palette         = variant.palette if isinstance(variant.palette, dict) else None,
        )
    except Exception as exc:
        log.error(f"Image generation failed: {exc}", exc_info=True)
        sys.exit(1)

    # ── 9. Save images ─────────────────────────────────────────────────────────
    img_dir  = batch_dir / "assets" / "images"
    icon_dir = batch_dir / "assets" / "icons"

    write_binary(img_dir / "hero.jpg",       images.hero)
    write_binary(img_dir / "background.jpg", images.background)

    icon_paths: list[str] = []
    for idx, icon_bytes in enumerate(images.icons, 1):
        fname = f"icon_{idx}.png"
        write_binary(icon_dir / fname, icon_bytes)
        icon_paths.append(f"assets/icons/{fname}")

    # ── 10. Save logo (AI-generated PNG + SVG fallback) ───────────────────────
    write_binary(icon_dir / "logo.png", images.logo)
    # SVG fallback is still written as logo.svg for the <link rel="icon">
    logo_svg = generate_logo_svg(brand_name, topic)
    write_text(icon_dir / "logo.svg", logo_svg)

    # ── 11. Assemble SiteContext ───────────────────────────────────────────────
    ctx = build_context(
        batch_name   = args.batch,
        brand_name   = brand_name,
        topic        = topic,
        tone         = tone,
        current_year = datetime.now().year,
        game1_folder = game1.folder,
        game1_name   = game1.display_name,
        game1_banner = game1.banner_image,
        game2_folder = game2.folder,
        game2_name   = game2.display_name,
        game2_banner = game2.banner_image,
        icon_paths   = icon_paths,
        ai_content   = ai_content,
        variant      = variant,
    )

    # ── 12. Generate PHP files ─────────────────────────────────────────────────
    log.info("Building PHP files…")
    try:
        PHPGenerator(ctx).write_all(batch_dir)
    except Exception as exc:
        log.error(f"PHP generation failed: {exc}", exc_info=True)
        sys.exit(1)

    # ── 13. Generate CSS + JS ──────────────────────────────────────────────────
    write_text(batch_dir / "styles.css", generate_css(opacity, topic=topic, tone=tone, variant=variant))
    write_text(batch_dir / "script.js",  generate_js())
    log.info("CSS and JS written")

    # ── 14. Validate output ────────────────────────────────────────────────────
    try:
        warnings = validate_output(batch_dir, folders)
    except RuntimeError as exc:
        log.error(str(exc))
        sys.exit(1)

    # ── 15. Done ───────────────────────────────────────────────────────────────
    log.info(f"{'=' * 60}")
    log.info(f"  Generation complete!")
    log.info(f"  Site URL : http://localhost/{args.batch}/")
    log.info(f"  Files in : {batch_dir}")
    if warnings:
        log.info(f"  Warnings : {len(warnings)} (see above)")
    log.info(f"{'=' * 60}")
    _reset_openai_generation_state()
    log.info("  OpenAI generation state reset")


# ── Batch processing helper ────────────────────────────────────────────────────

def run_batch(batch_names: list[str], **kwargs: str) -> None:
    """
    Run the pipeline for multiple batches sequentially.

    Extra keyword arguments are converted to CLI-style ``--key value`` pairs
    and appended to each invocation's argument list.

    Example::

        run_batch(
            ['dragon-arena', 'space-duo'],
            topic='fantasy',
            tone='dark',
        )
    """
    extra: list[str] = []
    for key, value in kwargs.items():
        extra.extend([f"--{key}", str(value)])

    for name in batch_names:
        log.info(f"\n{'─' * 60}")
        log.info(f"  Starting batch: {name}")
        log.info(f"{'─' * 60}")
        try:
            run(["--batch", name] + extra)
        finally:
            _reset_openai_generation_state()
