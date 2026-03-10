#!/usr/bin/env python3
"""Recover ME_CAM login access on a device.

Usage examples:
  python3 scripts/recover_login.py --username owner --password 'NewStrongPass123!'
  python3 scripts/recover_login.py --username owner --password 'NewStrongPass123!' --rotate-key
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

from werkzeug.security import generate_password_hash


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Recover ME_CAM login credentials")
    parser.add_argument("--username", required=True, help="Username to create/update")
    parser.add_argument("--password", required=True, help="New password (min 8 chars)")
    parser.add_argument(
        "--config",
        default="config/config.json",
        help="Path to config.json (default: config/config.json)",
    )
    parser.add_argument(
        "--users",
        default="config/users.json",
        help="Path to users.json (default: config/users.json)",
    )
    parser.add_argument(
        "--rotate-key",
        action="store_true",
        help="Rotate customer enrollment key",
    )
    return parser.parse_args()


def load_json(path: Path, default):
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)
        handle.write("\n")


def new_security_key() -> str:
    import secrets

    raw = secrets.token_hex(10).upper()
    groups = [raw[i:i + 4] for i in range(0, 20, 4)]
    return "-".join(groups)


def backup(path: Path) -> None:
    if not path.exists():
        return
    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    bkp = path.with_suffix(path.suffix + f".bak_{stamp}")
    bkp.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")


def main() -> int:
    args = parse_args()

    username = args.username.strip()
    password = args.password

    if len(username) < 3:
        raise SystemExit("Error: username must be at least 3 characters")
    if len(password) < 8:
        raise SystemExit("Error: password must be at least 8 characters")

    config_path = Path(args.config)
    users_path = Path(args.users)

    cfg = load_json(config_path, {})
    users = load_json(users_path, {})

    backup(config_path)
    backup(users_path)

    users[username] = {
        "password_hash": generate_password_hash(password),
        "pin": "1234",
        "role": "user",
    }

    security = dict(cfg.get("security") or {})
    security["bootstrap_required"] = False
    security["bootstrap_admin"] = ""

    if args.rotate_key or not security.get("enrollment_key"):
        security["enrollment_key"] = new_security_key()
        security["enrollment_key_updated_at"] = datetime.utcnow().isoformat()
        security["enrollment_key_reason"] = "recovery"

    cfg["security"] = security
    cfg["first_run_completed"] = True

    save_json(users_path, users)
    save_json(config_path, cfg)

    print("Login recovery applied")
    print(f"Username: {username}")
    print("Password: (updated)")
    print(f"bootstrap_required: {security.get('bootstrap_required')}")
    print(f"Enrollment key: {security.get('enrollment_key', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
