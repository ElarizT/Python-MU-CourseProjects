#!/usr/bin/env python3
"""
Homepage Loading Fix Script

This script analyzes the Flask application and fixes loading screen issues 
specifically for the homepage.
"""

import os
import re
import sys

def fix_loading_issue():
    print("Applying homepage loading fix...")
    
    # Step 1: Create the ultimate loading fix JavaScript file
    js_path = os.path.join('static', 'js', 'ultimate-homepage-fix.js')
    full_js_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), js_path)
    
    js_content = """/**
 * Ultimate Homepage Loading Fix
 * This script is designed to completely eliminate loading screen issues on the homepage.
 */

(function() {
    'use strict';

    // Only run on the homepage/index page
    const isHomepage = window.location.pathname === '/' || window.location.pathname === '';
    if (!isHomepage) return;
    
    console.log('Ultimate homepage loading fix activated');

    // PART 1: Apply CSS fix
    function injectCSS() {
        const css = `
            #global-loading-overlay {
                display: none !important;
                opacity: 0 !important;
                visibility: hidden !important;
                pointer-events: none !important;
            }
            
            /* Ensure content is visible */
            body {
                visibility: visible !important;
                opacity: 1 !important;
            }
            
            .container {
                display: block !important;
            }
        `;
        
        const style = document.createElement('style');
        style.textContent = css;
        
        // Add to head if available, otherwise to document
        if (document.head) {
            document.head.appendChild(style);
        } else {
            document.documentElement.appendChild(style);
        }
        
        console.log('Homepage loading fix: CSS injected');
    }
    
    // PART 2: Direct DOM manipulation
    function hideLoadingElements() {
        // Find all loading overlays by id or class
        const overlays = document.querySelectorAll('#global-loading-overlay, .loading-overlay');
        
        if (overlays && overlays.length) {
            overlays.forEach(overlay => {
                overlay.style.display = 'none';
                overlay.style.opacity = '0';
                overlay.style.visibility = 'hidden';
            });
            console.log('Homepage loading fix: Removed', overlays.length, 'loading overlays');
        }
    }
    
    // PART 3: API overrides
    function overrideLoadingAPIs() {
        // Override LoadingManager if it exists
        if (window.LoadingManager) {
            // Save original methods for non-homepage pages
            const originalShow = window.LoadingManager.showLoading;
            const originalHide = window.LoadingManager.hideLoading;
            
            // Replace showLoading to do nothing on homepage
            window.LoadingManager.showLoading = function(message) {
                if (isHomepage) {
                    console.log('Homepage loading fix: Prevented showing loading screen');
                    return;
                }
                return originalShow.call(window.LoadingManager, message);
            };
            
            // Call hideLoading
            window.LoadingManager.hideLoading();
            
            console.log('Homepage loading fix: Overrode LoadingManager methods');
        }
        
        // When PageInitializer is available, ensure it doesn't show loading
        if (window.PageInitializer) {
            const originalInit = window.PageInitializer.init;
            window.PageInitializer.init = function() {
                if (isHomepage) {
                    // Run without loading screens
                    console.log('Homepage loading fix: Modified PageInitializer.init');
                    hideLoadingElements();
                }
                return originalInit.apply(this, arguments);
            };
        }
    }
    
    // PART 4: MutationObserver to catch any dynamically added loading elements
    function setupMutationObserver() {
        if (!window.MutationObserver) return;
        
        const observer = new MutationObserver(function(mutations) {
            let needsCheck = false;
            
            for (const mutation of mutations) {
                if (mutation.addedNodes.length) {
                    needsCheck = true;
                    break;
                }
            }
            
            if (needsCheck) {
                hideLoadingElements();
            }
        });
        
        // Start observing the document
        observer.observe(document.documentElement, {
            childList: true,
            subtree: true
        });
        
        console.log('Homepage loading fix: MutationObserver active');
    }
    
    // Execute fixes immediately
    injectCSS();
    hideLoadingElements();
    
    // Set up continuous protection
    setupMutationObserver();
    
    // Run API overrides when ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', overrideLoadingAPIs);
    } else {
        overrideLoadingAPIs();
    }
    
    // Additional safety checks
    window.addEventListener('load', function() {
        hideLoadingElements();
        console.log('Homepage loading fix: Final checks on window load');
    });
    
    // Final safety net: check repeatedly for a short period
    let checkCount = 0;
    const intervalId = setInterval(function() {
        hideLoadingElements();
        checkCount++;
        if (checkCount >= 10) clearInterval(intervalId);
    }, 100);
})();"""

    # Create directory if needed
    os.makedirs(os.path.dirname(full_js_path), exist_ok=True)
    
    with open(full_js_path, 'w', encoding='utf-8') as f:
        f.write(js_content)
    
    print(f"Created {js_path}")
    
    # Step 2: Update the layout.html file
    layout_path = os.path.join('templates', 'layout.html')
    full_layout_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), layout_path)
    
    if os.path.exists(full_layout_path):
        with open(full_layout_path, 'r', encoding='utf-8') as f:
            layout_content = f.read()
        
        # Add our script to the head section
        head_pattern = r'<head>(.*?)<meta'
        script_tag = '<head>\n    <!-- Immediate loading fix for homepage -->\n    <script src="/static/js/ultimate-homepage-fix.js"></script>\n    <meta'
        
        updated_content = re.sub(head_pattern, script_tag, layout_content, flags=re.DOTALL)
        
        # Modify the loading screen logic to skip homepage
        loading_pattern = r'// Show loading only for authenticated pages(.*?)}'
        loading_replacement = """// Show loading only for authenticated pages that need content loading
            // Skip showing loading for public pages and homepage
            if (!window.location.pathname.includes('/login') && 
                !window.location.pathname.includes('/signup') && 
                !window.location.pathname.includes('/logout') &&
                window.location.pathname !== '/' &&
                window.location.pathname !== '') {
                    
                if (window.LoadingManager) {
                    window.LoadingManager.showLoading('Loading application...');
                }
            }"""
        
        updated_content = re.sub(loading_pattern, loading_replacement, updated_content, flags=re.DOTALL)
        
        # Write back the updated content
        with open(full_layout_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print(f"Updated {layout_path}")
    else:
        print(f"Warning: Could not find {layout_path}")
    
    # Step 3: Update the index.html file
    index_path = os.path.join('templates', 'index.html')
    full_index_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), index_path)
    
    if os.path.exists(full_index_path):
        with open(full_index_path, 'r', encoding='utf-8') as f:
            index_content = f.read()
        
        # Add inline fix to head_scripts block
        head_scripts_pattern = r'{% block head_scripts %}(.*?){% endblock %}'
        head_scripts_replacement = """{% block head_scripts %}
{% if is_homepage %}
<!-- Inline homepage loading fix that runs immediately -->
<script>
    (function() {
        console.log('Inline homepage loading fix running immediately');
        
        // PART 1: Add CSS rules to completely hide loading elements
        document.write('<style id="homepage-loading-fix-style">#global-loading-overlay, .loading-overlay {display: none !important; opacity: 0 !important; visibility: hidden !important;}</style>');
        
        // PART 2: Function to hide any loading elements
        function hideAllLoadingElements() {
            console.log('Hiding all loading elements');
            var elements = document.querySelectorAll('#global-loading-overlay, .loading-overlay');
            if (elements && elements.length > 0) {
                for (var i = 0; i < elements.length; i++) {
                    elements[i].style.display = 'none';
                    elements[i].style.opacity = '0';
                    elements[i].style.visibility = 'hidden';
                }
            }
            
            // Also use LoadingManager API if available
            if (window.LoadingManager) {
                window.LoadingManager.hideLoading();
            }
        }
        
        // Run immediately
        hideAllLoadingElements();
        
        // Also run when DOM is ready
        document.addEventListener('DOMContentLoaded', hideAllLoadingElements);
        
        // And when window is fully loaded
        window.addEventListener('load', hideAllLoadingElements);
        
        // Repeatedly check during the first few seconds
        var count = 0;
        var interval = setInterval(function() {
            hideAllLoadingElements();
            count++;
            if (count >= 10) clearInterval(interval);
        }, 200);
    })();
</script>
{% endif %}

<script src="/static/js/ultimate-homepage-fix.js"></script>

<script>
    // Check for dark mode preference
    function checkDarkMode() {
        if (localStorage.getItem('darkMode') === 'enabled' || 
            (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches && 
             localStorage.getItem('darkMode') !== 'disabled')) {
            document.body.classList.add('dark-mode');
        }
    }
    
    // Run on page load
    document.addEventListener('DOMContentLoaded', checkDarkMode);
</script>
{% endblock %}"""
        
        updated_content = re.sub(head_scripts_pattern, head_scripts_replacement, index_content, flags=re.DOTALL)
        
        # Write back the updated content
        with open(full_index_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print(f"Updated {index_path}")
    else:
        print(f"Warning: Could not find {index_path}")
        
    # Step 4: Update the app.py file
    app_path = 'app.py'
    full_app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), app_path)
    
    if os.path.exists(full_app_path):
        with open(full_app_path, 'r', encoding='utf-8') as f:
            app_content = f.read()
        
        # Update all render_template calls for index.html to include is_homepage=True
        index_render_pattern = r"render_template\('index\.html'(.*?)\)"
        index_render_replacement = r"render_template('index.html', is_homepage=True\1)"
        
        updated_content = re.sub(index_render_pattern, index_render_replacement, app_content)
        
        # Write back the updated content
        with open(full_app_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print(f"Updated {app_path}")
    else:
        print(f"Warning: Could not find {app_path}")
    
    print("Homepage loading fix applied successfully!")


if __name__ == "__main__":
    fix_loading_issue()
