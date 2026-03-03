#!/usr/bin/env python3
import argparse
import datetime as dt
from pathlib import Path

BOOT_CONFIG = Path('/boot/firmware/config.txt')

SUPPORTED = {
    'auto': {
        'camera_auto_detect': '1',
        'overlay': None,
        'label': 'Auto-detect (switch-safe)'
    },
    'imx519': {
        'camera_auto_detect': '0',
        'overlay': 'imx519',
        'label': 'Arducam IMX519'
    },
    'ov5647': {
        'camera_auto_detect': '0',
        'overlay': 'ov5647',
        'label': 'OV5647'
    },
    'ov547': {
        'camera_auto_detect': '0',
        'overlay': 'ov547',
        'label': 'OV547'
    },
}

OVERLAY_PREFIXES = (
    'dtoverlay=imx519',
    'dtoverlay=ov5647',
    'dtoverlay=ov547',
    'dtoverlay=imx219',
    'dtoverlay=imx708',
)


def backup_config(path: Path) -> Path:
    stamp = dt.datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    backup = path.with_name(f'config.txt.mecam_backup_{stamp}')
    backup.write_text(path.read_text())
    return backup


def apply_profile(path: Path, profile: str) -> None:
    cfg = SUPPORTED[profile]
    lines = path.read_text().splitlines()

    cleaned = []
    for line in lines:
        s = line.strip()
        if s.startswith('camera_auto_detect='):
            continue
        if s.startswith('gpu_mem=128'):
            continue
        if any(s.startswith(prefix) for prefix in OVERLAY_PREFIXES):
            continue
        cleaned.append(line)

    cleaned.append('')
    cleaned.append('# ME_CAM camera profile (managed by scripts/set_camera_profile.py)')
    cleaned.append(f"camera_auto_detect={cfg['camera_auto_detect']}")
    if cfg['overlay']:
        cleaned.append(f"dtoverlay={cfg['overlay']}")
    cleaned.append('gpu_mem=128')

    path.write_text('\n'.join(cleaned) + '\n')


def main() -> int:
    parser = argparse.ArgumentParser(description='Set Raspberry Pi camera boot profile for ME_CAM.')
    parser.add_argument('--profile', choices=SUPPORTED.keys(), required=True,
                        help='Camera profile to apply: auto, imx519, ov5647, ov547')
    parser.add_argument('--boot-config', default=str(BOOT_CONFIG),
                        help='Path to boot firmware config (default: /boot/firmware/config.txt)')
    parser.add_argument('--no-backup', action='store_true', help='Skip config backup')
    args = parser.parse_args()

    config_path = Path(args.boot_config)
    if not config_path.exists():
        raise FileNotFoundError(f'Config not found: {config_path}')

    if not args.no_backup:
        backup = backup_config(config_path)
        print(f'[OK] Backup written: {backup}')

    apply_profile(config_path, args.profile)
    selected = SUPPORTED[args.profile]

    print(f"[OK] Applied profile: {args.profile} ({selected['label']})")
    print('[NEXT] Reboot required: sudo reboot')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
