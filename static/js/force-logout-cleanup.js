/**
 * Force Logout Function for Firebase Auth Watchdog
 * This script adds enhanced logout functionality to the Firebase Auth Watchdog.
 */

// Wait for the document to be ready
document.addEventListener('DOMContentLoaded', function() {
    // Add the force logout function to the page
    if (typeof window.forceLogoutCleanup === 'undefined') {
        /**
         * Force a complete Firebase logout and cleanup
         * Called by the auth watchdog when Firebase auth state doesn't match server state
         */
        window.forceLogoutCleanup = async function() {
            console.log('[FORCE-LOGOUT] Starting aggressive Firebase auth cleanup');
            
            // 1. Set explicit logout flags in both storage types
            localStorage.setItem('explicitly_logged_out', 'true');
            sessionStorage.setItem('explicitly_logged_out', 'true');
            
            try {
                // 2. Get current user details if available for token revocation
                let currentToken = null;
                let uid = null;
                
                if (typeof firebase !== 'undefined' && firebase.auth && firebase.auth().currentUser) {
                    const user = firebase.auth().currentUser;
                    uid = user.uid;
                    console.log('[FORCE-LOGOUT] Current user before force logout:', user.email);
                    
                    try {
                        currentToken = await user.getIdToken();
                        console.log('[FORCE-LOGOUT] Retrieved token for revocation');
                    } catch (tokenError) {
                        console.error('[FORCE-LOGOUT] Error getting token:', tokenError);
                    }
                }
                
                // 3. Clear all auth-related storage before attempting operations
                clearAllAuthStorageAggressive();
                  // 4. Change Firebase persistence to NONE before logout
                if (typeof firebase !== 'undefined' && firebase.auth) {
                    try {
                        await firebase.auth().setPersistence(firebase.auth.Auth.Persistence.NONE);
                        console.log('[FORCE-LOGOUT] Set Firebase persistence to NONE');
                    } catch (e) {
                        console.error('[FORCE-LOGOUT] Error setting persistence:', e);
                    }
                }
                
                // 5. Revoke token on server if we have one
                if (currentToken) {
                    try {
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
                            console.log('[FORCE-LOGOUT] Successfully revoked token on server');
                        } else {
                            console.warn('[FORCE-LOGOUT] Failed to revoke token:', await revokeResponse.text());
                        }
                    } catch (revokeError) {
                        console.error('[FORCE-LOGOUT] Error revoking token:', revokeError);
                    }
                } else if (uid) {
                    // If we couldn't get the token but have a user ID, try to revoke by user ID
                    try {
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
                            console.log('[FORCE-LOGOUT] Successfully revoked tokens for user ID');
                        } else {
                            console.warn('[FORCE-LOGOUT] Failed to revoke tokens by user ID');
                        }
                    } catch (revokeError) {
                        console.error('[FORCE-LOGOUT] Error revoking tokens by user ID:', revokeError);
                    }
                }
                  // 6. Sign out from the server side
                const serverLogoutResponse = await fetch('/api/auth/signout', { 
                    method: 'POST',
                    headers: {
                        'Cache-Control': 'no-cache, no-store, must-revalidate',
                        'Pragma': 'no-cache',
                        'Expires': '0'
                    }
                });
                
                if (serverLogoutResponse.ok) {
                    console.log('[FORCE-LOGOUT] Server-side logout successful');
                } else {
                    console.warn('[FORCE-LOGOUT] Server-side logout error');
                }
                
                // 7. Final storage cleanup before Firebase signOut
                clearAllAuthStorageAggressive();
                
                // 8. Call Firebase signOut AFTER server and token revocation
                if (typeof firebase !== 'undefined' && firebase.auth) {
                    try {
                        await firebase.auth().signOut();
                        console.log('[FORCE-LOGOUT] Firebase auth signOut successful');
                    } catch (signOutError) {
                        console.error('[FORCE-LOGOUT] Error in Firebase signOut:', signOutError);
                    }
                }
                
                // 9. Final storage cleanup after all operations
                clearAllAuthStorageAggressive();
                  // 10. Delete Firebase apps if possible to fully reset state
                if (typeof firebase !== 'undefined' && firebase.apps && firebase.apps.length > 0) {
                    try {
                        await Promise.all(firebase.apps.map(app => app.delete()));
                        console.log('[FORCE-LOGOUT] Successfully deleted all Firebase apps');
                    } catch (deleteError) {
                        console.error('[FORCE-LOGOUT] Error deleting Firebase apps:', deleteError);
                    }
                }
                
                // 11. Consider refreshing the page if we're not already on a login or logout page
                const currentPath = window.location.pathname.toLowerCase();
                if (!currentPath.includes('login') && !currentPath.includes('logout') && 
                    !currentPath.includes('signup') && !currentPath.includes('auth')) {
                    // We're not on an auth page, might need to reload
                    console.log('[FORCE-LOGOUT] Not on an auth page, consider redirecting to logout page');
                    // Uncomment the following line if you want to force redirect
                    // window.location.href = '/logout_cleanup?t=' + new Date().getTime();
                }
                
                console.log('[FORCE-LOGOUT] Force logout completed successfully');
                return true;
            } catch (error) {
                console.error('[FORCE-LOGOUT] Error in force logout:', error);
                return false;
            }
        };
        
        /**
         * More aggressive version of storage clearance for auth-related data
         */
        function clearAllAuthStorageAggressive() {
            console.log('[FORCE-LOGOUT] Clearing all auth storage aggressively');
            
            // Clear localStorage
            const knownLocalStorageKeys = [
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
                    console.log('[FORCE-LOGOUT] Detected project ID for targeted cleanup:', projectId);
                    
                    // Add project-specific keys if we found a project ID
                    if (projectId) {
                        knownLocalStorageKeys.push(`firebase:authUser:${projectId}`);
                        knownLocalStorageKeys.push(`firebase:previous-user:${projectId}`);
                    }
                }
            } catch (error) {
                console.error('[FORCE-LOGOUT] Error detecting project ID:', error);
            }
            
            // Clear all known keys
            knownLocalStorageKeys.forEach(key => {
                try {
                    localStorage.removeItem(key);
                    console.log(`[FORCE-LOGOUT] Cleared localStorage key: ${key}`);
                } catch (e) {
                    console.error(`[FORCE-LOGOUT] Error clearing localStorage key ${key}:`, e);
                }
            });
            
            // Clear any Firebase-related keys
            for (let i = localStorage.length - 1; i >= 0; i--) {
                const key = localStorage.key(i);
                if (key && (
                    key.startsWith('firebase:') || 
                    key.includes('firebase') || 
                    // key.includes('auth') || // Avoid deleting explicitly_logged_out
                    key.includes('token')
                )) {
                    try {
                        localStorage.removeItem(key);
                        console.log(`[FORCE-LOGOUT] Cleared dynamic localStorage key: ${key}`);
                    } catch (e) {
                        console.error(`[FORCE-LOGOUT] Error clearing localStorage key ${key}:`, e);
                    }
                }
            }
            
            // Clear sessionStorage as well
            for (let i = sessionStorage.length - 1; i >= 0; i--) {
                const key = sessionStorage.key(i);
                if (key && (
                    key.startsWith('firebase:') || 
                    key.includes('firebase') || 
                    // key.includes('auth') || // Avoid deleting explicitly_logged_out
                    key.includes('token')
                )) {
                    try {
                        sessionStorage.removeItem(key);
                        console.log(`[FORCE-LOGOUT] Cleared sessionStorage key: ${key}`);
                    } catch (e) {
                        console.error(`[FORCE-LOGOUT] Error clearing sessionStorage key ${key}:`, e);
                    }
                }
            }
            
            // Clear IndexedDB if available
            try {
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
                        req.onsuccess = () => console.log(`[FORCE-LOGOUT] Successfully deleted IndexedDB: ${dbName}`);
                        req.onerror = (err) => console.error(`[FORCE-LOGOUT] Error deleting IndexedDB ${dbName}:`, err);
                    } catch (e) {
                        console.error(`[FORCE-LOGOUT] Error with IndexedDB operation on ${dbName}:`, e);
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
                                req.onsuccess = () => console.log(`[FORCE-LOGOUT] Successfully deleted dynamic IndexedDB: ${database.name}`);
                                req.onerror = (err) => console.error(`[FORCE-LOGOUT] Error deleting dynamic IndexedDB ${database.name}:`, err);
                            }
                        });
                    }).catch(err => {
                        console.error('[FORCE-LOGOUT] Error listing IndexedDB databases:', err);
                    });
                }
            } catch (e) {
                console.error('[FORCE-LOGOUT] Error clearing IndexedDB:', e);
            }
            
            // Clear cookies related to Firebase auth
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
                    console.log(`[FORCE-LOGOUT] Cleared cookie: ${name}`);
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
                    )) {
                        document.cookie = `${cookieName}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
                        document.cookie = `${cookieName}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;domain=${window.location.hostname}`;
                        document.cookie = `${cookieName}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;domain=.${window.location.hostname}`;
                        console.log(`[FORCE-LOGOUT] Cleared dynamic cookie: ${cookieName}`);
                    }
                }
            } catch (e) {
                console.error('[FORCE-LOGOUT] Error clearing cookies:', e);
            }
        }
        
        console.log('Force logout cleanup utility initialized');
    }
});
