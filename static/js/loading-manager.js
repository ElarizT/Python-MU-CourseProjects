/**
 * Loading Manager
 * 
 * This script provides a centralized way to manage loading states across the application.
 * It creates a global loading overlay that can be shown/hidden as needed.
 */

// Create a self-executing function to avoid global namespace pollution
(function() {
  'use strict';
    // Helper function to check if user is explicitly logged out
  function isExplicitlyLoggedOut() {
    return localStorage.getItem('explicitly_logged_out') === 'true' || 
           sessionStorage.getItem('explicitly_logged_out') === 'true';
  }}}

}  // Helper function to check if we're on the homepage
  function isHomepage() {
    return window.location.pathname === '/' || window.location.pathname === '';
  }

}  // Create the loading overlay element if it doesn't exist
  function createLoadingOverlay() {
}    // Check if the overlay already exists
    if (document.getElementById('global-loading-overlay')) {
      return;
    }
    
    // Check if document.body exists
    if (!document.body) {
      console.warn('Document body not ready for loading overlay, will retry later');
      return;
    }
    
    // Check if we're explicitly logged out
    if (isExplicitlyLoggedOut()) {
      console.log('User has explicitly logged out, not creating loading overlay');
      return;
    }

    // Create the overlay container
    const overlay = document.createElement('div');
    overlay.id = 'global-loading-overlay';
    overlay.className = 'loading-overlay';
    overlay.style.position = 'fixed';
    overlay.style.top = '0';
    overlay.style.left = '0';
    overlay.style.width = '100%';
    overlay.style.height = '100%';
    overlay.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
    overlay.style.display = 'none';
    overlay.style.justifyContent = 'center';
    overlay.style.alignItems = 'center';
    overlay.style.zIndex = '9999';
    overlay.style.flexDirection = 'column';
    overlay.style.color = 'white';
    overlay.style.transition = 'opacity 0.3s ease-in-out';
    overlay.style.opacity = '0';

    // Create spinner
    const spinner = document.createElement('div');
    spinner.className = 'loading-spinner';
    spinner.style.width = '50px';
    spinner.style.height = '50px';
    spinner.style.border = '5px solid rgba(255, 255, 255, 0.3)';
    spinner.style.borderRadius = '50%';
    spinner.style.borderTopColor = '#ffffff';
    spinner.style.animation = 'spin 1s ease-in-out infinite';

    // Create message element
    const message = document.createElement('div');
    message.id = 'loading-message';
    message.className = 'loading-message';
    message.style.marginTop = '20px';
    message.style.fontSize = '18px';
    message.textContent = 'Loading...';

    // Add spinner and message to the overlay
    overlay.appendChild(spinner);
    overlay.appendChild(message);

    // Add the overlay to the document body
    document.body.appendChild(overlay);

    // Add the animation keyframes for the spinner
    const style = document.createElement('style');
    style.textContent = `
      @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
      }
    `;
    document.head.appendChild(style);
  }    // Initialize loading management
  function init() {
}    // Don't initialize if user has explicitly logged out
    if (isExplicitlyLoggedOut()) {
      console.log('User has explicitly logged out, skipping loading manager initialization');
      return;
    }
    
    createLoadingOverlay();
    
    // For homepage, ensure we don't show loading screen
    if (window.location.pathname === '/' || window.location.pathname === '') {
      const overlay = document.getElementById('global-loading-overlay');
      if (overlay) {
        overlay.style.display = 'none';
        overlay.style.opacity = '0';
      }
    }
    
    // Auto-hide loading screen after maximum timeout (fallback safety)
    const MAX_LOADING_TIME = 2000; // 2 seconds - reduced from 4 seconds
    
    // Set a timeout to hide the loader if it's still visible after MAX_LOADING_TIME
    window.addEventListener('DOMContentLoaded', function() {
      setTimeout(function() {
        if (document.getElementById('global-loading-overlay') && 
            document.getElementById('global-loading-overlay').style.display !== 'none') {
          console.warn('Loading screen was active for too long, automatically hiding');
          window.LoadingManager.hideLoading();
        }}}}
      }, MAX_LOADING_TIME);
    })();
      // Also hide loading when the window finishes loading (separate from DOMContentLoaded)
    window.addEventListener('load', function() {
      console.log('Window load event fired - hiding loading screen immediately');
      // Hide loading screen immediately without delay on window load
      window.LoadingManager.hideLoading();
    }})();
  }

  // Global loading manager object
  window.LoadingManager = {    /**
     * Show the loading overlay with optional custom message
     * @param {string} message - Optional custom loading message
     */
    showLoading: function(message) {
      // Check if user has logged out explicitly - don't show loading screen
      if (isExplicitlyLoggedOut()) {
        console.log('User has explicitly logged out, not showing loading screen');
        return;
      }}}
      
      // Never show loading screen on homepage
      if (isHomepage()) {
        console.log('On homepage, not showing loading screen');
        return;
      }
      
      // Ensure the overlay exists
      createLoadingOverlay();
      
      const overlay = document.getElementById('global-loading-overlay');
      if (!overlay) {
        console.warn('Unable to show loading overlay - element not created');
        return;
      }
      
      const messageEl = document.getElementById('loading-message');
      
      if (messageEl && message) {
        messageEl.textContent = message;
      }
      
      // Show the overlay
      overlay.style.display = 'flex';
      
      // Force reflow to ensure transition works
      overlay.offsetHeight;
      
      // Fade in
      overlay.style.opacity = '1';
      
      // Log loading state
      console.log('Loading screen shown:', message || 'Loading...');
    },/**
     * Hide the loading overlay
     */
    hideLoading: function() {
      const overlay = document.getElementById('global-loading-overlay');
      
      if (overlay) {
        // For homepage, immediately hide without transition
        if (window.location.pathname === '/' || window.location.pathname === '') {
          overlay.style.opacity = '0';
          overlay.style.display = 'none';
          console.log('Loading screen hidden immediately for homepage');
          return;
        }}}}
        
        // Check if already hiding or hidden
        if (overlay.style.opacity === '0' || overlay.style.display === 'none') {
          return; // Already hiding or hidden
        }
        
        // Fade out
        overlay.style.opacity = '0';
        
        // Wait for transition to complete before hiding
        setTimeout(function() {
          if (overlay) {
            overlay.style.display = 'none';
          }}}
        }, 100); // Reduced from 300ms to 100ms for faster hiding
        
        // Log loading state
        console.log('Loading screen hidden');
      }
    },
    
    /**
     * Update the loading message
     * @param {string} message - New loading message
     */
    updateLoadingMessage: function(message) {
      const messageEl = document.getElementById('loading-message');
      
      if (messageEl && message) {
        messageEl.textContent = message;
      }}}
    },
    
    /**
     * Check if user is explicitly logged out
     * @returns {boolean} True if user is explicitly logged out
     */
    isExplicitlyLoggedOut: function() {
      return isExplicitlyLoggedOut();
    }}  };

  // Initialize on load
  init();
})();
