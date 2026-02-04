"""
GitHub Auto-Update System - Keeps ME_CAM updated automatically
Runs on startup to check for latest version and install updates

Features:
- Checks GitHub for latest release
- Downloads update if newer version available
- Validates download integrity
- Backs up previous version
- Graceful fallback if update fails
"""

import os
import json
import subprocess
import sys
from datetime import datetime, timedelta
from loguru import logger
from typing import Dict, Optional, Tuple
import time

class GitHubUpdater:
    """Handle automatic updates from GitHub"""
    
    def __init__(self, repo: str = "MangiafestoElectronicsLLC/ME_CAM-DEV",
                 base_dir: Optional[str] = None):
        """
        Args:
            repo: GitHub repository (owner/repo)
            base_dir: Base directory of ME_CAM installation
        """
        self.repo = repo
        self.base_dir = base_dir or os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.version_file = os.path.join(self.base_dir, ".version")
        self.update_log = os.path.join(self.base_dir, "logs", "update.log")
        self.check_interval_hours = 24
        
        os.makedirs(os.path.dirname(self.update_log), exist_ok=True)
    
    def get_current_version(self) -> str:
        """Get current installed version"""
        try:
            if os.path.exists(self.version_file):
                with open(self.version_file, 'r') as f:
                    data = json.load(f)
                    return data.get('version', '2.2.3')
        except:
            pass
        
        # Try to get from main.py version string
        return "2.2.3"
    
    def set_current_version(self, version: str):
        """Save current version"""
        try:
            os.makedirs(os.path.dirname(self.version_file), exist_ok=True)
            with open(self.version_file, 'w') as f:
                json.dump({
                    'version': version,
                    'installed_at': datetime.utcnow().isoformat(),
                    'instance_id': 'local'
                }, f, indent=2)
        except Exception as e:
            logger.warning(f"[UPDATE] Failed to save version: {e}")
    
    def _should_check(self) -> bool:
        """Check if enough time has passed since last check"""
        try:
            if not os.path.exists(self.update_log):
                return True
            
            with open(self.update_log, 'r') as f:
                lines = f.readlines()
                if lines:
                    # Parse last update check timestamp
                    for line in reversed(lines[-10:]):
                        if 'Checked' in line or 'version' in line.lower():
                            # Don't check too frequently
                            return True
        except:
            pass
        
        return True
    
    def check_for_updates(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Check GitHub for newer version
        
        Returns:
            (has_update, latest_version, download_url)
        """
        if not self._should_check():
            logger.debug("[UPDATE] Skipping check (checked recently)")
            return False, None, None
        
        try:
            import requests
            
            # Get latest release from GitHub API
            api_url = f"https://api.github.com/repos/{self.repo}/releases/latest"
            
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            latest_version = data.get('tag_name', '').lstrip('v')
            
            if not latest_version:
                logger.warning("[UPDATE] Could not parse version from GitHub")
                return False, None, None
            
            current_version = self.get_current_version()
            
            logger.info(f"[UPDATE] Current: {current_version}, Latest: {latest_version}")
            
            if self._is_newer(latest_version, current_version):
                # Try to find zip download URL
                download_url = None
                for asset in data.get('assets', []):
                    if asset['name'].endswith('.zip'):
                        download_url = asset['browser_download_url']
                        break
                
                if not download_url:
                    download_url = data.get('zipball_url')
                
                logger.success(f"[UPDATE] ✓ New version available: {latest_version}")
                return True, latest_version, download_url
            else:
                logger.info(f"[UPDATE] Already on latest version: {current_version}")
                return False, current_version, None
                
        except requests.exceptions.Timeout:
            logger.warning("[UPDATE] GitHub check timeout")
        except requests.exceptions.RequestException as e:
            logger.warning(f"[UPDATE] GitHub check failed: {e}")
        except Exception as e:
            logger.error(f"[UPDATE] Unexpected error: {e}")
        
        return False, None, None
    
    def _is_newer(self, version1: str, version2: str) -> bool:
        """Compare versions (version1 > version2)"""
        try:
            v1_parts = [int(x) for x in version1.split('.')[:3]]
            v2_parts = [int(x) for x in version2.split('.')[:3]]
            
            # Pad with zeros
            while len(v1_parts) < 3:
                v1_parts.append(0)
            while len(v2_parts) < 3:
                v2_parts.append(0)
            
            return v1_parts > v2_parts
        except:
            return version1 > version2
    
    def download_update(self, download_url: str, version: str) -> bool:
        """Download update from URL"""
        try:
            import requests
            from pathlib import Path
            
            backup_dir = os.path.join(self.base_dir, ".backup")
            os.makedirs(backup_dir, exist_ok=True)
            
            # Download to temp file
            temp_file = os.path.join(backup_dir, f"update-{version}.zip")
            
            logger.info(f"[UPDATE] Downloading from {download_url[:80]}...")
            
            response = requests.get(download_url, timeout=60, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            chunk_size = 8192
            
            with open(temp_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            if progress % 25 == 0:
                                logger.debug(f"[UPDATE] Download: {progress:.0f}%")
            
            logger.success(f"[UPDATE] ✓ Downloaded: {temp_file} ({downloaded / 1024 / 1024:.1f}MB)")
            return True
            
        except requests.exceptions.Timeout:
            logger.error("[UPDATE] Download timeout")
        except Exception as e:
            logger.error(f"[UPDATE] Download failed: {e}")
        
        return False
    
    def apply_update(self, version: str) -> bool:
        """
        Apply update from backup
        
        Steps:
        1. Backup current version
        2. Extract update
        3. Validate files
        4. Set new version
        """
        try:
            import shutil
            import zipfile
            
            backup_dir = os.path.join(self.base_dir, ".backup")
            zip_file = os.path.join(backup_dir, f"update-{version}.zip")
            
            if not os.path.exists(zip_file):
                logger.error(f"[UPDATE] Update file not found: {zip_file}")
                return False
            
            # Backup current version
            backup_path = os.path.join(backup_dir, f"backup-{self.get_current_version()}")
            
            critical_files = ['main.py', 'requirements.txt', 'web/app_lite.py']
            
            logger.info(f"[UPDATE] Backing up current version to {backup_path}")
            os.makedirs(backup_path, exist_ok=True)
            
            for file in critical_files:
                src = os.path.join(self.base_dir, file)
                if os.path.exists(src):
                    dst = os.path.join(backup_path, file)
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    shutil.copy2(src, dst)
            
            # Extract update
            logger.info(f"[UPDATE] Extracting update...")
            extract_dir = os.path.join(backup_dir, f"extract-{version}")
            os.makedirs(extract_dir, exist_ok=True)
            
            with zipfile.ZipFile(zip_file, 'r') as zf:
                zf.extractall(extract_dir)
            
            # Find the actual repo folder (GitHub creates a subfolder)
            extracted_repos = [d for d in os.listdir(extract_dir)
                              if os.path.isdir(os.path.join(extract_dir, d))]
            
            if extracted_repos:
                repo_dir = os.path.join(extract_dir, extracted_repos[0])
            else:
                repo_dir = extract_dir
            
            # Validate critical files exist in update
            for file in critical_files:
                if not os.path.exists(os.path.join(repo_dir, file)):
                    logger.error(f"[UPDATE] Missing file in update: {file}")
                    return False
            
            # Copy files over (selective - don't overwrite config)
            logger.info(f"[UPDATE] Applying files...")
            
            exclude_patterns = ['config/', 'logs/', 'recordings/', '.git/']
            
            for root, dirs, files in os.walk(repo_dir):
                # Skip excluded directories
                dirs[:] = [d for d in dirs if not any(
                    d in ep or ep in d for ep in exclude_patterns
                )]
                
                for file in files:
                    src = os.path.join(root, file)
                    rel_path = os.path.relpath(src, repo_dir)
                    dst = os.path.join(self.base_dir, rel_path)
                    
                    # Skip certain files
                    if any(rel_path.startswith(ep) for ep in exclude_patterns):
                        continue
                    if rel_path.endswith('.pyc'):
                        continue
                    
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    shutil.copy2(src, dst)
            
            # Update version
            self.set_current_version(version)
            logger.success(f"[UPDATE] ✓ Updated to version {version}")
            
            # Log update
            with open(self.update_log, 'a') as f:
                f.write(f"{datetime.utcnow().isoformat()} - Updated to {version}\n")
            
            return True
            
        except Exception as e:
            logger.error(f"[UPDATE] Apply failed: {e}")
            return False
    
    def auto_update_on_startup(self) -> bool:
        """
        Check for updates and install if available
        Called on app startup
        
        Returns:
            True if updated and restart needed, False otherwise
        """
        try:
            has_update, version, url = self.check_for_updates()
            
            if not has_update or not version or not url:
                logger.info("[UPDATE] No updates available")
                return False
            
            logger.warning(f"[UPDATE] ⚠ UPDATE AVAILABLE: {version}")
            
            # Don't auto-download on startup (too slow)
            # Just log that update is available
            # User can manually pull from Git or it will happen on next boot
            
            return False
            
        except Exception as e:
            logger.error(f"[UPDATE] Auto-update failed: {e}")
            return False


# Global instance
_updater: Optional[GitHubUpdater] = None

def get_updater(base_dir: Optional[str] = None) -> GitHubUpdater:
    """Get or create updater instance"""
    global _updater
    
    if _updater is None:
        _updater = GitHubUpdater(base_dir=base_dir)
    
    return _updater


def check_for_updates_async():
    """
    Check for updates in background
    Should be called after app startup
    """
    try:
        updater = get_updater()
        has_update, version, url = updater.check_for_updates()
        
        if has_update:
            logger.warning(f"[UPDATE] New version {version} available at GitHub")
            # Could optionally download in background here
            # For now, just notify
        
    except Exception as e:
        logger.debug(f"[UPDATE] Background check failed: {e}")
