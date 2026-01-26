#!/usr/bin/env python3
import json
import sys

config_file = sys.argv[1] if len(sys.argv) > 1 else '/home/pi/ME_CAM-DEV/config/config.json'

try:
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    config['first_run_completed'] = True
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Marked first-run as complete in {config_file}")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
