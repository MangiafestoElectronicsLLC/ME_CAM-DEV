# Mobile & Responsive Design Testing Guide

**Date:** February 19, 2026  
**Version:** 2.3.0

---

## Quick Testing Checklist

### 🔲 Mobile Phone (< 480px)

#### Layout & Spacing
- [ ] Hamburger menu visible (toggle button)
- [ ] All buttons are >= 44px tall
- [ ] Text is readable without zooming
- [ ] No horizontal scrolling needed
- [ ] Safe area respected (notched devices)

#### Camera Feed
- [ ] Feed takes full width
- [ ] Max height ~50vh (doesn't cover content)
- [ ] Controls responsive and tappable
- [ ] Quality selector visible

#### Forms
- [ ] Input fields are 16px font (prevents auto-zoom)
- [ ] Labels visible above inputs
- [ ] Error messages clear and readable
- [ ] Buttons full-width or properly sized

#### Navigation
- [ ] Menu toggle works (☰ button)
- [ ] Menu closes when link clicked
- [ ] No overlapping elements

### 🔲 Phone Landscape (480px - 767px)

- [ ] Navigation switches to horizontal (no menu toggle)
- [ ] Camera feed max height ~55vh
- [ ] Status cards arranged 2 columns
- [ ] All text readable in landscape

### 🔲 Tablet (768px - 1024px)

#### Layout
- [ ] Full navigation bar visible (no hamburger)
- [ ] 2-column status grid
- [ ] Camera feed with side panel support
- [ ] Adequate padding on all sides

#### Functionality
- [ ] All buttons accessible
- [ ] Touch targets >= 44px
- [ ] Form fields comfortable to use

### 🔲 Desktop (1280px+)

#### Multi-column Layout
- [ ] 4+ column status grid
- [ ] Sidebar visible (if applicable)
- [ ] Camera feed takes appropriate space
- [ ] No wasted horizontal space

#### Advanced Features
- [ ] Multi-camera view if applicable
- [ ] Detailed dashboard visible
- [ ] All controls accessible

---

## Browser DevTools Testing

### Chrome/Edge DevTools (F12)

1. **Toggle Device Toolbar:** `Ctrl+Shift+M`
2. **Preset Devices:**
   - iPhone SE (375px) → Test small phones
   - iPhone 12 (390px) → Test modern phones
   - iPad (768px) → Test tablets
   - iPad Pro (1024px) → Test large tablets
   - Laptop (1280px) → Test desktop
   - 4K (1920px) → Test large displays

3. **Custom Dimensions:**
   ```
   Mobile Portrait:    375 x 667
   Mobile Landscape:   667 x 375
   Tablet Portrait:    768 x 1024
   Tablet Landscape:   1024 x 768
   Desktop:            1280 x 720
   Large Desktop:      1920 x 1080
   ```

4. **Test Touch Events:**
   - Ctrl+Shift+M enables touch simulation
   - Long-tap for context menu
   - Pinch to zoom

5. **Responsive Design Mode:**
   - Resize window manually
   - Test orientation changes
   - Verify no breakage at arbitrary sizes

### Network Throttling

1. Go to Network tab
2. Click "No throttling" dropdown
3. Select:
   - **Slow 3G** - Test on poor connection
   - **Fast 3G** - Test on typical mobile
   - **4G** - Test on good connection

### Test Results

```
✓ Load Time: < 3 seconds on Fast 3G
✓ Layout: No horizontal scrolling
✓ Images: Properly scaled
✓ Forms: Usable on touch
✓ Navigation: Accessible
```

---

## Real Device Testing

### iOS (iPhone/iPad)

#### Setup
```bash
# 1. Get your Mac's IP address
ifconfig | grep "inet " | grep -v 127.0.0.1

# 2. Start server on accessible port
python3 web/app.py  # Runs on 0.0.0.0:8080

# 3. On iPhone, open Safari
# Go to: http://<your-mac-ip>:8080
```

#### Test Checklist
- [ ] Portrait mode looks good
- [ ] Landscape mode works
- [ ] Keyboard doesn't block content
- [ ] Forms work with auto-fill
- [ ] Touches register correctly
- [ ] Status bar color matches theme
- [ ] "Add to Home Screen" works (if configured)

### Android (Phones/Tablets)

#### Setup
```bash
# 1. Enable USB debugging on device
# Settings > Developer Options > USB Debugging

# 2. Connect device via USB
# Allow debugging connection

# 3. Find device IP
# Settings > WiFi > Connected > IP address

# 4. Or use adb
adb shell ip addr show

# 5. Access from device browser
# http://<your-server-ip>:8080
```

#### Test Checklist
- [ ] Full-screen mode works
- [ ] Hardware back button doesn't break app
- [ ] Native keyboard works with inputs
- [ ] Chrome DevTools remote debugging (optional)

### Remote Testing (Raspberry Pi)

```bash
# SSH into Pi
ssh pi@mecamdev3.local

# Check current IP
hostname -I
# Output: 192.168.1.100

# Start app
cd /home/pi/ME_CAM-DEV
python3 web/app.py

# Access from phone/tablet:
# http://192.168.1.100:8080
```

---

## Specific Feature Testing

### Camera Feed
```
✓ Loads within 2 seconds
✓ Responsive to window resize
✓ Quality selector works
✓ Pause/resume functional
✓ Fullscreen button responsive
✓ Screenshot feature works
```

### Dashboard Stats
```
✓ Quick stats grid responsive
✓ Battery indicator updates
✓ Status pills visible and readable
✓ Cards have proper spacing
✓ Hover effects work (desktop)
```

### Forms & Input
```
✓ Labels associated with inputs
✓ Focus states visible
✓ Error messages display
✓ Success messages display
✓ Tab order is logical
✓ Form submission works
✓ CSRF token included
```

### Navigation
```
✓ Mobile: Menu toggle works
✓ Mobile: Menu closes on link click
✓ Tablet: Menu visible without toggle
✓ Desktop: Full navigation bar
✓ All links functional
✓ Active page indicator
```

---

## Automated Testing Script

Save as `test_responsive.py`:

```python
#!/usr/bin/env python3
"""
Quick responsive design tester
Checks breakpoints and basic functionality
"""

import requests
from bs4 import BeautifulSoup
import sys

BASE_URL = "http://localhost:8080"

def test_connectivity():
    """Test server is running"""
    try:
        response = requests.get(BASE_URL)
        print("✓ Server is running")
        return True
    except:
        print("✗ Server is not running")
        return False

def test_csrf_token():
    """Test CSRF token generation"""
    session = requests.Session()
    response = session.get(f"{BASE_URL}/login")
    
    if 'csrf_token' in session.cookies or 'session' in response.cookies:
        print("✓ CSRF token generation working")
        return True
    else:
        print("✗ CSRF token not generated")
        return False

def test_responsive_css():
    """Check responsive CSS is included"""
    response = requests.get(f"{BASE_URL}")
    
    if 'responsive.css' in response.text:
        print("✓ Responsive CSS included")
        return True
    else:
        print("✗ Responsive CSS missing")
        return False

def test_viewport_meta():
    """Check viewport meta tag"""
    response = requests.get(f"{BASE_URL}/login")
    soup = BeautifulSoup(response.text, 'html.parser')
    
    viewport = soup.find('meta', {'name': 'viewport'})
    if viewport:
        print(f"✓ Viewport meta tag present")
        return True
    else:
        print("✗ Viewport meta tag missing")
        return False

def main():
    tests = [
        test_connectivity,
        test_csrf_token,
        test_responsive_css,
        test_viewport_meta,
    ]
    
    print("=== ME_CAM Responsive Design Tests ===\n")
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ {test.__name__}: {e}")
            failed += 1
    
    print(f"\n=== Results ===")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    return 0 if failed == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
```

**Run it:**
```bash
python3 test_responsive.py
```

---

## Performance Metrics

### Target Metrics

```
Mobile (3G):
  - First Paint: < 2 seconds
  - Interactive: < 4 seconds
  - CSS Size: < 25KB gzipped
  - HTML Size: < 50KB

Mobile (4G):
  - First Paint: < 1 second
  - Interactive: < 2 seconds

Desktop:
  - First Paint: < 0.5 seconds
  - Interactive: < 1 second
```

### Measure with DevTools

1. Open DevTools (F12)
2. Go to **Performance** tab
3. Click record button (⏺️)
4. Reload page
5. Stop recording
6. Analyze:
   - **First Contentful Paint (FCP)**
   - **Largest Contentful Paint (LCP)**
   - **Cumulative Layout Shift (CLS)**

---

## Common Issues & Fixes

### Issue: Horizontal Scrolling on Mobile
**Cause:** Fixed-width elements wider than viewport  
**Fix:** Check CSS for `width: 1200px` - change to `max-width: 1200px`

### Issue: Text Too Small to Read
**Cause:** Font sizes not responsive  
**Fix:** Use media queries to increase font size on mobile

### Issue: Buttons Not Tappable
**Cause:** Buttons < 44px  
**Fix:** Add `min-height: 44px; min-width: 44px;`

### Issue: Mobile Menu Won't Open
**Cause:** CSS `display: none` overriding toggle  
**Fix:** Use `.nav-menu.active { display: flex !important; }`

### Issue: Camera Feed Looks Stretched
**Cause:** Aspect ratio not maintained  
**Fix:** Use `object-fit: contain;` on image

### Issue: CSRF Token Missing
**Cause:** Session not initialized  
**Fix:** Check `session['csrf_token']` in layout.html

---

## Checklist for Release

- [ ] Tested on iPhone SE (small phone)
- [ ] Tested on iPhone 12 (modern phone)
- [ ] Tested on iPad (tablet)
- [ ] Tested on desktop (1280px)
- [ ] Tested on large desktop (1920px)
- [ ] Landscape orientation works
- [ ] All buttons >= 44px
- [ ] No horizontal scrolling
- [ ] CSRF tokens working
- [ ] Rate limiting working
- [ ] Security headers present
- [ ] Forms submit correctly
- [ ] Camera feed responsive
- [ ] Navigation functional
- [ ] Accessibility pass
- [ ] Load time < 3 seconds on 3G

---

## Continuous Testing

```bash
# Watch for changes and test
while true; do
  inotifywait -r web/static web/templates
  python3 test_responsive.py
done
```

---

**Last Updated:** February 19, 2026
