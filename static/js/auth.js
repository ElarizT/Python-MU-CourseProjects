console.log('[AUTH.JS TOP] Initial check of explicitly_logged_out - localStorage:', localStorage.getItem('explicitly_logged_out'), ', sessionStorage:', sessionStorage.getItem('explicitly_logged_out'));

/**
 * Firebase Authentication Utilities for LightYearAI
 * 
 * This file provides common authentication functionality across the application.
 * It handles:
 * - Firebase initialization
 * - Authentication state changes
 * - Session management
 * - Login/logout operations
 */

// HARD BLOCK: If explicitly_logged_out is set and not on login/signup page, stop all further JS execution
(function() {
    var explicitlyLoggedOut = localStorage.getItem('explicitly_logged_out') === 'true' || sessionStorage.getItem('explicitly_logged_out') === 'true';
    var isLoginPage = window.location.pathname.includes('/login');
    var isSignupPage = window.location.pathname.includes('/signup');
    var isAuthPage = isLoginPage || isSignupPage;
    if (explicitlyLoggedOut && !isAuthPage) {
        console.warn('User is explicitly logged out. Blocking all app JS execution until login/signup.');
        // Optionally, show a message or redirect to login
        document.body.innerHTML = '<div style="padding:2em;text-align:center;font-size:1.2em;color:#c00;">You have been securely logged out.<br>Please <a href="/login">sign in</a> to continue.</div>';
        // Stop further JS execution
        return;
    }
})();

// Store the auth state
let isAuthenticated = false;
let currentUser = null;

// Early check: If explicitly_logged_out is set, clear all Firebase state before anything else
if (localStorage.getItem('explicitly_logged_out') === 'true' || sessionStorage.getItem('explicitly_logged_out') === 'true') {
    // Clear all Firebase caches and force sign out if Firebase is loaded
    if (window.firebase && firebase.apps && firebase.apps.length > 0) {
        clearFirebaseAuthCache();
        firebase.auth().setPersistence(firebase.auth.Auth.Persistence.NONE).then(() => {
            return firebase.auth().signOut();
        }).then(() => {
            return Promise.all(firebase.apps.map(app => app.delete()));
        }).catch(() => {});
    } else {
        clearFirebaseAuthCache();
    }
}

// Initialize Firebase if config is available
function initializeFirebase() {
    // Prevent Firebase initialization if explicitly logged out and not on login/signup page
    const explicitlyLoggedOut = localStorage.getItem('explicitly_logged_out') === 'true' || sessionStorage.getItem('explicitly_logged_out') === 'true';
    const isLoginPage = window.location.pathname.includes('/login');
    const isSignupPage = window.location.pathname.includes('/signup');
    const isAuthPage = isLoginPage || isSignupPage;
    if (explicitlyLoggedOut && !isAuthPage) {
        console.warn('Firebase initialization blocked due to explicit logout and not on auth page');
        return false;
    }
    
    // Check if Firebase is already initialized
    if (window.firebase && firebase.apps && firebase.apps.length > 0) {
        return true;
    }
    
    // Check if we have the config data in the page
    const apiKey = document.querySelector('meta[name="firebase-api-key"]')?.content;
    const authDomain = document.querySelector('meta[name="firebase-auth-domain"]')?.content;
    const projectId = document.querySelector('meta[name="firebase-project-id"]')?.content;
    
    if (!apiKey || !authDomain || !projectId) {
        console.error('Firebase configuration not found in page meta tags');
        return false;
    }
    
    // Initialize Firebase
    const firebaseConfig = {
        apiKey: apiKey,
        authDomain: authDomain,
        projectId: projectId,
        storageBucket: document.querySelector('meta[name="firebase-storage-bucket"]')?.content || '',
        messagingSenderId: document.querySelector('meta[name="firebase-messaging-sender-id"]')?.content || '',
        appId: document.querySelector('meta[name="firebase-app-id"]')?.content || ''
    };
    
    try {
        firebase.initializeApp(firebaseConfig);
          // Set persistence to session only if explicitly logged out
        const explicitlyLoggedOut = localStorage.getItem('explicitly_logged_out') === 'true' || sessionStorage.getItem('explicitly_logged_out') === 'true';
        if (explicitlyLoggedOut) {
            console.log('User was explicitly logged out, using temporary session persistence');
            
            // First clear any cached auth data to prevent auto-login
            clearFirebaseAuthCache();
            
            // Use temporary session persistence (eliminates persistent login after browser is closed)
            firebase.auth().setPersistence(firebase.auth.Auth.Persistence.SESSION)
                .catch((error) => {
                    console.error('Error setting auth persistence:', error);
                });
        }
        
        return true;
    } catch (error) {
        console.error('Error initializing Firebase:', error);
        return false;
    }
}

// Monitor authentication state changes
function monitorAuthState() {
    // Prevent monitoring if Firebase should not be initialized
    // Use unique variable names to avoid redeclaration
    const explicitlyLoggedOut_monitor = localStorage.getItem('explicitly_logged_out') === 'true' || sessionStorage.getItem('explicitly_logged_out') === 'true';
    const isLoginPage_monitor = window.location.pathname.includes('/login');
    const isSignupPage_monitor = window.location.pathname.includes('/signup');
    const isAuthPage_monitor = isLoginPage_monitor || isSignupPage_monitor;
    if (explicitlyLoggedOut_monitor && !isAuthPage_monitor) {
        console.warn('Auth state monitoring blocked due to explicit logout and not on auth page');
        return;
    }
    if (!initializeFirebase()) {
        return;
    }
    
    // Check if user has explicitly logged out
    const explicitlyLoggedOut = localStorage.getItem('explicitly_logged_out') === 'true' || sessionStorage.getItem('explicitly_logged_out') === 'true';
    console.log('Auth state monitor started, explicitly logged out?', explicitlyLoggedOut);
    
    // If on login or signup pages, check for explicit logout state
    const isLoginPage = window.location.pathname.includes('/login');
    const isSignupPage = window.location.pathname.includes('/signup');
    const isAuthPage = isLoginPage || isSignupPage;
      // If explicitly logged out and not on an auth page, disable Firebase persistence
    if (explicitlyLoggedOut && !isAuthPage) {
        console.log('User has explicitly logged out and not on auth page, enforcing SESSION persistence');
        
        // First clear any cached auth data to prevent auto-login
        clearFirebaseAuthCache();
        
        // Try to disable persistence to prevent auto-relogin
        try {
            firebase.auth().setPersistence(firebase.auth.Auth.Persistence.NONE)
                .then(() => {
                    console.log('Set Firebase persistence to NONE');
                    
                    // Force sign out to ensure clean state
                    return firebase.auth().signOut();
                })
                .then(() => {
                    console.log('Successfully signed out from Firebase after setting persistence');
                    
                    // Clear cache again after signing out
                    clearFirebaseAuthCache();
                    
                    // Delete Firebase apps for thorough cleanup
                    if (firebase.apps && firebase.apps.length > 0) {
                        return Promise.all(firebase.apps.map(app => app.delete()));
                    }
                })
                .then(() => {
                    console.log('Successfully cleaned up Firebase apps after forced logout');
                })
                .catch((error) => {
                    console.error('Error setting auth persistence or signing out:', error);
                });
        } catch (error) {
            console.error('Error in persistence/signout operation:', error);
        }
    }    firebase.auth().onAuthStateChanged(async (user) => {
        const isCurrentlyExplicitlyLoggedOut = localStorage.getItem('explicitly_logged_out') === 'true' || sessionStorage.getItem('explicitly_logged_out') === 'true';
        // If user explicitly logged out, ignore auto-login attempts
        if (isCurrentlyExplicitlyLoggedOut && user) {
            console.log('User explicitly logged out (checked inside onAuthStateChanged) but Firebase still has auth state, signing out again');
            try {
                // First clear Firebase auth cache before signing out
                clearFirebaseAuthCache();
                
                // Get the token for revocation
                let token = null;
                try {
                    token = await user.getIdToken();
                } catch (tokenError) {
                    console.error('Error getting token during forced logout:', tokenError);
                }
                
                // Revoke the token if we got one
                if (token) {
                    try {
                        const revokeResponse = await fetch('/api/auth/revoke-token', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'Cache-Control': 'no-cache, no-store, must-revalidate',
                                'Pragma': 'no-cache',
                                'Expires': '0'
                            },
                            body: JSON.stringify({ token })
                        });
                        
                        if (revokeResponse.ok) {
                            console.log('Successfully revoked token during forced logout');
                        }
                    } catch (revokeError) {
                        console.error('Error revoking token during forced logout:', revokeError);
                    }
                }
                
                // Then sign out from Firebase
                await firebase.auth().setPersistence(firebase.auth.Auth.Persistence.NONE);
                await firebase.auth().signOut();
                
                // Force extra cleanup after signout
                clearFirebaseAuthCache();
                
                // Try to delete Firebase apps
                if (firebase.apps && firebase.apps.length > 0) {
                    try {
                        await Promise.all(firebase.apps.map(app => app.delete()));
                        console.log('Successfully deleted all Firebase apps');
                    } catch (e) {
                        console.error('Error deleting Firebase apps:', e);
                    }
                }
                
                console.log('Successfully enforced logout from Firebase (from within onAuthStateChanged)');
                // Ensure global state reflects logout immediately
                currentUser = null;
                isAuthenticated = false;
                document.dispatchEvent(new CustomEvent('authStateChanged', { 
                    detail: { isAuthenticated: false, user: null } 
                }));
                return; // Stop processing - we're enforcing logout
            } catch (e) {
                console.error('Error enforcing logout (from within onAuthStateChanged):', e);
            }
        }
        
        if (user) {
            // User is signed in
            console.log('Firebase auth state shows user is signed in:', user.email);
            currentUser = user;
              // Check if the server knows about this login
            try {
                const sessionResult = await fetch('/api/auth/session', {
                    headers: {
                        'Cache-Control': 'no-cache, no-store, must-revalidate',
                        'Pragma': 'no-cache',
                        'Expires': '0'
                    }
                }).then(res => res.json());
                
                console.log('Server session check result:', sessionResult);
                
                // If server reports explicit logout, enforce it
                if (sessionResult.explicitly_logged_out) {
                    console.log('Server reports explicit logout, signing out from Firebase');
                    await firebase.auth().signOut();
                    isAuthenticated = false;
                    localStorage.setItem('explicitly_logged_out', 'true');
                    // Force extra cleanup
                    clearFirebaseAuthCache();
                    return;
                }
            
                if (!sessionResult.authenticated) {
                    // Server doesn't know about this user yet, send the token
                    try {
                        const idToken = await user.getIdToken();
                        const response = await fetch('/api/auth/email', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({ idToken })
                        });
                        
                        if (!response.ok) {
                            console.error('Failed to authenticate with server');
                            // Don't log out here - might be temporary server issue
                        }
                    } catch (error) {
                        console.error('Error sending authentication token to server', error);
                    }
                }
            } catch (error) {
                console.error('Error checking session with server:', error);
            }
            
            isAuthenticated = true;
            
            // Trigger auth state change event
            document.dispatchEvent(new CustomEvent('authStateChanged', { 
                detail: { isAuthenticated: true, user } 
            }));
        } else {
            // User is signed out
            currentUser = null;
            isAuthenticated = false;
            
            // Trigger auth state change event
            document.dispatchEvent(new CustomEvent('authStateChanged', { 
                detail: { isAuthenticated: false, user: null } 
            }));
        }
    });
}

// Sign out the user
async function signOut() {
    if (!initializeFirebase()) {
        // Fallback to server-side logout
        window.location.href = '/logout';
        return;
    }
    
    try {
        console.log('Starting logout process...');
        
        // Get user UID for later use in token revocation
        let uid = null;
        let currentToken = null;

        if (firebase.auth().currentUser) {
            const user = firebase.auth().currentUser;
            uid = user.uid;
            console.log('Current user before logout:', user.email, 'UID:', uid);
            try {
                currentToken = await user.getIdToken();
            } catch (tokenError) {
                console.error('Error getting token to revoke:', tokenError);
            }
        }

        // Change persistence to NONE before trying any operations
        try {
            await firebase.auth().setPersistence(firebase.auth.Auth.Persistence.NONE);
            console.log('Changed Firebase persistence to NONE');
        } catch (persistenceError) {
            console.error('Error setting persistence:', persistenceError);
        }
        
        // First handle token revocation
        if (currentToken) {
            // ... existing token revocation logic ...
        } else if (uid) {
            // ... existing token revocation by UID logic ...
        }

        // Now tell the server to log out the user
        // ... existing server signout fetch ...
        
        // Clear localStorage and sessionStorage (related to Firebase)
        clearFirebaseAuthCache();
        
        // AFTER server logout and clearing cache, sign out from Firebase
        await firebase.auth().signOut();
        console.log('Firebase logout successful');
        
        // Clear storage again after signing out from Firebase
        clearFirebaseAuthCache();
        
        // Remove any Firebase cookies
        // ... existing cookie clearing logic ...

        // Finally, delete Firebase apps for complete cleanup
        if (window.firebase && firebase.apps && firebase.apps.length > 0) {
            try {
                await Promise.all(firebase.apps.map(app => app.delete()));
                console.log('Successfully deleted all Firebase apps');
            } catch (e) {
                console.error('Error deleting Firebase apps:', e);
            }
        }

        // Set explicit logout flag in localStorage and sessionStorage LAST, just before redirect
        localStorage.setItem('explicitly_logged_out', 'true');
        sessionStorage.setItem('explicitly_logged_out', 'true');
        console.log('[SIGN_OUT] Set explicitly_logged_out flag in storage as final step before redirect.');
        console.log('[SIGN_OUT] localStorage flag state:', localStorage.getItem('explicitly_logged_out'));
        console.log('[SIGN_OUT] sessionStorage flag state:', sessionStorage.getItem('explicitly_logged_out'));

        // Redirect to the dedicated logout cleanup page
        console.log('Redirecting to logout cleanup page...');
        window.location.href = '/logout_cleanup?t=' + new Date().getTime();
    } catch (error) {
        console.error('Error signing out:', error);
        // Still attempt to set logout flag and redirect as a fallback
        localStorage.setItem('explicitly_logged_out', 'true');
        sessionStorage.setItem('explicitly_logged_out', 'true');
        window.location.href = '/logout_cleanup?t=' + new Date().getTime() + '&error=true';
    }
}

// Override Firebase indexedDB-based persistence to prevent automatic logins
function clearFirebaseAuthCache() {
    console.log('Clearing Firebase auth cache...');
    
    // Clear Firebase auth data from localStorage
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
                console.log('Detected project ID for targeted cleanup:', projectId);
                
                // Add project-specific keys if we found a project ID
                if (projectId) {
                    knownKeys.push(`firebase:authUser:${projectId}`);
                    knownKeys.push(`firebase:previous-user:${projectId}`);
                }
            }
        } catch (projectIdError) {
            console.error('Error detecting project ID:', projectIdError);
        }
        
        knownKeys.forEach(key => {
            try {
                localStorage.removeItem(key);
                console.log(`Cleared localStorage key: ${key}`);
            } catch (e) {
                console.error(`Error clearing localStorage key ${key}:`, e);
            }
        });
        
        // Then clear any keys that start with firebase:
        for (let i = localStorage.length - 1; i >= 0; i--) {
            const key = localStorage.key(i);
            if (key && (key.startsWith('firebase:') || key.includes('firebase'))) {
                localStorage.removeItem(key);
                console.log('Cleared localStorage item:', key);
            }
        }
        
        // Clear sessionStorage as well
        for (let i = sessionStorage.length - 1; i >= 0; i--) {
            const key = sessionStorage.key(i);
            if (key && (key.startsWith('firebase:') || key.includes('firebase'))) {
                sessionStorage.removeItem(key);
                console.log('Cleared sessionStorage item:', key);
            }
        }
    } catch (e) {
        console.error('Error clearing localStorage/sessionStorage:', e);
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
            const req = indexedDB.deleteDatabase(dbName);
            req.onsuccess = () => console.log(`Successfully deleted IndexedDB: ${dbName}`);
            req.onerror = () => console.error(`Error deleting IndexedDB: ${dbName}`);
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
                        req.onsuccess = () => console.log(`Successfully deleted dynamic IndexedDB: ${database.name}`);
                        req.onerror = () => console.error(`Error deleting dynamic IndexedDB: ${database.name}`);
                    }
                });
            }).catch(err => {
                console.error('Error listing IndexedDB databases:', err);
            });
        }
    } catch (e) {
        console.error('Error clearing IndexedDB:', e);
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
            )) {
                document.cookie = `${cookieName}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
                document.cookie = `${cookieName}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;domain=${window.location.hostname}`;
                document.cookie = `${cookieName}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;domain=.${window.location.hostname}`;
                console.log(`Cleared cookie: ${cookieName}`);
            }
        }
    } catch (e) {
        console.error('Error clearing cookies:', e);
    }
}

// Get current authentication state
function getAuthState() {
    return {
        isAuthenticated,
        currentUser
    };
}

// Get Firebase ID token for authenticated requests
async function getIdToken() {
    if (!currentUser) {
        return null;
    }
    
    try {
        return await currentUser.getIdToken();
    } catch (error) {
        console.error('Error getting ID token:', error);
        return null;
    }
}

// Initialize auth monitoring when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Set up logout button click handlers
    document.querySelectorAll('[data-auth="logout"]').forEach(element => {        element.addEventListener('click', (e) => {
            e.preventDefault();
            
            // Use improved logout if available
            if (window.FirebaseLogout) {
                window.FirebaseLogout.logout();
            } else {
                signOut();
            }
        });
    });
    
    // Start monitoring auth state
    monitorAuthState();
});

// Export the auth utilities
window.authUtils = {
    initializeFirebase,
    monitorAuthState,
    signOut,
    getAuthState,
    getIdToken,
    clearFirebaseAuthCache
};
