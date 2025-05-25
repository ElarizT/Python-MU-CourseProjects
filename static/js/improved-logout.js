/**
 * Improved Firebase Logout
 * 
 * This script provides a robust and complete Firebase logout process
 * that ensures the user is fully logged out without any persisted auth state.
 */

// Self-executing function to avoid polluting global namespace
(function() {
    'use strict';
    
    // Create the FirebaseLogout global object
    window.FirebaseLogout = {
        /**
         * Perform a complete Firebase logout
         * This handles clearing all storage and tokens
         */
        logoutCompletely: async function() {
            console.log('Starting complete Firebase logout process');
            
            // 1. Set explicit logout flag
            localStorage.setItem('explicitly_logged_out', 'true');
            
            try {
                // 2. Revoke token if we have a current user
                if (firebase.auth().currentUser) {
                    try {
                        const token = await firebase.auth().currentUser.getIdToken();
                        
                        // Send token to server for revocation
                        await fetch('/api/auth/revoke-token', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'Cache-Control': 'no-cache, no-store, must-revalidate',
                                'Pragma': 'no-cache',
                                'Expires': '0'
                            },
                            body: JSON.stringify({ token: token })
                        });
                        
                        console.log('Token revocation request sent');
                    } catch (e) {
                        console.error('Error getting token for revocation:', e);
                    }
                }
                
                // 3. Set persistence to NONE to prevent auto-relogin
                await firebase.auth().setPersistence(firebase.auth.Auth.Persistence.NONE);
                console.log('Set Firebase persistence to NONE');
                
                // 4. Sign out from Firebase
                await firebase.auth().signOut();
                console.log('Successfully signed out from Firebase');
                
                // 5. Call server-side logout
                const logoutResponse = await fetch('/api/auth/signout', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Cache-Control': 'no-cache, no-store, must-revalidate',
                        'Pragma': 'no-cache',
                        'Expires': '0'
                    }
                });
                
                if (logoutResponse.ok) {
                    console.log('Server-side logout successful');
                } else {
                    console.warn('Server-side logout failed:', await logoutResponse.text());
                }
                
            } catch (e) {
                console.error('Error during Firebase logout:', e);
            }
            
            // 6. Clear all storage regardless of errors above
            this.clearAllStorage();
            
            console.log('Firebase logout process completed');
            return true;
        },
        
        /**
         * Clear all Firebase-related storage
         */
        clearAllStorage: function() {
            console.log('Clearing all Firebase storage');
            
            // Clear localStorage
            const localStorageKeys = [];
            for (let i = 0; i < localStorage.length; i++) {
                localStorageKeys.push(localStorage.key(i));
            }
            
            localStorageKeys.forEach(key => {
                if (key && (
                    key.startsWith('firebase:') || 
                    key.includes('firebase') || 
                    key.includes('auth') ||
                    key.includes('user')
                )) {
                    localStorage.removeItem(key);
                    console.log('Removed localStorage item:', key);
                }
            });
            
            // Clear sessionStorage
            const sessionStorageKeys = [];
            for (let i = 0; i < sessionStorage.length; i++) {
                sessionStorageKeys.push(sessionStorage.key(i));
            }
            
            sessionStorageKeys.forEach(key => {
                if (key && (
                    key.startsWith('firebase:') || 
                    key.includes('firebase') || 
                    key.includes('auth') ||
                    key.includes('user')
                )) {
                    sessionStorage.removeItem(key);
                    console.log('Removed sessionStorage item:', key);
                }
            });
            
            // Clear IndexedDB
            try {
                const dbNames = [
                    'firebaseLocalStorageDb', 
                    'firebase-heartbeat-database',
                    'firebase-installations-database',
                    'firebase-messaging-database',
                    'firebase-analytics-database'
                ];
                
                dbNames.forEach(dbName => {
                    const req = indexedDB.deleteDatabase(dbName);
                    req.onsuccess = () => console.log(`Successfully deleted IndexedDB: ${dbName}`);
                    req.onerror = (e) => console.error(`Error deleting IndexedDB ${dbName}: ${e.target.error}`);
                });
                
                // Try to dynamically find and delete any Firebase DBs
                if (indexedDB.databases) {
                    indexedDB.databases().then(dbs => {
                        dbs.forEach(db => {
                            if (db.name.includes('firebase') || db.name.includes('auth')) {
                                const req = indexedDB.deleteDatabase(db.name);
                                req.onsuccess = () => console.log(`Successfully deleted dynamic IndexedDB: ${db.name}`);
                            }
                        });
                    }).catch(e => console.error('Error listing databases:', e));
                }
            } catch (e) {
                console.error('Error clearing IndexedDB:', e);
            }
            
            // Clear cookies
            document.cookie.split(';').forEach(cookie => {
                const cookieName = cookie.split('=')[0].trim();
                if (cookieName.includes('firebase') || cookieName.includes('auth')) {
                    document.cookie = `${cookieName}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
                    console.log('Cleared cookie:', cookieName);
                }
            });
        },
        
        /**
         * Redirect to logout page for visual feedback
         */
        redirectToLogoutPage: function() {
            window.location.href = '/logout_cleanup';
        },
        
        /**
         * Complete logout process with redirect
         */
        logout: async function() {
            // Show loading if available
            if (window.LoadingManager) {
                window.LoadingManager.showLoading('Signing out...');
            }
            
            try {
                await this.logoutCompletely();
                
                // Redirect to logout page
                this.redirectToLogoutPage();
            } catch (e) {
                console.error('Error during logout:', e);
                
                // Still redirect even if error
                this.redirectToLogoutPage();
            }
        }
    };
})();
