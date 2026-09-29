import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent


def load_local_env():
    """Load .env values without replacing variables already provided by the host."""
    env_file = PROJECT_ROOT / ".env"
    if not env_file.exists():
        return

    for line in env_file.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and value and key not in os.environ:
            os.environ[key] = value
