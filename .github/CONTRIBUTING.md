# Contributing to ME Camera

Thank you for your interest in contributing to ME Camera! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

- Be respectful and inclusive
- Focus on the code, not the person
- Report issues professionally
- No harassment or discrimination

## How to Contribute

### Reporting Bugs

1. **Check existing issues** - Avoid duplicates
2. **Create a detailed report** including:
   - Device model (Pi Zero 2W, 3B+, etc.)
   - OS version (Bullseye, Bookworm, etc.)
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - Relevant logs or screenshots

### Suggesting Features

1. **Check existing issues** for similar requests
2. **Create a feature request** with:
   - Clear description of feature
   - Use cases and benefits
   - Example implementation (if applicable)
   - Potential impact on performance

### Creating Pull Requests

1. **Fork the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/ME_CAM-DEV.git
   cd ME_CAM-DEV
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Keep commits focused
   - Use clear commit messages
   - Follow existing code style

4. **Test thoroughly**
   ```bash
   # On Pi Zero 2W or test device
   python3 main_lite.py --mode lite --pi zero2w
   ```

5. **Write/update documentation**
   - Update README if needed
   - Add inline comments for complex logic
   - Update CHANGELOG

6. **Submit Pull Request**
   - Reference any related issues
   - Describe changes clearly
   - Include before/after screenshots if UI changes

## Code Style

### Python
```python
# Use 4 spaces for indentation
# Follow PEP 8 style guide
# Max line length: 100 characters
# Use meaningful variable names
# Add docstrings to functions

def save_motion_clip(camera_obj, frame, duration_sec=3):
    """Save a short MP4 clip when motion is detected.
    
    Args:
        camera_obj: Picamera2 camera object
        frame: Current video frame (numpy array)
        duration_sec: Duration to record (default: 3 seconds)
    
    Returns:
        str: Filename if successful, None if failed
    """
    pass
```

### JavaScript
```javascript
// Use 2 spaces for indentation
// Camel case for variable names
// Clear function names
// Add comments for complex logic

function formatTimestamp(timestamp) {
    // Parse timestamp and format for display
    const date = new Date(timestamp + 'Z');
    return date.toLocaleString('en-US', {
        timeZone: 'America/New_York',
        // ... other options
    });
}
```

### HTML/CSS
```html
<!-- Use semantic HTML -->
<!-- ID for unique elements, classes for styling -->
<!-- Keep indentation consistent -->

<div class="event-item">
    <div class="event-info">
        <!-- Content -->
    </div>
</div>
```

## Performance Considerations

### Pi Zero 2W Constraints
- Limited to 512MB RAM
- Keep memory footprint <200MB
- Optimize video encoding
- Minimize background tasks

### Testing Before Submitting
```bash
# Check memory usage
free -m

# Monitor process
ps aux | grep python

# Check video playback
# Test in browser on low-speed connection
```

## Documentation Standards

### Code Comments
```python
# For complex sections, use block comments
# Explain the "why", not the "what"
# Keep comments updated with code

# Good:
# Motion detection uses frame difference to detect changes
# This is more efficient than ML-based detection for Pi Zero 2W
diff = cv2.absdiff(last_frame, current_frame)

# Avoid:
# Calculate diff between frames
diff = cv2.absdiff(last_frame, current_frame)
```

### Commit Messages
```
feat: Brief description of feature

- Bullet point of changes
- Another change
- Related issue: #123

Detailed explanation if needed.
Type-specific markers:
- feat: New feature
- enhance: Improvement to existing feature
- fix: Bug fix
- docs: Documentation changes
- config: Configuration changes
- test: Test additions
```

## Testing Guidelines

### Manual Testing Checklist
- [ ] Camera streaming works
- [ ] Motion detection triggers
- [ ] Videos record and playback
- [ ] Events save correctly
- [ ] SMS sends (if applicable)
- [ ] Configuration persists
- [ ] Service restarts properly
- [ ] No errors in logs
- [ ] Mobile responsive
- [ ] Performance acceptable

### Device Testing
Test on at least:
- [ ] Pi Zero 2W (primary)
- [ ] Pi 3B+ or higher (if applicable)
- [ ] Multiple browsers (Chrome, Firefox, Safari)

### Performance Requirements
- Memory: <200MB under load
- CPU: <80% during normal operation
- Video stream: Smooth 20 FPS
- Load time: <2 seconds for web pages

## Release Process

1. **Version Bump**
   - Update version in code
   - Update README
   - Update CHANGELOG

2. **Testing**
   - Run full test suite
   - Manual testing on hardware
   - Documentation review

3. **Create Release**
   ```bash
   git tag -a vX.Y.Z -m "Description"
   git push origin vX.Y.Z
   ```

4. **Create GitHub Release**
   - Use release template
   - Include detailed changelog
   - Add release notes

## Versioning

We use Semantic Versioning (MAJOR.MINOR.PATCH):
- MAJOR: Breaking changes, major rewrites
- MINOR: New features, backward compatible
- PATCH: Bug fixes, minor improvements

Example: v2.1.0
- v2 = Major version (multiple releases stable)
- .1 = Minor version (new SMS feature)
- .0 = Patch version (release count)

## License

By contributing, you agree that your contributions are licensed under the same MIT License as the project.

## Questions?

- **GitHub Issues**: For bug reports and feature requests
- **GitHub Discussions**: For questions and community help
- **Email**: support@mangiafestoelectronics.com

## Recognition

Contributors will be recognized in:
- CHANGELOG.md
- README contributors section
- Release notes

Thank you for helping make ME Camera better! 🚀

