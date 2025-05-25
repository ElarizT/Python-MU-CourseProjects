/**
 * Force Logout Script
 * This script runs on page load and ensures Firebase authentication is cleared
 * when the explicitly_logged_out flag is set
 */

(function() {
    // Run immediately on script load
    const forceLogout = function() {
        // Check if explicitly logged out flag is set
        const explicitlyLoggedOut = localStorage.getItem('explicitly_logged_out') === 'true';
        
        if (explicitlyLoggedOut) {
            console.log('Force logout script activated: explicit logout flag is set');
            
            // Check if we're on the login, signup, or auth pages
            const isLoginPage = window.location.pathname.includes('/login');
            const isSignupPage = window.location.pathname.includes('/signup');
            const isLogoutPage = window.location.pathname.includes('/logout');
            const isAuthDiagnostics = window.location.pathname.includes('/auth-diagnostics');
            const isAuthPage = isLoginPage || isSignupPage || isLogoutPage || isAuthDiagnostics;
            
            // If on an auth page, don't forcefully log out - the auth page will handle this
            if (isAuthPage) {
                console.log('Force logout: On auth page, the page will handle logout state');
                return;
            }
            
            // Clear Firebase auth cache regardless of whether Firebase is loaded yet
            clearAuthCache();
            
            // Set up auth state listener to detect any persistent auth state
            document.addEventListener('DOMContentLoaded', function() {
                setupPersistentAuthDetection();
            });
            
            // Wait for Firebase to be available
            const checkFirebase = setInterval(() => {
                if (window.firebase && firebase.auth) {
                    clearInterval(checkFirebase);
                    
                    // First try to disable persistence to prevent auto re-login
                    try {
                        firebase.auth().setPersistence(firebase.auth.Auth.Persistence.NONE)
                            .then(() => console.log('Set Firebase persistence to NONE'))
                            .catch(err => console.error('Error setting Firebase persistence:', err));
                    } catch (e) {
                        console.error('Error setting Firebase persistence:', e);
                    }
                    
                    // Sign out from Firebase forcefully
                    firebase.auth().signOut().then(() => {
                        console.log('Force logout: Successfully signed out from Firebase');
                        
                        // Clear any Firebase auth cache
                        clearAuthCache();
                        
                        // Delete Firebase apps if possible
                        try {
                            if (firebase.apps && firebase.apps.length > 0) {
                                Promise.all(firebase.apps.map(app => app.delete()))
                                    .then(() => console.log('Successfully deleted all Firebase apps'))
                                    .catch(e => console.error('Error deleting Firebase apps:', e));
                            }
                        } catch (e) {
                            console.error('Error deleting Firebase apps:', e);
                        }
                    }).catch(error => {
                        console.error('Force logout: Error signing out from Firebase:', error);
                        // Still try to clear cache
                        clearAuthCache();
                    });
                }
            }, 100);
            
            // Set a timeout to give up after 5 seconds
            setTimeout(() => {
                clearInterval(checkFirebase);
                console.log('Force logout: Gave up waiting for Firebase to be available');
            }, 5000);
        }
    };
    
    // Helper function to clear auth cache
    function clearAuthCache() {
        console.log('Force logout: Clearing auth cache');
        
        try {
            // Clear localStorage Firebase items
            for (let i = localStorage.length - 1; i >= 0; i--) {
                const key = localStorage.key(i);
                if (key && (key.startsWith('firebase:') || key.includes('firebase') || key.includes('auth'))) {
                    localStorage.removeItem(key);
                    console.log(`Removed localStorage item: ${key}`);
                }
            }
            
            // Clear sessionStorage Firebase items
            for (let i = sessionStorage.length - 1; i >= 0; i--) {
                const key = sessionStorage.key(i);
                if (key && (key.startsWith('firebase:') || key.includes('firebase') || key.includes('auth'))) {
                    sessionStorage.removeItem(key);
                    console.log(`Removed sessionStorage item: ${key}`);
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
                    'firebase-performance-database'
                ];
                
                dbNames.forEach(dbName => {
                    try {
                        const req = indexedDB.deleteDatabase(dbName);
                        req.onsuccess = () => console.log(`Successfully deleted IndexedDB: ${dbName}`);
                        req.onerror = (e) => console.error(`Error deleting IndexedDB ${dbName}: ${e.target.error}`);
                    } catch (e) {
                        console.error(`Error deleting IndexedDB ${dbName}:`, e);
                    }
                });
                
                // Also try to delete any database with firebase in the name
                if (indexedDB.databases) {
                    indexedDB.databases().then(databases => {
                        databases.forEach(database => {
                            if (database.name && database.name.toLowerCase().includes('firebase')) {
                                const req = indexedDB.deleteDatabase(database.name);
                                req.onsuccess = () => console.log(`Successfully deleted dynamic IndexedDB: ${database.name}`);
                                req.onerror = () => console.error(`Error deleting dynamic IndexedDB: ${database.name}`);
                            }
                        });
                    }).catch(err => {
                        console.error('Error listing IndexedDB databases:', err);
                    });
                }
            } catch (e) {
                console.error(`Error clearing IndexedDB: ${e.message}`);
            }
            
            // Clear cookies
            try {
                const cookieNames = ['firebaseauth', 'firebase-auth', 'firebase'];
                cookieNames.forEach(name => {
                    document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
                });
                
                // Also try to clear any cookies with firebase in the name
                const allCookies = document.cookie.split(';');
                for (let i = 0; i < allCookies.length; i++) {
                    const cookiePart = allCookies[i].trim();
                    const cookieName = cookiePart.split('=')[0];
                    if (cookieName && (cookieName.toLowerCase().includes('firebase') || cookieName.toLowerCase().includes('auth'))) {
                        document.cookie = `${cookieName}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
                        console.log(`Cleared cookie: ${cookieName}`);
                    }
                }
            } catch (e) {
                console.error('Error clearing cookies:', e);
            }
        } catch (e) {
            console.error('Error in clearAuthCache:', e);
        }
    }
    
    // Function to setup detection for persistent authentication state
    function setupPersistentAuthDetection() {
        console.log('Setting up persistent auth detection');
        
        // Check immediately
        if (window.firebase && firebase.auth) {
            checkForLoggedInUserState();
        }
        
        // Also set up an interval to check multiple times
        let checkCount = 0;
        const maxChecks = 30;
        const checkInterval = setInterval(() => {
            if (window.firebase && firebase.auth) {
                checkForLoggedInUserState();
            }
            
            checkCount++;
            if (checkCount >= maxChecks) {
                clearInterval(checkInterval);
                console.log('Completed persistent auth state detection checks');
            }
        }, 1000);
    }
    
    // Function to check for logged in user state
    function checkForLoggedInUserState() {
        firebase.auth().onAuthStateChanged(user => {
            if (user && localStorage.getItem('explicitly_logged_out') === 'true') {
                console.warn(`Force logout: Detected persistent user state for ${user.email} even though logout flag is set!`);
                console.log('Force logout: Taking aggressive action to clear persistent state');
                
                // Clear cache again
                clearAuthCache();
                
                // Try to sign out
                firebase.auth().signOut().then(() => {
                    console.log('Force logout: Successfully signed out persistent user');
                    
                    // Delete apps if possible
                    if (firebase.apps && firebase.apps.length > 0) {
                        Promise.all(firebase.apps.map(app => app.delete()))
                            .then(() => console.log('Force logout: Successfully deleted all Firebase apps'))
                            .catch(e => console.error('Force logout: Error deleting Firebase apps:', e));
                    }
                    
                    // One more cache clear
                    setTimeout(() => {
                        clearAuthCache();
                        
                        // Redirect to the logout cleanup page
                        window.location.href = `/logout_cleanup?t=${new Date().getTime()}`;
                    }, 100);
                }).catch(error => {
                    console.error('Force logout: Error signing out persistent user:', error);
                    
                    // Try harder - redirect to logout
                    window.location.href = `/logout_cleanup?t=${new Date().getTime()}`;
                });
            }
        });
    }
    
    // Run the force logout
    forceLogout();
})();
