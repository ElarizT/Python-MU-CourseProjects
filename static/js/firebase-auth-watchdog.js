/**
 * Firebase Auth State Watchdog
 * 
 * This script runs in the background to continuously monitor Firebase auth state
 * and ensure that it correctly reflects the user's session state. If the auth
 * state becomes out of sync with the session state, it will take corrective action.
 * 
 * This is especially useful for fixing persistent auth states even after logout.
 */

(function() {
    'use strict';
      // Configuration
    const CONFIG = {
        checkIntervalSeconds: 10,     // How often to check auth state while page is open (increased from 5)
        maxCheckDuration: 300,        // Maximum duration to keep checking (seconds)
        debugMode: false              // Set to false for less verbose logging
    };
    
    // Keep track of monitoring state
    let monitoringStartTime = null;
    let checkIntervalId = null;
    let watchdogActive = false;
    
    // Initialize on page load
    window.addEventListener('DOMContentLoaded', function() {
        // Start the auth state watchdog
        startAuthStateWatchdog();
    });
    
    /**
     * Start the auth state watchdog to monitor and correct Firebase auth state
     */
    function startAuthStateWatchdog() {
        if (watchdogActive) {
            return; // Already running
        }
        
        // Record the start time
        monitoringStartTime = Date.now();
        watchdogActive = true;
        
        // Log the watchdog activation
        logDebug('Firebase Auth Watchdog activated');
        
        // Do an immediate check
        performAuthStateCheck();
        
        // Set up interval for continued monitoring
        checkIntervalId = setInterval(function() {
            // Check if we've exceeded the maximum duration
            const elapsedSeconds = (Date.now() - monitoringStartTime) / 1000;
            if (elapsedSeconds > CONFIG.maxCheckDuration) {
                stopAuthStateWatchdog();
                logDebug(`Auth watchdog stopped after ${elapsedSeconds.toFixed(1)}s (max duration reached)`);
                return;
            }
            
            // Perform the check
            performAuthStateCheck();
        }, CONFIG.checkIntervalSeconds * 1000);
    }
    
    /**
     * Stop the auth state watchdog
     */
    function stopAuthStateWatchdog() {
        if (checkIntervalId) {
            clearInterval(checkIntervalId);
            checkIntervalId = null;
        }
        watchdogActive = false;
    }
    
    /**
     * Check the current Firebase auth state and session status for inconsistencies
     */
    function performAuthStateCheck() {
        const isExplicitlyLoggedOut = localStorage.getItem('explicitly_logged_out') === 'true';
        
        // Skip auth pages to avoid interfering with the login flow
        const isAuthPage = window.location.pathname.includes('/login') || 
                          window.location.pathname.includes('/signup') ||
                          window.location.pathname.includes('/logout');
        
        if (isAuthPage) {
            logDebug('Auth watchdog: On auth page, skipping check');
            return;
        }
        
        // Check if Firebase is available
        if (typeof firebase === 'undefined' || !firebase.auth) {
            // We can't check the auth state if Firebase isn't available
            logDebug('Auth watchdog: Firebase not available, skipping check');
            return;
        }
        
        // Check if Firebase instance has been invalidated
        try {
            // This will throw if firebase is no longer properly initialized
            firebase.app();
        } catch (e) {
            logDebug('Auth watchdog: Firebase instance invalid, skipping check');
            return;
        }
        
        // Get the current auth state
        firebase.auth().onAuthStateChanged(function(user) {
            if (user && isExplicitlyLoggedOut) {
                // This is the problematic state we're looking for:
                // Firebase thinks user is logged in but our app knows they logged out
                logDebug(`Auth watchdog detected CRITICAL AUTH STATE MISMATCH: Firebase reports user ${user.email} is logged in, but explicitly_logged_out flag is set!`);
                
                // Use our enhanced force logout function if available
                if (typeof window.forceLogoutCleanup === 'function') {
                    logDebug('Auth watchdog using enhanced force logout cleanup...');
                    window.forceLogoutCleanup().then(() => {
                        logDebug('Force logout cleanup completed');
                    }).catch(err => {
                        logDebug(`Force logout cleanup error: ${err}`);
                    });
                } else {
                    // Take immediate corrective action with the old method
                    logDebug('Auth watchdog is performing corrective action (legacy method)...');
                    performCriticalAuthReset(user.email);
                }
            } else if (user) {
                // User is logged in according to Firebase - this is expected during normal use
                logDebug(`Auth watchdog: User is logged in (${user.email}), which is consistent with session state`);
                
                // Verify with the server that this user session is valid
                verifyServerSession();
            } else if (isExplicitlyLoggedOut) {
                // User is logged out and explicit_logout flag is set - this is correct
                logDebug('Auth watchdog: User is logged out and explicit_logout flag is set (correct state)');
            } else {
                // User is logged out but explicit_logout flag is not set
                // This is a normal state when the user hasn't logged in yet
                logDebug('Auth watchdog: User is not logged in');
            }
        });
    }    /**
     * Verify with the server that the current session is valid
     */
    function verifyServerSession(user) {
        // Fetch the session status from the server
        fetch('/api/auth/session', {
            method: 'GET',
            headers: {
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            }
        })
        .then(response => response.json())
        .then(async data => {
            // Check if the server reports user is explicitly logged out
            if (data.explicitly_logged_out === true) {
                // Server says user is logged out, but Firebase says logged in - mismatch!
                logDebug('Auth watchdog: Server reports explicit logout but Firebase shows logged in state!');
                
                // Set the local flag to match server state
                localStorage.setItem('explicitly_logged_out', 'true');
                sessionStorage.setItem('explicitly_logged_out', 'true');
                
                // Use enhanced force logout if available
                if (typeof window.forceLogoutCleanup === 'function') {
                    try {
                        await window.forceLogoutCleanup();
                        logDebug('Force logout cleanup completed after server session mismatch');
                    } catch (e) {
                        logDebug(`Force logout cleanup error: ${e}`);
                    }
                } else {
                    // Force logout in next cycle with legacy method
                    setTimeout(() => performCriticalAuthReset(user?.email || 'unknown'), 100);
                }
            } else if (data.authenticated === false && user) {
                // Server says user is not authenticated but Firebase says logged in
                logDebug('Auth watchdog: Server reports unauthenticated but Firebase shows logged in!');
                
                // Use enhanced force logout if available
                if (typeof window.forceLogoutCleanup === 'function') {
                    try {
                        await window.forceLogoutCleanup();
                        logDebug('Force logout cleanup completed after auth state mismatch');
                    } catch (e) {
                        logDebug(`Force logout cleanup error: ${e}`);
                    }
                } else {
                    // Perform corrective action on next cycle with legacy method 
                    setTimeout(() => performCriticalAuthReset(user.email), 100);
                }
            } else {
                logDebug('Auth watchdog: Server session verification successful');
            }
        })
        .catch(error => {
            logDebug(`Auth watchdog: Error verifying server session: ${error}`);
        });
    }
    
    /**
     * Perform a critical auth reset when a serious auth state mismatch is detected
     * This is a more aggressive version of the normal logout process
     */
    async function performCriticalAuthReset(email) {
        logDebug(`AUTH WATCHDOG CRITICAL RESET: Starting for ${email}`);
        
        try {
            // 1. Ensure the explicit logout flag is set
            localStorage.setItem('explicitly_logged_out', 'true');
            sessionStorage.setItem('explicitly_logged_out', 'true');
            
            // 2. Attempt to get the token to revoke it server-side
            let token = null;
            try {
                const user = firebase.auth().currentUser;
                if (user) {
                    token = await user.getIdToken();
                    logDebug('Auth watchdog: Retrieved token for server-side revocation');
                }
            } catch (tokenError) {
                logDebug(`Auth watchdog: Error getting token: ${tokenError}`);
            }
            
            // 3. Force a complete logout with most aggressive settings
            try {
                // Set persistence to NONE
                await firebase.auth().setPersistence(firebase.auth.Auth.Persistence.NONE);
                logDebug('Auth watchdog: Set Firebase persistence to NONE');
                
                // Perform signout
                await firebase.auth().signOut();
                logDebug('Auth watchdog: Successfully signed out from Firebase');
            } catch (authError) {
                logDebug(`Auth watchdog: Error in Firebase signout: ${authError}`);
            }
            
            // 4. Clear all storage
            clearAllAuthStorage();
              // 5. Revoke token on server if we have one
            if (token) {
                try {
                    const response = await fetch('/api/auth/revoke-token', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Cache-Control': 'no-cache, no-store, must-revalidate'
                        },
                        body: JSON.stringify({ token: token })
                    });
                    
                    if (response.ok) {
                        logDebug('Auth watchdog: Successfully revoked token on server');
                    } else {
                        logDebug('Auth watchdog: Failed to revoke token on server');
                    }
                } catch (revokeError) {
                    logDebug(`Auth watchdog: Error revoking token: ${revokeError}`);
                }
            } else if (firebase.auth().currentUser) {
                // If we couldn't get the token but have a user ID, try to revoke by user ID
                try {
                    const uid = firebase.auth().currentUser.uid;
                    const response = await fetch('/api/auth/revoke-token', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Cache-Control': 'no-cache, no-store, must-revalidate'
                        },
                        body: JSON.stringify({ user_id: uid })
                    });
                    
                    if (response.ok) {
                        logDebug('Auth watchdog: Successfully revoked token by user ID on server');
                    } else {
                        logDebug('Auth watchdog: Failed to revoke token by user ID on server');
                    }
                } catch (revokeError) {
                    logDebug(`Auth watchdog: Error revoking token by user ID: ${revokeError}`);
                }
            }
            
            // 6. Reload the page to ensure a completely fresh state
            if (!isOnAuthPage()) {
                logDebug('Auth watchdog: Reloading page to ensure clean state...');
                window.location.href = `/logout_cleanup?t=${new Date().getTime()}`;
            }
        } catch (error) {
            logDebug(`Auth watchdog critical reset error: ${error}`);
        }
    }
    
    /**
     * Clear all storage related to authentication state
     */
    function clearAllAuthStorage() {
        logDebug('Auth watchdog: Clearing all auth-related storage');
        
        // Clear localStorage
        const knownLocalStorageKeys = [
            'firebase:authUser',
            'firebase:previous-user',
            'firebase:remember',
            'firebase:forceRefresh',
            'firebase:redirectUser',
            'firebase:persistence',
            'firebase:pendingRedirect',
            'firebaseToken'
        ];
        
        // Get project ID if available for more targeted cleanup
        let projectId = null;
        try {
            const authDomain = document.querySelector('meta[name="firebase-auth-domain"]')?.content;
            if (authDomain) {
                projectId = authDomain.split('.')[0];
                knownLocalStorageKeys.push(`firebase:authUser:${projectId}`);
                knownLocalStorageKeys.push(`firebase:previous-user:${projectId}`);
            }
        } catch (e) {
            logDebug(`Auth watchdog: Error getting project ID: ${e}`);
        }
        
        // Clear known localStorage keys
        knownLocalStorageKeys.forEach(key => {
            try {
                localStorage.removeItem(key);
            } catch (e) {
                logDebug(`Auth watchdog: Error clearing localStorage key ${key}: ${e}`);
            }
        });
        
        // Clear any key that looks like Firebase auth
        for (let i = localStorage.length - 1; i >= 0; i--) {
            const key = localStorage.key(i);
            if (key && (
                key.startsWith('firebase:') || 
                key.includes('firebase') || 
                key.includes('auth') ||
                key.includes('token')
            )) {
                localStorage.removeItem(key);
            }
        }
        
        // Clear sessionStorage as well
        for (let i = sessionStorage.length - 1; i >= 0; i--) {
            const key = sessionStorage.key(i);
            if (key && (
                key.startsWith('firebase:') || 
                key.includes('firebase') || 
                key.includes('auth') ||
                key.includes('token')
            )) {
                sessionStorage.removeItem(key);
            }
        }
        
        // Clear IndexedDB
        try {
            const dbNames = [
                'firebaseLocalStorageDb', 
                'firebase-heartbeat-database',
                'firebase-installations-database',
                'firebase-messaging-database',
                'firebase-analytics-database',
                'firebase-performance-database',
                'firebase-auth',
                'firebase-auth-state'
            ];
            
            dbNames.forEach(dbName => {
                try {
                    const req = indexedDB.deleteDatabase(dbName);
                    req.onsuccess = () => logDebug(`Auth watchdog: Deleted IndexedDB: ${dbName}`);
                    req.onerror = (e) => logDebug(`Auth watchdog: Error deleting IndexedDB ${dbName}: ${e}`);
                } catch (e) {
                    logDebug(`Auth watchdog: Error with IndexedDB ${dbName}: ${e}`);
                }
            });
            
            // Also try to delete any database with firebase in the name
            if (indexedDB.databases) {
                indexedDB.databases().then(databases => {
                    databases.forEach(database => {
                        if (database.name && (
                            database.name.toLowerCase().includes('firebase') || 
                            database.name.toLowerCase().includes('auth') || 
                            database.name.toLowerCase().includes('credential')
                        )) {
                            const req = indexedDB.deleteDatabase(database.name);
                            req.onsuccess = () => logDebug(`Auth watchdog: Deleted dynamic IndexedDB: ${database.name}`);
                            req.onerror = (e) => logDebug(`Auth watchdog: Error deleting dynamic IndexedDB: ${e}`);
                        }
                    });
                }).catch(err => {
                    logDebug(`Auth watchdog: Error listing IndexedDB databases: ${err}`);
                });
            }
        } catch (e) {
            logDebug(`Auth watchdog: Error clearing IndexedDB: ${e}`);
        }
        
        // Clear cookies
        try {
            const cookieNames = [
                'firebaseauth', 
                'firebase-auth', 
                'firebase',
                'firebaseToken',
                'auth',
                'session'
            ];
            
            cookieNames.forEach(name => {
                document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
                document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;domain=${window.location.hostname}`;
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
                    cookieName.toLowerCase().includes('token')
                )) {
                    document.cookie = `${cookieName}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
                    document.cookie = `${cookieName}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;domain=${window.location.hostname}`;
                }
            }
        } catch (e) {
            logDebug(`Auth watchdog: Error clearing cookies: ${e}`);
        }
    }
    
    /**
     * Check if the current page is an auth page
     */
    function isOnAuthPage() {
        return window.location.pathname.includes('/login') || 
               window.location.pathname.includes('/signup') ||
               window.location.pathname.includes('/logout');
    }
    
    /**
     * Log debug messages if debugMode is enabled
     */
    function logDebug(message) {
        if (CONFIG.debugMode) {
            console.log(`[AUTH-WATCHDOG] ${message}`);
        }
    }
})();
