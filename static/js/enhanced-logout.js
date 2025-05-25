/**
 * Enhanced Firebase Logout Utilities
 * This file provides more aggressive Firebase auth cleanup functions
 * for ensuring complete logout in problematic scenarios.
 */

// Namespace for logout utilities
window.logoutUtils = window.logoutUtils || {};

/**
 * Aggressive cleanup of all Firebase auth state
 * Call this function when standard logout methods are not working
 */
logoutUtils.forceFirebaseLogout = async function() {
    console.log('Force Firebase Logout: Starting aggressive Firebase auth cleanup');
    
    // Set explicit logout flag
    localStorage.setItem('explicitly_logged_out', 'true');
    console.log('Force Firebase Logout: Set explicitly_logged_out flag');
    
    // Clear all Firebase auth data from storage
    logoutUtils.clearAllFirebaseStorage();
      // Handle Firebase auth if available
    if (typeof firebase !== 'undefined' && firebase.auth) {
        try {
            console.log('Force Firebase Logout: Firebase is available, performing auth cleanup');
            
            // Get current user token for revocation if possible
            let currentToken = null;
            try {
                const currentUser = firebase.auth().currentUser;
                if (currentUser) {
                    console.log('Force Firebase Logout: Current user before logout:', currentUser.email);
                    // Try to get the token to revoke it
                    currentToken = await currentUser.getIdToken();
                }
            } catch (tokenError) {
                console.error('Force Firebase Logout: Error getting token to revoke:', tokenError);
            }
            
            // Set persistence to NONE to prevent auto-relogin
            try {
                await firebase.auth().setPersistence(firebase.auth.Auth.Persistence.NONE);
                console.log('Force Firebase Logout: Set Firebase persistence to NONE');
            } catch (e) {
                console.error('Force Firebase Logout: Error setting persistence:', e);
            }
            
            // Sign out from Firebase
            await firebase.auth().signOut();
            console.log('Force Firebase Logout: Successfully signed out from Firebase');
              // Revoke token if we had one
            if (currentToken) {
                try {
                    // Make a request to revoke the token on the server
                    const revokeResponse = await fetch('/api/auth/revoke-token', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Cache-Control': 'no-cache, no-store, must-revalidate',
                            'Pragma': 'no-cache',
                            'Expires': '0'
                        },
                        body: JSON.stringify({ token: currentToken })
                    });
                    
                    if (revokeResponse.ok) {
                        console.log('Force Firebase Logout: Successfully revoked Firebase token');
                    } else {
                        console.warn('Force Firebase Logout: Failed to revoke token, response:', await revokeResponse.text());
                    }
                } catch (revokeError) {
                    console.error('Force Firebase Logout: Error revoking token:', revokeError);
                }
            } else if (firebase.auth().currentUser) {
                // If we couldn't get the token but we have a current user, try to revoke by user ID
                try {
                    const uid = firebase.auth().currentUser.uid;
                    const revokeResponse = await fetch('/api/auth/revoke-token', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Cache-Control': 'no-cache, no-store, must-revalidate',
                            'Pragma': 'no-cache', 
                            'Expires': '0'
                        },
                        body: JSON.stringify({ user_id: uid })
                    });
                    
                    if (revokeResponse.ok) {
                        console.log('Force Firebase Logout: Successfully revoked tokens for user ID');
                    } else {
                        console.warn('Force Firebase Logout: Failed to revoke tokens by user ID, response:', await revokeResponse.text());
                    }
                } catch (revokeError) {
                    console.error('Force Firebase Logout: Error revoking tokens by user ID:', revokeError);
                }
            }
            
            // Clear storage again after signout
            logoutUtils.clearAllFirebaseStorage();
            
            // Delete all Firebase apps if possible
            if (firebase.apps && firebase.apps.length > 0) {
                try {
                    await Promise.all(firebase.apps.map(app => app.delete()));
                    console.log('Force Firebase Logout: Successfully deleted all Firebase apps');
                } catch (e) {
                    console.error('Force Firebase Logout: Error deleting Firebase apps:', e);
                }
            }
        } catch (e) {
            console.error('Force Firebase Logout: Error during Firebase auth cleanup:', e);
        }
    } else {
        console.log('Force Firebase Logout: Firebase is not available, skipping auth cleanup');
    }
    
    // Clear all Firebase auth data from storage one more time
    logoutUtils.clearAllFirebaseStorage();
    
    // Return true to indicate completion
    return true;
};

/**
 * Clear all Firebase-related storage items
 */
logoutUtils.clearAllFirebaseStorage = function() {
    console.log('Force Firebase Logout: Clearing all Firebase storage');
    
    try {
        // First, clear known Firebase keys
        const knownKeys = [
            'firebase:authUser',
            'firebase:previous-user',
            'firebase:remember',
            'firebase:forceRefresh',
            'firebase:redirectUser',
            'firebase:persistence',
            'firebase:pendingRedirect',
            'firebaseToken',
            'firebase:host:',
            'firebase.database:',
            'firebase-installations-database',
            'firebase-messaging-database',
            'firebaseLocalStorageDb',
            'firebase-heartbeat-database'
        ];
        
        // Get project ID if available for more targeted cleanup
        let projectId = null;
        try {
            const authDomain = document.querySelector('meta[name="firebase-auth-domain"]')?.content;
            if (authDomain) {
                projectId = authDomain.split('.')[0];
                console.log('Force Firebase Logout: Detected project ID for targeted cleanup:', projectId);
                
                // Add project-specific keys if we found a project ID
                if (projectId) {
                    knownKeys.push(`firebase:authUser:${projectId}`);
                    knownKeys.push(`firebase:previous-user:${projectId}`);
                }
            }
        } catch (error) {
            console.error('Force Firebase Logout: Error detecting project ID:', error);
        }
        
        // Clear all known keys
        knownKeys.forEach(key => {
            try {
                localStorage.removeItem(key);
            } catch (e) {
                console.error(`Force Firebase Logout: Error clearing localStorage key ${key}:`, e);
            }
        });
        
        // Clear any keys related to Firebase in localStorage
        for (let i = localStorage.length - 1; i >= 0; i--) {
            const key = localStorage.key(i);
            if (key && (key.startsWith('firebase:') || key.includes('firebase') || key.includes('auth'))) {
                localStorage.removeItem(key);
            }
        }
        
        // Clear sessionStorage as well
        for (let i = sessionStorage.length - 1; i >= 0; i--) {
            const key = sessionStorage.key(i);
            if (key && (key.startsWith('firebase:') || key.includes('firebase') || key.includes('auth'))) {
                sessionStorage.removeItem(key);
            }
        }
          // Clear IndexedDB data if possible
        try {
            // Clear IndexedDB for common Firebase auth stores
            const dbNames = [
                'firebaseLocalStorageDb', 
                'firebase-heartbeat-database',
                'firebase-installations-database',
                'firebase-messaging-database',
                'firebase-analytics-database',
                'firebase-performance-database',
                'firebase-auth',
                'firebase-auth-state',
                'firebase-auth-session'
            ];
            
            dbNames.forEach(dbName => {
                try {
                    const req = indexedDB.deleteDatabase(dbName);
                    req.onsuccess = () => console.log(`Force Firebase Logout: Deleted IndexedDB: ${dbName}`);
                    req.onerror = (e) => console.error(`Force Firebase Logout: Error deleting IndexedDB ${dbName}:`, e);
                } catch (e) {
                    console.error(`Force Firebase Logout: Error with IndexedDB ${dbName}:`, e);
                }
            });
              // Also try to delete any database with firebase in the name
            if (indexedDB.databases) {
                indexedDB.databases().then(databases => {
                    databases.forEach(database => {
                        if (database.name && 
                           (database.name.toLowerCase().includes('firebase') || 
                            database.name.toLowerCase().includes('auth') || 
                            database.name.toLowerCase().includes('credential'))) {
                            const req = indexedDB.deleteDatabase(database.name);
                            req.onsuccess = () => console.log(`Force Firebase Logout: Deleted dynamic IndexedDB: ${database.name}`);
                            req.onerror = (e) => console.error(`Force Firebase Logout: Error deleting dynamic IndexedDB:`, e);
                        }
                    });
                }).catch(err => {
                    console.error('Force Firebase Logout: Error listing IndexedDB databases:', err);
                });
            }
        } catch (e) {
            console.error('Force Firebase Logout: Error clearing IndexedDB:', e);
        }
          // Try to clear cookies related to Firebase auth
        try {
            const cookieNames = [
                'firebaseauth', 
                'firebase-auth', 
                'firebase',
                'firebaseToken',
                'firebaseTokenId',
                'firebaseSession',
                'firebase.session',
                'auth',
                'session',
                'user'
            ];
            
            cookieNames.forEach(name => {
                document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
                // Also try with different paths
                document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;domain=${window.location.hostname}`;
                document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;domain=.${window.location.hostname}`;
            });
            
            // Also try to clear any cookies with firebase in the name
            const allCookies = document.cookie.split(';');
            for (let i = 0; i < allCookies.length; i++) {
                const cookiePart = allCookies[i].trim();
                const cookieName = cookiePart.split('=')[0];
                if (cookieName && (
                    cookieName.toLowerCase().includes('firebase') || 
                    cookieName.toLowerCase().includes('auth') || 
                    cookieName.toLowerCase().includes('session') ||
                    cookieName.toLowerCase().includes('token') ||
                    cookieName.toLowerCase().includes('user')
                )) {                    document.cookie = `${cookieName}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
                    document.cookie = `${cookieName}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;domain=${window.location.hostname}`;
                    document.cookie = `${cookieName}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;domain=.${window.location.hostname}`;
                }
            }
        } catch (e) {
            console.error('Force Firebase Logout: Error clearing cookies:', e);
        }
    } catch (e) {
        console.error('Force Firebase Logout: Error in clearAllFirebaseStorage:', e);
    }
};

// Auto-attach to the logout button in settings modal if it exists
document.addEventListener('DOMContentLoaded', function() {
    const logoutBtn = document.getElementById('settings-logout');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function(e) {
            // Prevent default action if it has one
            e.preventDefault();
            
            console.log('Logout button clicked, using enhanced logout');
            
            // Use the enhanced logout function
            logoutUtils.forceFirebaseLogout().then(() => {
                // Redirect to logout_cleanup with cache-busting parameter
                window.location.href = '/logout_cleanup?t=' + new Date().getTime();
            });
        });
    }
});

// Export logout utilities
console.log('Enhanced Firebase logout utilities loaded');
