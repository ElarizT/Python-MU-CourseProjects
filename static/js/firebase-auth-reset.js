/**
 * Firebase Auth Reset Utilities
 * 
 * This script provides enhanced functionality to ensure complete
 * Firebase authentication logout, fixing persistent auth states.
 */

// Self-executing function to minimize global scope pollution
(function() {
    'use strict';

    // Check immediately on script load if we need to force logout
    document.addEventListener('DOMContentLoaded', function() {
        // Initialize diagnostics
        initializeAuthStateMonitor();
    });

    /**
     * Initialize continuous monitoring of authentication state
     * to detect and fix any lingering auth sessions
     */
    function initializeAuthStateMonitor() {
        console.log("Starting continuous Firebase auth monitoring");
        
        // Check for explicitly_logged_out flag
        const isExplicitlyLoggedOut = localStorage.getItem('explicitly_logged_out') === 'true';
        
        // Skip further checks on auth pages to avoid interfering with login flow
        const isAuthPage = window.location.pathname.includes('/login') || 
                          window.location.pathname.includes('/signup');
        
        if (isExplicitlyLoggedOut && !isAuthPage) {
            console.log("User explicitly logged out - enforcing logout state");
            
            // Set up continuous auth state monitoring to catch any reappearing auth states
            startContinuousAuthCheck();
        } else {
            // Just do a single check for diagnostics
            performAuthCheck();
        }
    }

    /**
     * Start continuous authentication state checking
     * This will monitor for 30 seconds after page load to catch any auth state that reappears
     */
    function startContinuousAuthCheck() {
        // Initial check immediately
        performAuthCheck();
        
        // Then check every second for 30 seconds
        let checkCount = 0;
        const maxChecks = 30;
        
        const intervalId = setInterval(() => {
            checkCount++;
            performAuthCheck();
            
            if (checkCount >= maxChecks) {
                clearInterval(intervalId);
                console.log("Completed continuous auth state monitoring");
            }
        }, 1000);
    }

    /**
     * Perform a single auth check and fix any detected issues
     */
    function performAuthCheck() {
        // Only proceed if Firebase is available
        if (typeof firebase === 'undefined' || !firebase.auth) {
            return;
        }
        
        firebase.auth().onAuthStateChanged((user) => {
            if (user) {
                const isExplicitlyLoggedOut = localStorage.getItem('explicitly_logged_out') === 'true';
                
                if (isExplicitlyLoggedOut) {
                    console.warn("⚠️ Auth state mismatch detected! User is signed in but should be logged out:", user.email);
                    console.log("Forcing aggressive logout...");
                    
                    // Force immediate signout with extra aggressive measures
                    forceAggressiveSignout(user.email);
                } else {
                    console.log("Firebase auth state: User is signed in:", user.email);
                }
            } else {
                console.log("Firebase auth state: No user detected");
            }
        });
    }

    /**
     * Performs an extremely aggressive signout when a user is detected
     * that should not be there
     */
    async function forceAggressiveSignout(email) {
        console.log(`Performing aggressive signout for ${email}`);
        
        // 1. Set persistence to NONE first
        try {
            await firebase.auth().setPersistence(firebase.auth.Auth.Persistence.NONE);
            console.log("Set Firebase persistence to NONE");
        } catch (e) {
            console.error("Failed to set persistence:", e);
        }
        
        // 2. Clear all storage before signout
        clearAllFirebaseStorage();
        
        // 3. Perform the signout
        try {
            await firebase.auth().signOut();
            console.log("Successfully signed out user from Firebase");
        } catch (e) {
            console.error("Error signing out from Firebase:", e);
        }
        
        // 4. Clear storage again after signout
        clearAllFirebaseStorage();
        
        // 5. Delete all Firebase apps if possible
        try {
            if (firebase.apps && firebase.apps.length > 0) {
                await Promise.all(firebase.apps.map(app => app.delete()));
                console.log("Successfully deleted all Firebase apps");
            }
        } catch (e) {
            console.error("Error deleting Firebase apps:", e);
        }
        
        // 6. Reload the page if we're not already on an auth page
        const isAuthPage = window.location.pathname.includes('/login') || 
                          window.location.pathname.includes('/signup') ||
                          window.location.pathname.includes('/logout');
        
        if (!isAuthPage) {
            console.log("Reloading page to ensure clean state...");
            window.location.href = "/logout_cleanup?t=" + new Date().getTime();
        }
    }

    /**
     * Aggressively clear all Firebase-related storage
     */
    function clearAllFirebaseStorage() {
        // Clear localStorage
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
        
        // Clear sessionStorage
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
                    req.onsuccess = () => console.log(`Deleted IndexedDB: ${dbName}`);
                    req.onerror = () => console.error(`Error deleting IndexedDB: ${dbName}`);
                } catch (e) {
                    console.error(`Error with IndexedDB ${dbName}:`, e);
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
                            req.onsuccess = () => console.log(`Deleted dynamic IndexedDB: ${database.name}`);
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
            console.error('Error clearing cookies:', e);
        }
    }
})();
