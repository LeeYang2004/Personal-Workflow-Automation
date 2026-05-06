from pathlib import Path

def get_credentials_path() -> Path:
    base_dir = Path(__file__).resolve().parent.parent
    return base_dir / "credentials.json"

def get_token_path() -> Path:
    base_dir = Path(__file__).resolve().parent.parent
    return base_dir / "token.json"

def get_log_path() -> Path:
    base_dir = Path(__file__).resolve().parent.parent
    return base_dir / "logs"