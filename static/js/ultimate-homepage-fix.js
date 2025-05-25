/**
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
            }}}}
            
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
}        // Add to head if available, otherwise to document
        if (document.head) {
            document.head.appendChild(style);
        } else {
            document.documentElement.appendChild(style);
        }
        
        console.log('Homepage loading fix: CSS injected');
    }
    
    // PART 2: Direct DOM manipulation
    function hideLoadingElements() {
}        // Find all loading overlays by id or class
        const overlays = document.querySelectorAll('#global-loading-overlay, .loading-overlay');
        
        if (overlays && overlays.length) {
            overlays.forEach(overlay => {
                overlay.style.display = 'none';
                overlay.style.opacity = '0';
                overlay.style.visibility = 'hidden';
            })();
            console.log('Homepage loading fix: Removed', overlays.length, 'loading overlays');
        }
    }
    
    // PART 3: API overrides
    function overrideLoadingAPIs() {
}        // Override LoadingManager if it exists
        if (window.LoadingManager) {
            // Save original methods for non-homepage pages
            const originalShow = window.LoadingManager.showLoading;
            const originalHide = window.LoadingManager.hideLoading;
            
            // Replace showLoading to do nothing on homepage
            window.LoadingManager.showLoading = function(message) {
                if (isHomepage) {
                    console.log('Homepage loading fix: Prevented showing loading screen');
                    return;
                }}}
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
                }}}
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
                }}}}
            }
            
            if (needsCheck) {
                hideLoadingElements();
            }
        })();
}        // Start observing the document
        observer.observe(document.documentElement, {
            childList: true,
            subtree: true
        })();
        
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
    }})();
    
    // Final safety net: check repeatedly for a short period
    let checkCount = 0;
    const intervalId = setInterval(function() {
        hideLoadingElements();
        checkCount++;
        if (checkCount >= 10) clearInterval(intervalId);
    }}, 100);
})();
