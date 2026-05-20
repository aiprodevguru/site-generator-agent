"""
Central configuration — paths, API settings, lookup tables, and constants.

Every module imports what it needs from here.  Nothing is hard-coded elsewhere.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the project root (two levels up from this file)
_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_ENV_PATH)


def _env_flag(name: str, default: bool) -> bool:
    """Parse boolean env vars without forcing callers to normalize values."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}

# ── Paths ──────────────────────────────────────────────────────────────────────
HTDOCS_ROOT: Path = Path(os.getenv("HTDOCS_ROOT", "C:/xampp/htdocs"))

# ── OpenAI ─────────────────────────────────────────────────────────────────────
OPENAI_API_KEY:         str = os.getenv("OPENAI_API_KEY", "")
OPENAI_TEXT_MODEL:      str = os.getenv("OPENAI_TEXT_MODEL", "")
OPENAI_TEXT_MODEL_PRIMARY: str = os.getenv(
    "OPENAI_TEXT_MODEL_PRIMARY",
    OPENAI_TEXT_MODEL or "gpt-5-mini",
)
OPENAI_TEXT_MODEL_FALLBACK: str = os.getenv(
    "OPENAI_TEXT_MODEL_FALLBACK",
    "gpt-5.4-mini",
)
OPENAI_TEXT_ENABLE_FALLBACK: bool = _env_flag("OPENAI_TEXT_ENABLE_FALLBACK", True)
OPENAI_TEXT_USE_JSON_SCHEMA: bool = _env_flag("OPENAI_TEXT_USE_JSON_SCHEMA", True)
OPENAI_IMAGE_MODEL:     str = os.getenv("OPENAI_IMAGE_MODEL", "dall-e-3")
OPENAI_IMAGE_SIZE_HERO: str = "1792x1024"    # wide landscape for hero
OPENAI_IMAGE_SIZE_STD:  str = "1024x1024"    # backgrounds, icons
OPENAI_IMAGE_QUALITY:   str = os.getenv("OPENAI_IMAGE_QUALITY", "standard")

# ── Resilience ─────────────────────────────────────────────────────────────────
MAX_RETRIES:    int   = 3
RETRY_BACKOFF:  float = 2.0    # seconds; doubled each attempt

# ── Site defaults ──────────────────────────────────────────────────────────────
DEFAULT_CONTAINER_OPACITY: float = 0.05   # rgba alpha for card backgrounds

# ── Banned words (gambling / real-money) ──────────────────────────────────────
BANNED_WORDS: list[str] = [
    "casino", "bet", "betting", "spin", "spinning",
    "gambling", "gamble", "bonus", "real money", "real-money",
    "jackpot", "wager", "wagering", "stake", "staking",
    "odds", "payout", "winnings", "slot machine", "roulette",
    "poker", "blackjack", "baccarat", "craps", "keno",
    "cashout", "cash out", "withdraw", "deposit funds",
]

# ── Topic inference keyword map ────────────────────────────────────────────────
TOPIC_KEYWORDS: dict[str, str] = {
    # fantasy
    "dragon":   "fantasy",  "quest":    "fantasy",  "wizard":   "fantasy",
    "magic":    "fantasy",  "knight":   "fantasy",  "elf":      "fantasy",
    "dwarf":    "fantasy",  "sorcerer": "fantasy",  "castle":   "fantasy",
    # legend
    "legend":   "legend",   "myth":     "legend",   "hero":     "legend",
    "epic":     "legend",   "saga":     "legend",   "titan":    "legend",
    "oracle":   "legend",   "deity":    "legend",
    # sci-fi
    "space":    "sci-fi",   "blast":    "sci-fi",   "galactic": "sci-fi",
    "star":     "sci-fi",   "cyber":    "sci-fi",   "robot":    "sci-fi",
    "alien":    "sci-fi",   "neon":     "sci-fi",   "laser":    "sci-fi",
    "mech":     "sci-fi",   "quantum":  "sci-fi",   "nova":     "sci-fi",
    # battle
    "warrior":  "battle",   "clash":    "battle",   "combat":   "battle",
    "war":      "battle",   "strike":   "battle",   "arena":    "battle",
    "siege":    "battle",   "assault":  "battle",   "blitz":    "battle",
    # sports
    "soccer":   "sports",   "football": "sports",   "race":     "sports",
    "turbo":    "sports",   "champion": "sports",   "speed":    "sports",
    "league":   "sports",   "trophy":   "sports",
    # horror
    "horror":   "horror",   "dead":     "horror",   "ghost":    "horror",
    "zombie":   "horror",   "crypt":    "horror",   "blood":    "horror",
    "shadow":   "horror",   "cursed":   "horror",   "demon":    "horror",
    # adventure
    "jungle":   "adventure","treasure": "adventure","pirate":   "adventure",
    "safari":   "adventure","explore":  "adventure","voyage":   "adventure",
    "island":   "adventure","relic":    "adventure",
    # colorful
    "fruit":    "colorful", "candy":    "colorful", "jewel":    "colorful",
    "rainbow":  "colorful", "gem":      "colorful", "pop":      "colorful",
    "bubble":   "colorful", "sparkle":  "colorful",
    # rpg
    "rpg":      "rpg",      "dungeon":  "rpg",      "guild":    "rpg",
    "tavern":   "rpg",      "scroll":   "rpg",      "rune":     "rpg",
    "forge":    "rpg",      "realm":    "rpg",      "lore":     "rpg",
    # strategy
    "strategy": "strategy", "empire":   "strategy", "command":  "strategy",
    "dominion": "strategy", "conquest": "strategy", "fortress": "strategy",
    "throne":   "strategy", "general":  "strategy", "marshal":  "strategy",
    # puzzle
    "puzzle":   "puzzle",   "maze":     "puzzle",   "riddle":   "puzzle",
    "enigma":   "puzzle",   "cipher":   "puzzle",   "lock":     "puzzle",
    "brain":    "puzzle",   "logic":    "puzzle",
    # arcade
    "arcade":   "arcade",   "retro":    "arcade",   "pixel":    "arcade",
    "bit":      "arcade",   "8bit":     "arcade",   "classic":  "arcade",
    "coin":     "arcade",   "joystick": "arcade",
    # racing
    "racing":   "racing",   "drift":    "racing",   "rally":    "racing",
    "nitro":    "racing",   "lap":      "racing",   "podium":   "racing",
    "gran":     "racing",   "prix":     "racing",
}

# ── Tone inference keyword map ─────────────────────────────────────────────────
TONE_KEYWORDS: dict[str, str] = {
    "dragon":   "fierce",   "fire":     "fierce",   "war":      "fierce",
    "clash":    "fierce",   "blast":    "fierce",   "strike":   "fierce",
    "combat":   "fierce",   "siege":    "fierce",   "assault":  "fierce",
    "space":    "dark",     "shadow":   "dark",     "night":    "dark",
    "zombie":   "dark",     "horror":   "dark",     "dead":     "dark",
    "cyber":    "dark",     "crypt":    "dark",     "cursed":   "dark",
    "demon":    "dark",     "abyss":    "dark",
    "candy":    "colorful", "fruit":    "colorful", "rainbow":  "colorful",
    "jewel":    "colorful", "gem":      "colorful", "pop":      "colorful",
    "bubble":   "colorful", "sparkle":  "colorful",
    "legend":   "warm",     "hero":     "warm",     "quest":    "warm",
    "treasure": "warm",     "safari":   "warm",     "relic":    "warm",
    "neon":     "neon",     "laser":    "neon",     "pixel":    "neon",
    "arcade":   "neon",     "retro":    "neon",     "bit":      "neon",
    "nova":     "neon",     "electro":  "neon",
    "epic":     "epic",     "titan":    "epic",     "dominion": "epic",
    "conquest": "epic",     "throne":   "epic",     "saga":     "epic",
    "empire":   "epic",     "grand":    "epic",
}

DEFAULT_TOPIC: str = "fantasy"
DEFAULT_TONE:  str = "dark"

# ── Icon subjects per topic (10–12 options each for maximum variety) ──────────
ICON_SUBJECTS: dict[str, list[str]] = {
    "fantasy": [
        "enchanted sword glowing blue",        "ancient leather-bound magic tome",
        "bubbling luminous potion bottle",     "cracked dragon egg with golden cracks",
        "iron round shield with embossed crest","jewelled golden crown",
        "wizard staff with crystal orb",       "mystical amulet on chain",
        "glowing rune stone tablet",           "silver elven dagger",
        "wooden wand with sparkling tip",      "treasure chest overflowing with gold",
    ],
    "sci-fi": [
        "chrome rocket ship",                  "neon-outlined laser cannon",
        "glowing alien crystal shard",         "holographic circuit board chip",
        "reflective chrome space helmet",      "star navigation map hologram",
        "cybernetic robotic arm",              "plasma energy cell battery",
        "hovering surveillance drone",         "quantum teleport pad",
        "warp core reactor",                   "neural interface headset",
    ],
    "battle": [
        "crossed swords forming an X",         "war drum with tribal markings",
        "double-headed battle axe",            "armoured gauntlet fist",
        "spiked mace with chain",              "championship victory trophy",
        "knights full-face visor helmet",      "circular war shield with spikes",
        "throwing javelin",                    "iron-tipped crossbow bolt",
        "siege catapult",                      "warrior chest-plate armour",
    ],
    "legend": [
        "ancient rolled parchment scroll",     "legendary glowing gemstone",
        "flowing hero cape",                   "golden navigator's compass",
        "blazing torch flame",                 "championship gold medal",
        "oracle crystal sphere",               "god statue carved in stone",
        "sacred golden chalice",               "ancient prophecy tablet",
        "constellation star map",              "divine lightning bolt",
    ],
    "sports": [
        "gleaming gold trophy cup",            "electric lightning bolt",
        "chequered finish-line flag",          "white-panelled soccer ball",
        "gold olympic medal on ribbon",        "precision stopwatch",
        "starting pistol",                     "athletes running shoes",
        "scoreboard display panel",            "referee whistle",
        "sports laurel wreath",                "podium first-place block",
    ],
    "horror": [
        "grinning human skull",                "outstretched bat wings",
        "rust-stained haunted lantern",        "dripping spider web",
        "blood-red crescent moon",             "broken human bone",
        "cracked and oozing zombie hand",      "flickering melted candle",
        "iron coffin lid",                     "bubbling green cauldron",
        "torn ghost shroud",                   "hourglass with black sand",
    ],
    "adventure": [
        "overflowing treasure chest",          "spinning compass rose",
        "coiled climbing rope",                "aged treasure map",
        "flaming wooden torch",                "rusted ships anchor",
        "binoculars with leather strap",       "pith explorer's hat",
        "rolled-up jungle map",                "ancient temple doorway",
        "carved wooden totem pole",            "crocodile tooth necklace",
    ],
    "colorful": [
        "glowing four-leaf clover",            "shooting star with sparkle trail",
        "vibrant double rainbow arc",          "brilliant cut diamond gem",
        "zigzag neon lightning bolt",          "tropical hibiscus flower",
        "spinning top toy",                    "candy swirl lollipop",
        "party confetti explosion",            "bright balloon bouquet",
        "kaleidoscope prism crystal",          "retro lava lamp",
    ],
    "rpg": [
        "leather-bound spellbook with lock",   "iron dungeon door key",
        "flaming magic fireball spell",        "potion rack with coloured vials",
        "guild crest emblem shield",           "carved rune stone slab",
        "enchanted blacksmith anvil",          "glowing mana crystal orb",
        "ornate dagger with jewelled hilt",    "tavern tankard overflowing",
        "character level-up star burst",       "monster claw gauntlet",
    ],
    "strategy": [
        "stone fortress tower battlement",     "military command flag",
        "tactical map with pins",              "war elephant silhouette",
        "bronze general's helmet",             "crossed cannon barrels",
        "wooden catapult arm",                 "medieval siege ladder",
        "stone throne with crown",             "compass over territory map",
        "troop formation chess knight",        "armistice scroll and quill",
    ],
    "puzzle": [
        "interlocking jigsaw puzzle piece",    "illuminated maze overhead view",
        "glowing light bulb idea",             "rotating combination lock dial",
        "stacked wooden blocks",               "magnifying glass over clues",
        "abacus counting beads",               "logic circuit node diagram",
        "cryptic keyhole and key",             "geometric origami shape",
        "rubik's cube face",                   "hourglass timer running out",
    ],
    "arcade": [
        "retro joystick controller",           "classic arcade cabinet front",
        "pixel-art coin spinning",             "8-bit spaceship sprite",
        "neon high score display",             "pixel explosion burst",
        "cartridge game cassette",             "retro D-pad button cross",
        "CRT monitor scanline screen",         "laser blaster gun",
        "power-up star pickup",                "life hearts row display",
    ],
    "racing": [
        "trophy checkered flag",               "speedometer dial at max",
        "slick racing tyre",                   "nitro boost flame exhaust",
        "racing helmet with visor",            "podium first-place trophy",
        "pit stop wheel wrench",               "steering wheel with grip",
        "starting traffic light",              "racing gloves pair",
        "spoiler rear wing carbon",            "fuel gauge near empty",
    ],
}

# ── Required output files (for validation) ─────────────────────────────────────
REQUIRED_OUTPUT_FILES: list[str] = [
    "index.php",
    "game.php",
    "game_proxy.php",
    "contact.php",
    "terms.php",
    "privacy.php",
    "cookie.php",
    "styles.css",
    "script.js",
    "partials/header.php",
    "partials/footer.php",
    "assets/images/hero.jpg",
    "assets/images/background.jpg",
]
