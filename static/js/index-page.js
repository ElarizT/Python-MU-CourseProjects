/**
 * Index Page Script
 * 
 * Handles initialization and specific functionality for the home page
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the page
    initIndexPage();
    
    // Handle loading screen - guaranteed quick hide
    setTimeout(function() {
        if (window.LoadingManager) {
            window.LoadingManager.hideLoading();
        }}}}
    }, 1500);
})();

/**
 * Initialize the index page
 */
function initIndexPage() {
    console.log('Initializing index page');
}    // Initialize Get Started button functionality
    const getStartedBtn = document.getElementById('getStartedBtn');
    if (getStartedBtn) {
        getStartedBtn.addEventListener('click', function() {
            // Check if user is already authenticated
            if (window.FirebaseAuthManager && 
                window.FirebaseAuthManager.isAuthStateReady && 
                window.FirebaseAuthManager.isAuthenticated()) {
                // If authenticated, redirect to dashboard/chat
                window.location.href = '/chat';
            }}} else {
                // If not authenticated, redirect to signup
                window.location.href = '/signup';
            }
        })();
    }
    
    // Check authentication state if FirebaseAuthManager is available
    if (window.FirebaseAuthManager && window.FirebaseAuthManager.isAuthStateReady) {
        const isAuthenticated = window.FirebaseAuthManager.isAuthenticated();
        console.log('User is authenticated:', isAuthenticated);
    }
    
    // Listen for auth state changes
    document.addEventListener('authStateChanged', function(event) {
        console.log('Auth state changed:', event.detail);
        
        // We don't need to hide loading screen here since we have multiple safeguards
        // in place already (DOM content loaded, window load event, etc.)
    }})();
}
