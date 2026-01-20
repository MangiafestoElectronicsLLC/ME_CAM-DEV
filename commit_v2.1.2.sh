#!/bin/bash
# Git Commit Script for v2.1.2
# Run this to commit all changes to GitHub

echo "🚀 Preparing v2.1.2 Release..."
echo ""

# Show what will be committed
echo "📋 Files staged for commit:"
git status --short

echo ""
echo "📝 Commit Message:"
cat << 'EOF'

v2.1.2: Motion Detection Overhaul & Pi Zero Optimization

Major Updates:
✨ Advanced motion detection with shadow/sunlight filtering
✨ User registration system with validation
✨ WiFi configuration UI in settings page
✨ H.264 video codec for universal browser compatibility
✨ Pre-buffered recording captures full motion events
✨ Enhanced storage management with automatic file cleanup

Bug Fixes:
🐛 Fixed timezone to EST (was showing GMT)
🐛 Fixed video playback stuck at 0:00
🐛 Fixed JSON serialization errors (numpy types)
🐛 Fixed file deletion not removing actual videos
🐛 Fixed motion recording timing (now captures during, not after)

Performance:
⚡ Optimized for Pi Zero 2W (512MB RAM)
⚡ Frame skipping reduces CPU load 50%
⚡ Reduced buffer size for memory efficiency
⚡ Faster cooldown between motion events

Security:
🔒 No credentials in source code
🔒 .gitignore updated to exclude sensitive files
🔒 Self-signed SSL certificate support

Documentation:
📚 Added RELEASE_NOTES_V2.1.2.md
📚 Updated .gitignore with deployment exclusions

Tested on: Raspberry Pi Zero 2W, Pi Camera Module v3 (IMX708)

EOF

echo ""
read -p "🔍 Review changes above. Commit to GitHub? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]
then
    git commit -m "v2.1.2: Motion Detection Overhaul & Pi Zero Optimization

Major Updates:
- Advanced motion detection with shadow/sunlight filtering
- User registration system with validation  
- WiFi configuration UI in settings page
- H.264 video codec for universal browser compatibility
- Pre-buffered recording captures full motion events
- Enhanced storage management with automatic file cleanup

Bug Fixes:
- Fixed timezone to EST (was showing GMT)
- Fixed video playback stuck at 0:00
- Fixed JSON serialization errors (numpy types)
- Fixed file deletion not removing actual videos
- Fixed motion recording timing (now captures during, not after)

Performance:
- Optimized for Pi Zero 2W (512MB RAM)
- Frame skipping reduces CPU load 50%
- Reduced buffer size for memory efficiency
- Faster cooldown between motion events

Security:
- No credentials in source code
- .gitignore updated to exclude sensitive files
- Self-signed SSL certificate support

Tested on: Raspberry Pi Zero 2W, Pi Camera Module v3 (IMX708)"

    echo ""
    echo "✅ Committed successfully!"
    echo ""
    read -p "📤 Push to GitHub now? (y/n) " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]
    then
        git push origin main
        echo ""
        echo "🎉 v2.1.2 Released to GitHub!"
        echo "🔗 https://github.com/MangiafestoElectronicsLLC/ME_CAM-DEV"
    else
        echo "⏸️  Commit saved locally. Push manually with: git push origin main"
    fi
else
    echo "❌ Commit cancelled"
fi
