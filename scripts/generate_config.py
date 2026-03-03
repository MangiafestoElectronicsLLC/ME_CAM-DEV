#!/usr/bin/env python3
import argparse
import copy
import json
import sys
from pathlib import Path


PROFILES = {
    "device3": {
        "first_run_completed": True,
        "device_name": "ME_CAM_3",
        "device_id": "pi-cam-003",
        "resolution": "640x480",
        "framerate": 40,
        "motion_detection": True,
        "video_length": 30,
        "storage_limit_gb": 50,
        "auto_delete_old": True,
        "web_port": 8080,
    },
    "device4": {
        "first_run_completed": True,
        "device_name": "ME_CAM_4",
        "device_id": "pi-cam-004",
        "resolution": "640x480",
        "framerate": 30,
        "motion_detection": True,
        "video_length": 30,
        "storage_limit_gb": 50,
        "auto_delete_old": True,
        "web_port": 8080,
        "security": {
            "tailscale_only": False,
            "allow_localhost": True,
            "allow_setup_without_vpn": True,
        },
        "camera": {
            "stream_fps": 30,
            "stream_quality": 85,
            "encoding": "mjpeg",
        },
    },
    "device7": {
        "first_run_completed": True,
        "device_name": "ME_CAM_7",
        "device_id": "pi-cam-007",
        "resolution": "1280x720",
        "framerate": 60,
        "motion_detection": True,
        "video_length": 30,
        "storage_limit_gb": 100,
        "auto_delete_old": True,
        "web_port": 8080,
        "security": {
            "tailscale_only": False,
            "allow_localhost": True,
            "allow_setup_without_vpn": True,
        },
        "camera": {
            "stream_fps": 60,
            "stream_quality": 95,
            "encoding": "h264",
        },
        "hub_mode": True,
        "notes": "Pi 5 testing/hub device - higher resolution and FPS due to 4GB RAM and dual-core GPU",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate config/config.json for ME_CAM without manual editing."
    )
    parser.add_argument(
        "--profile",
        choices=sorted(PROFILES.keys()),
        required=True,
        help="Preset profile to use.",
    )
    parser.add_argument(
        "--device-number",
        type=int,
        help="Optional device number (for auto device_name/device_id like ME_CAM_008).",
    )
    parser.add_argument(
        "--device-name",
        help="Override device_name explicitly.",
    )
    parser.add_argument(
        "--device-id",
        help="Override device_id explicitly.",
    )
    parser.add_argument(
        "--output",
        default="config/config.json",
        help="Output file path (default: config/config.json).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite output file if it already exists.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    config = copy.deepcopy(PROFILES[args.profile])

    if args.device_number is not None:
        if args.device_number < 1 or args.device_number > 999:
            print("Error: --device-number must be between 1 and 999.", file=sys.stderr)
            return 2
        config["device_name"] = f"ME_CAM_{args.device_number}"
        config["device_id"] = f"pi-cam-{args.device_number:03d}"

    if args.device_name:
        config["device_name"] = args.device_name

    if args.device_id:
        config["device_id"] = args.device_id

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists() and not args.force:
        print(
            f"Error: {output_path} already exists. Use --force to overwrite.",
            file=sys.stderr,
        )
        return 1

    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(config, handle, indent=2)
        handle.write("\n")

    print(f"Created {output_path}")
    print(f"Profile: {args.profile}")
    print(f"device_name: {config['device_name']}")
    print(f"device_id: {config['device_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
