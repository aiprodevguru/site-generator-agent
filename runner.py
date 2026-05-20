import os
import random
import shutil
import subprocess
from pathlib import Path

# CONFIG
GAMES_DIR = Path(r"E:\games")
XAMPP_DIR = Path(r"C:\xampp\htdocs")
DOMAIN_FILE = Path("domains.txt")
FAILED_FILE = Path("failed_domains.txt")
GAME_COUNT_PER_DOMAIN = 2


def load_next_domain(file_path: Path):
    """
    Reads the first domain from file and returns:
    (next_domain, remaining_domains)
    """
    if not file_path.exists():
        return None, []

    with file_path.open("r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    if not lines:
        return None, []

    return lines[0], lines[1:]


def get_game_folders():
    return [p for p in GAMES_DIR.iterdir() if p.is_dir()]


def copy_games(selected_games, target_folder: Path):
    """
    Copy games instead of moving so they can be reused.
    """
    target_folder.mkdir(parents=True, exist_ok=True)

    for game in selected_games:
        dest = target_folder / game.name
        print(f"Copying {game} -> {dest}")
        shutil.copytree(game, dest, dirs_exist_ok=True)


def run_generator(domain: str) -> bool:
    """
    Runs generator script and returns True if successful.
    """
    print(f"Running generator for {domain} ...")

    result = subprocess.run(
        ["python", "generate_whitepage.py", "--batch", domain],
        capture_output=True,
        text=True
    )

    print(result.stdout)

    if result.returncode != 0:
        print(f"[ERROR] Generator failed for {domain}")
        print(result.stderr)
        return False

    return True


def save_failed_domain(domain: str):
    """
    Append failed domain to file.
    """
    with FAILED_FILE.open("a", encoding="utf-8") as f:
        f.write(domain + "\n")


def main():
    while True:
        domain, remaining = load_next_domain(DOMAIN_FILE)

        if not domain:
            print("No more domains to process.")
            break

        print(f"\n===== Processing domain: {domain} =====")

        games = get_game_folders()

        if len(games) < GAME_COUNT_PER_DOMAIN:
            print("Not enough game folders left to continue.")
            break

        selected = random.sample(games, GAME_COUNT_PER_DOMAIN)
        domain_folder = XAMPP_DIR / domain

        # STEP 1: Copy games
        copy_games(selected, domain_folder)

        # STEP 2: Run generator
        success = run_generator(domain)

        # STEP 3: Update domain lists
        if success:
            with DOMAIN_FILE.open("w", encoding="utf-8") as f:
                f.write("\n".join(remaining))
            print(f"[OK] Completed domain: {domain}")
        else:
            print(f"[FAIL] Saving failed domain: {domain}")
            save_failed_domain(domain)


if __name__ == "__main__":
    main()