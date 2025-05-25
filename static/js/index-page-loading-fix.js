/**
 * Index Page Loading Fix
 * 
 * This script is included directly on the index page template to handle the loading screen issue.
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('Index page specific loading fix running');
    
    // Function to hide any loading screens
    function hideLoadingScreens() {
}        // Try direct DOM manipulation first
        const overlay = document.getElementById('global-loading-overlay');
        if (overlay) {
            overlay.style.display = 'none';
            overlay.style.opacity = '0';
            console.log('Index page: Hidden loading overlay via direct DOM manipulation');
        }
        
        // Use LoadingManager API if available
        if (window.LoadingManager) {
            window.LoadingManager.hideLoading();
            console.log('Index page: Called LoadingManager.hideLoading()');
        }
    }
    
    // Hide loading screens immediately
    hideLoadingScreens();
    
    // Hide loading screens again after a very short delay (just to be safe)
    setTimeout(hideLoadingScreens, 100);
    setTimeout(hideLoadingScreens, 500);
    
    // Add a failsafe to the page that checks if content is visible
    setTimeout(function() {
        // Check if the main content is visible by seeing if it has rendered height
        const mainContent = document.querySelector('.container.py-4');
        if (mainContent) {
            const computedStyle = window.getComputedStyle(mainContent);
            const contentVisible = computedStyle.display !== 'none';
            
            if (!contentVisible) {
                console.warn('Index page: Main content might be hidden, attempting final fix');
                // Hide any potential loading screens one more time
                hideLoadingScreens();
                
                // Force show the main content
                mainContent.style.display = 'block';
            } else {
                console.log('Index page: Content is properly visible');
            }
        }
    }, 1000);
});

// Also run checks when window is fully loaded
window.addEventListener('load', function() {
    console.log('Index page: Window loaded, ensuring loading screens are hidden');
    
    // Hide any loading screens that might still be visible
    const overlay = document.getElementById('global-loading-overlay');
    if (overlay) {
        overlay.style.display = 'none';
        overlay.style.opacity = '0';
    }
    
    // Use LoadingManager API if available
    if (window.LoadingManager) {
        window.LoadingManager.hideLoading();
    }
})();
