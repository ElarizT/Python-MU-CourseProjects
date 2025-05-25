/**
 * Logout From All Devices 
 * 
 * This script provides functionality to logout from all devices by revoking
 * all Firebase refresh tokens for the current user.
 */

(function() {
    'use strict';
    
    // Add event listener when DOM is loaded
    document.addEventListener('DOMContentLoaded', function() {
        // Find the logout from all devices button
        const logoutAllBtn = document.querySelector('[data-auth="logout-all"]');
        
        if (logoutAllBtn) {
            logoutAllBtn.addEventListener('click', logoutFromAllDevices);
        }
    });
    
    /**
     * Logs the user out from all devices by revoking all Firebase refresh tokens
     */
    async function logoutFromAllDevices(event) {
        event.preventDefault();
        
        // Show loading state
        const originalText = event.target.innerHTML;
        event.target.innerHTML = '<i class="fas fa-circle-notch fa-spin me-2"></i> Logging out all devices...';
        event.target.disabled = true;
        
        try {
            console.log('Starting logout from all devices process');
            
            // Get current user if available
            let uid = null;
            let currentToken = null;
            
            if (typeof firebase !== 'undefined' && firebase.auth) {
                try {
                    const currentUser = firebase.auth().currentUser;
                    if (currentUser) {
                        uid = currentUser.uid;
                        console.log('Current user UID for logout-all:', uid);
                        
                        // Try to get the token to include with the revocation request
                        try {
                            currentToken = await currentUser.getIdToken();
                        } catch (tokenError) {
                            console.error('Error getting token for logout-all:', tokenError);
                        }
                    }
                } catch (firebaseError) {
                    console.error('Error accessing Firebase user for logout-all:', firebaseError);
                }
            }
            
            // Revoke all tokens for this user
            if (uid || currentToken) {
                try {
                    const payload = {};
                    if (uid) payload.user_id = uid;
                    if (currentToken) payload.token = currentToken;
                    
                    // Call revoke endpoint
                    const response = await fetch('/api/auth/revoke-token', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Cache-Control': 'no-cache, no-store, must-revalidate'
                        },
                        body: JSON.stringify(payload)
                    });
                    
                    if (response.ok) {
                        console.log('Successfully revoked all tokens for all devices');
                    } else {
                        console.warn('Failed to revoke tokens for all devices:', await response.text());
                    }
                } catch (revokeError) {
                    console.error('Error revoking tokens for all devices:', revokeError);
                }
            }
            
            // After token revocation, perform standard logout
            if (typeof logoutUtils !== 'undefined' && logoutUtils.forceFirebaseLogout) {
                await logoutUtils.forceFirebaseLogout();
            } else if (typeof signOut === 'function') {
                await signOut();
            } else {
                // Fallback to simple redirect
                window.location.href = '/logout';
            }
        } catch (error) {
            console.error('Error in logout-all process:', error);
            
            // Reset button state
            event.target.innerHTML = originalText;
            event.target.disabled = false;
            
            // Show error message
            alert('Could not complete logout from all devices. Please try again.');
        }
    }
})();
