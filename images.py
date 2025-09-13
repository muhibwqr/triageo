# images.py
import random
from pathlib import Path

# Path to the assets folder relative to this file
ASSET_DIR = Path(__file__).parent / "assets"

def pick_random_image() -> str | None:
    """
    Return the absolute path of a random file named asset1..asset15
    inside the assets/ folder. Returns None if none found.
    """
    if not ASSET_DIR.exists():
        return None

    # Only allow asset1..asset15 (case-insensitive)
    allowed_names = {f"asset{i}" for i in range(1, 16)}  # asset1..asset15
    imgs = []
    for p in ASSET_DIR.iterdir():
        stem = p.stem.lower()  # filename without extension
        if stem in allowed_names and p.suffix.lower() in (".png", ".jpg", ".jpeg", ".gif"):
            imgs.append(p)

    if not imgs:
        return None
    return str(random.choice(imgs))
